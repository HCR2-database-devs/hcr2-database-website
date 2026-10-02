# Production Deployment

This guide covers deploying the application on a Linux server (Ubuntu/Debian) with Nginx and systemd.

## Architecture

```
Internet → Cloudflare → Nginx
                            ├── /      → static React files  (frontend/dist/)
                            └── /api/  → reverse proxy       → Uvicorn (FastAPI) :8000
```

The frontend is compiled to static files served directly by Nginx. The FastAPI backend runs as a systemd service.

## Prerequisites

```bash
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm nginx git
```

PostgreSQL must already be running and accessible (local or remote).

## 1. Clone the Repository

```bash
sudo mkdir -p /var/www/hcr2.xyz
sudo chown $USER:$USER /var/www/hcr2.xyz
git clone https://github.com/HCR2-database-devs/hcr2-database-website.git /var/www/hcr2.xyz
cd /var/www/hcr2.xyz
```

## 2. Configure Environment Variables

```bash
cp backend/.env.example backend/.env
nano backend/.env
```

Fill in production values:

```env
APP_NAME=HCR2 Records API
ENVIRONMENT=production

DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=hcr2_prod
DB_USER=hcr2_user
DB_PASS=strong_password_here
DB_SCHEMA=hcr2

AUTH_SHARED_SECRET=long_random_secret_here
# Separate key for hashing submission rate-limit buckets. Keep it distinct from
# AUTH_SHARED_SECRET: rotating that one to revoke sessions would also reset every
# rate-limit counter. Generate with: openssl rand -hex 32
SUBMISSION_RATE_LIMIT_HMAC_SECRET=another_long_random_secret_here
ALLOWED_DISCORD_IDS=123456789,987654321

# Community profile cooldowns, in days. The frontend reads these from
# GET /api/v1/community/config, so keep them in sync with the site copy.
USERNAME_CHANGE_COOLDOWN_DAYS=7
BANNER_CHANGE_COOLDOWN_DAYS=7

HCAPTCHA_SITE_KEY=your_hcaptcha_site_key
HCAPTCHA_SECRET_KEY=your_hcaptcha_secret_key

CORS_ORIGINS=https://yourdomain.com
```

Never commit `.env` to the repository.

## 3. Install the Backend

```bash
cd /var/www/hcr2.xyz/backend
python3.11 -m venv .venv
.venv/bin/pip install -e "."
cd ..
```

## 4. Create the systemd Service

Create `/etc/systemd/system/hcr2-backend.service`:

```ini
[Unit]
Description=HCR2 FastAPI Backend
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/hcr2.xyz/backend
EnvironmentFile=/var/www/hcr2.xyz/backend/.env
ExecStart=/var/www/hcr2.xyz/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2 --proxy-headers --forwarded-allow-ips=127.0.0.1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable hcr2-backend
sudo systemctl start hcr2-backend
sudo systemctl status hcr2-backend
```

Check the logs:

```bash
sudo journalctl -u hcr2-backend -f
```

Verify the API is responding:

```bash
curl http://127.0.0.1:8000/health
```

## 5. Build the Frontend

```bash
cd /var/www/hcr2.xyz/frontend
npm install
npm run build
cd ..
```

Static files are output to `frontend/dist/`.

## 6. Configure Nginx

Create `/etc/nginx/sites-available/hcr2`:

The `set_real_ip_from` list below is Cloudflare's complete published edge range set, verified against the official sources on 2026-10-02:

- IPv4: <https://www.cloudflare.com/ips-v4>
- IPv6: <https://www.cloudflare.com/ips-v6>

Re-check both URLs before each deployment and update this block if they differ. Adding a range you do not control would let anyone spoof `CF-Connecting-IP`.

