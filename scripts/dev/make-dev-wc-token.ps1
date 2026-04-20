$ErrorActionPreference = "Stop"

$secret = if ($env:AUTH_SHARED_SECRET) { $env:AUTH_SHARED_SECRET } else { "dev-only-hcr2-secret" }
$subject = if ($env:DEV_DISCORD_ID) { $env:DEV_DISCORD_ID } else { "dev-admin" }
$username = if ($env:DEV_DISCORD_USERNAME) { $env:DEV_DISCORD_USERNAME } else { "Dev Admin" }

$python = @"
import base64
import hashlib
import hmac
import json
import os
import time

def b64url(data):
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

secret = os.environ["TOKEN_SECRET"]
payload = {
    "sub": os.environ["TOKEN_SUBJECT"],
    "username": os.environ["TOKEN_USERNAME"],
    "exp": int(time.time()) + 86400,
}
header = {"alg": "HS256", "typ": "JWT"}
head = b64url(json.dumps(header, separators=(",", ":")).encode())
body = b64url(json.dumps(payload, separators=(",", ":")).encode())
sig = b64url(hmac.new(secret.encode(), f"{head}.{body}".encode(), hashlib.sha256).digest())
print(f"{head}.{body}.{sig}")
"@

$env:TOKEN_SECRET = $secret
$env:TOKEN_SUBJECT = $subject
$env:TOKEN_USERNAME = $username
$token = $python | python -

Write-Output $token
Write-Output ""
Write-Output "Browser cookie for local admin testing:"
Write-Output "WC_TOKEN=$token"