```nginx
server {
    set_real_ip_from 173.245.48.0/20;
    set_real_ip_from 103.21.244.0/22;
    set_real_ip_from 103.22.200.0/22;
    set_real_ip_from 103.31.4.0/22;
    set_real_ip_from 141.101.64.0/18;
    set_real_ip_from 108.162.192.0/18;
    set_real_ip_from 190.93.240.0/20;
    set_real_ip_from 188.114.96.0/20;
    set_real_ip_from 197.234.240.0/22;
    set_real_ip_from 198.41.128.0/17;
    set_real_ip_from 162.158.0.0/15;
    set_real_ip_from 104.16.0.0/13;
    set_real_ip_from 104.24.0.0/14;
    set_real_ip_from 172.64.0.0/13;
    set_real_ip_from 131.0.72.0/22;
    set_real_ip_from 2400:cb00::/32;
    set_real_ip_from 2606:4700::/32;
    set_real_ip_from 2803:f800::/32;
    set_real_ip_from 2405:b500::/32;
    set_real_ip_from 2405:8100::/32;
    set_real_ip_from 2a06:98c0::/29;
    set_real_ip_from 2c0f:f248::/32;
    real_ip_header CF-Connecting-IP;
    real_ip_recursive on;

    listen 80;
    server_name yourdomain.com;

    # React SPA — static files
    root /var/www/hcr2.xyz/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # FastAPI backend
    location ~ ^/(api|php|auth|health)(/|$) {
        client_max_body_size 12m;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

The Cloudflare ranges above are the published IPv4 and IPv6 edge ranges. Keep this list synchronized with the official Cloudflare IP list before each deployment. The origin must only be reachable through Cloudflare: restrict the host firewall or provider firewall so direct requests cannot bypass the trusted proxy layer. Uvicorn trusts only the local Nginx peer via `--forwarded-allow-ips=127.0.0.1`; do not widen that value to `*` or to client networks. Nginx overwrites `X-Forwarded-For` with the trusted client address rather than appending an untrusted incoming value.

The backend uses `request.client.host` after Uvicorn applies the trusted proxy headers. It does not trust `CF-Connecting-IP` or forwarded headers directly in application code.

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/hcr2 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 7. Apply Database Migrations

```bash
cd /var/www/hcr2.xyz
for f in migrations/*.up.sql; do
    psql -h 127.0.0.1 -U hcr2_user -d hcr2_prod -f "$f"
done
```

## 8. HTTPS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

Certbot updates the Nginx config automatically and sets up auto-renewal.

---

## Reloading After a Code Change

After a `git pull`, only reload what actually changed.

### Backend changed

```bash
sudo systemctl restart hcr2-backend
```

If port 8000 is already occupied (e.g. a stale process from a previous failed restart):

```bash
sudo fuser -k 8000/tcp
sudo systemctl start hcr2-backend
```

### Frontend changed

```bash
cd /var/www/hcr2.xyz/frontend
npm install       # only if package.json changed
npm run build
```

Nginx serves the files directly — no reload needed.

### Both changed

```bash
cd /var/www/hcr2.xyz/frontend && npm run build && cd ..
sudo systemctl restart hcr2-backend
```

### New migration

```bash
psql -h 127.0.0.1 -U hcr2_user -d hcr2_prod -f migrations/new_migration.up.sql
```

### Nginx config changed

```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## Convenience Deploy Script

Create `/var/www/hcr2.xyz/deploy.sh` for full redeployments:

```bash
#!/bin/bash
set -e
cd /var/www/hcr2.xyz

git pull

cd frontend
npm install --silent
npm run build
cd ..

sudo systemctl restart hcr2-backend
echo "Deploy complete."
```

```bash
chmod +x /var/www/hcr2.xyz/deploy.sh
```

Run it with:

```bash
/var/www/hcr2.xyz/deploy.sh
```

---

## Quick Reference

| Task                        | Command                                          |
|-----------------------------|--------------------------------------------------|
| Backend logs (live)         | `sudo journalctl -u hcr2-backend -f`             |
| Backend status              | `sudo systemctl status hcr2-backend`             |
| Restart backend             | `sudo systemctl restart hcr2-backend`            |
| Kill stale port 8000        | `sudo fuser -k 8000/tcp`                         |
| Rebuild frontend            | `cd frontend && npm run build`                   |
| Reload Nginx config         | `sudo nginx -t && sudo systemctl reload nginx`   |
| Check API health            | `curl http://127.0.0.1:8000/health`              |
