# Mapping backend existant

Date: 2026-04-20

Ce document mappe les fichiers backend PHP actuels vers les responsabilites cibles FastAPI.

## Vue d'ensemble

Backend actuel:

- PHP procedural.
- Configuration et connexion BDD dans `auth/config.php`.
- Auth JWT dans `auth/check_auth.php`.
- Endpoints JSON repartis entre `php/` et `auth/`.
- Logique metier directement dans les endpoints.
- SQL ecrit inline.
- Pas de tests backend automatises.

Backend cible:

```text
backend/
|-- app/
|   |-- main.py
|   |-- api/
|   |   |-- v1/
|   |   |   |-- public.py
|   |   |   |-- records.py
|   |   |   |-- auth.py
|   |   |   |-- admin.py
|   |   |   `-- maintenance.py
|   |-- core/
|   |   |-- config.py
|   |   |-- security.py
|   |   `-- errors.py
|   |-- db/
|   |   |-- session.py
|   |   `-- models.py
|   |-- schemas/
|   |-- repositories/
|   |-- services/
|   `-- utils/
`-- tests/
```

La cible doit conserver les contrats legacy pendant la migration.

## Configuration

Actuel: `auth/config.php`

Responsabilites:

- Charge `.env`.
- Lit `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS`.
- Lit `AUTH_SHARED_SECRET`, `ALLOWED_DISCORD_IDS`, `API_KEYS`.
- Lit `HCAPTCHA_SITE_KEY`, `HCAPTCHA_SECRET_KEY`.
- Configure cookies de session.
- Ajoute headers de securite.
- Cree connexion PDO PostgreSQL.
- Fournit erreurs JSON generiques.

Cible FastAPI:

- `backend/app/core/config.py`
  - Pydantic Settings.
  - Variables documentees et validees.
- `backend/app/core/security.py`
  - JWT `WC_TOKEN`.
  - allowlist Discord.
  - API keys.
- `backend/app/db/session.py`
  - Connexion PostgreSQL.
- `backend/app/core/errors.py`
  - Reponses d'erreur standardisees compatibles legacy.

## Auth

Actuel:

- `auth/check_auth.php`
- `auth/status.php`
- `auth/logout.php`

Contrats:

- `GET /auth/status.php`
  - non connecte: `{ "logged": false, "allowed": false }`
  - connecte: `{ "logged": true, "allowed": bool, "id": "...", "username": "..." }`
- `GET /auth/logout.php`
  - supprime session + cookie `WC_TOKEN`
  - redirige `/`

Regles:

- JWT compose de 3 segments.
- HMAC SHA-256.
- Payload requis: `sub`, `exp`.
- Expiration strictement verifiee.
- `username` propage en session.
- Admin si `sub` dans `ALLOWED_DISCORD_IDS`.

Cible:

- `api/v1/auth.py`
- dependances `get_current_user`, `require_admin`
- compat routes legacy exposees pendant transition:
  - `/auth/status.php`
  - `/auth/logout.php`
  - puis alias propre `/api/v1/auth/status`, `/api/v1/auth/logout`.

## Maintenance

Actuel:

- `php/maintenance_helpers.php`
- `php/maintenance_status.php`
- `php/set_maintenance.php`
- fichier flag `MAINTENANCE`

Contrats:

- `GET /php/maintenance_status.php` -> `{ maintenance, allowed }`
- `POST /php/set_maintenance.php` -> `{ success, maintenance }`
- JSON non-admin en maintenance -> HTTP 503 `{ error: "Site is under maintenance. Please try again later." }`
- HTML non-admin en maintenance -> HTTP 503 avec page maintenance.

Cible:

- `services/maintenance_service.py`
- `api/v1/maintenance.py`
- garder le flag fichier au debut pour compatibilite.
- Prevoir ensuite stockage config propre si besoin, mais pas pendant migration initiale.

## Lecture donnees publiques

Actuel: `php/load_data.php`

Types:

- `maps`: `SELECT * FROM _map`
- `vehicles`: `SELECT * FROM _vehicle`
- `players`: `SELECT * FROM _player`
- `tuning_parts`: `SELECT * FROM _tuningpart ORDER BY nameTuningPart`
- `tuning_setups`: setup + `string_agg(tp.nameTuningPart, ', ')`, transforme ensuite en `parts: [{ nameTuningPart }]`
- `records`: current records enrichis par map, vehicle, player, tuning parts

Cible:

- `api/v1/public.py`
- `repositories/maps.py`, `vehicles.py`, `players.py`, `tuning.py`, `records.py`
- `schemas/public.py`
- Conserver endpoint legacy:
  - `/php/load_data.php?type=...`
- Ajouter endpoints cibles:
  - `/api/v1/maps`
  - `/api/v1/vehicles`
  - `/api/v1/players`
  - `/api/v1/tuning-parts`
  - `/api/v1/tuning-setups`
  - `/api/v1/records`

## Records API avec cle

Actuel: `php/api_records.php`

Auth:

- `api_key` query param ou header `X-API-Key`.
- Cle dans `API_KEYS`.

Filtres:

- `map`
- `vehicle`
- `player`
- `country`
- `questionable` 0/1
- `min_distance`
- `max_distance`
- `q`
- `limit` clamp 1..500, defaut 100
- `offset` defaut 0

Sortie:

```json
{
  "records": [],
  "count": 0
}
```

Cible:

- `api/v1/records.py`
- `require_api_key` dependency.
- Tests de contrat indispensables.

## Soumission publique

Actuel: `php/public_submit.php`

Entree JSON:

- `mapId`
- `vehicleId`
- `distance`
- `playerName`
- `playerCountry`
- `tuningParts`
- `h_captcha_response`
- honeypots: `hp_email`, `hp_website`, `hp_phone`, `hp_comments`
- `form_load_time`
- `submission_time`

Validations:

- hCaptcha obligatoire et valide.
- champs requis: map, vehicle, distance, player.
- honeypots vides.
- temps passe >= 2000 ms sinon 429.
- distance > 0.
- 3 ou 4 tuning parts.
- rate limit: max 5 submissions par IP sur 1 heure.

Effet:

- insert `PendingSubmission`.

Cible:

- `schemas/submissions.py`
- `services/hcaptcha_service.py`
- `services/public_submission_service.py`
- `repositories/pending_submissions.py`
- route legacy `/php/public_submit.php` et route propre `/api/v1/submissions`.

## Admin records

Actuel:

- `php/submit_record.php`
- `php/delete_record.php`
- `php/set_questionable.php`
- `php/assign_setup.php`

### Submit record

Regles:

- Admin requis.
- map/vehicle/distance requis.
- distance positive.
- Si `playerId` fourni, le player doit exister.
- Transaction.
- Supprime les records existants pour map+vehicle.
- Insert `_worldrecord` avec `current=1`, `idTuningSetup`, `questionable`, `questionable_reason`.
- Retourne `success`, `playerId`, `mapName`, `vehicleName`, `playerName`, `distance`.

Point sensible:

- `newPlayerName` est accepte cote front mais non insere par ce endpoint. Ne pas changer sans decision produit.

### Delete record

Regle:

- Supprime `_worldrecord` par `idRecord`.

Risque:

- `require_once __DIR__ . '/auth/check_auth.php'` semble faux.

### Questionable

Regles:

- JSON valide.
- `recordId` requis.
- `questionable` doit etre 0 ou 1.
- record doit exister.
- update `questionable` et `questionable_reason`.

### Assign setup

Regles:

- Session admin.
- record existe.
- record sans setup.
- setup existe.
- update `idTuningSetup`.

Cible:

- `api/v1/admin_records.py`
- `services/record_service.py`
- `repositories/records.py`
- tests transactionnels.

## Admin referentiels

Actuel:

- `php/add_map.php`
- `php/add_vehicle.php`
- `php/add_tuning_part.php`
- `php/add_tuning_setup.php`

Map/vehicle:

- Nom requis.
- Doublon interdit.
- ID cree via `MAX(id)+1`.
- Insert.
- SVG optionnel:
  - extension/MIME SVG,
  - max 1MB,
  - contenu contient `<svg`,
  - sauvegarde dans `img/map_icons/` ou `img/vehicle_icons/`.

Tuning part:

- Nom requis.
- Doublon interdit.
- Insert sans ID explicite.
- SVG optionnel dans `img/tuning_parts_icons/`.

Tuning setup:

- `partIds` array.
- Backend exige 3 ou 4 parts.
- Tri ids.
- Refuse setup identique.
- Insert setup et association parts.

Point sensible:

- Front admin indique "Select Tuning Parts (3-4)" mais valide 2 a 4 dans le JS avant appel. Backend reste source de verite.

Cible:

- `services/catalog_service.py`
- `services/icon_upload_service.py`
- `repositories/catalog.py`

## Admin pending submissions

Actuel: `auth/admin_pending.php`

GET:

- Liste pending avec labels map/vehicle.

POST approve:

- Charge la submission.
- Transaction.
- Supprime record map+vehicle existant.
- Trouve ou cree player.
- Insert record courant.
- Si tuning parts fournies et resolues:
  - cree un nouveau tuning setup,
  - associe parts,
  - update record.
- Marque submission approved.

POST reject:

- Marque submission rejected.

Cible:

- `services/pending_submission_service.py`
- `repositories/pending_submissions.py`
- `repositories/players.py`
- `repositories/tuning.py`
- transaction explicite.

## News

Actuel:

- `php/get_news.php`
- `auth/post_news.php`

Public:

- limit defaut 10.
- clamp si <=0 ou >100 a 10.
- tri `created_at DESC`.

Admin:

- title/content requis.
- `strip_tags`.
- author depuis session.
- insert `News`.

Cible:

- `api/v1/news.py`
- `services/news_service.py`

## Backups/admin actions

Actuel: `auth/admin_actions.php`

Actions:

- `list_backups`
- `delete`
- `integrity`

Non supporte PostgreSQL:

- `download_db`
- `create_backup`
- `restore`
- `import`

Cible:

- Phase initiale: reproduire le comportement actuel, y compris erreurs "not supported".
- Phase ulterieure optionnelle: vrai backup PostgreSQL via outil dedie, mais ce serait une evolution fonctionnelle/ops a valider.

## Table de correspondance fichier -> cible

| PHP actuel | Cible FastAPI |
| --- | --- |
| `auth/config.php` | `core/config.py`, `db/session.py`, `core/errors.py` |
| `auth/check_auth.php` | `core/security.py`, dependencies |
| `auth/status.php` | `api/v1/auth.py` |
| `auth/logout.php` | `api/v1/auth.py` |
| `php/maintenance_helpers.php` | `services/maintenance_service.py` |
| `php/maintenance_status.php` | `api/v1/maintenance.py` |
| `php/set_maintenance.php` | `api/v1/maintenance.py` |
| `php/load_data.php` | `api/v1/public.py`, repositories |
| `php/api_records.php` | `api/v1/records.py` |
| `php/public_submit.php` | `api/v1/submissions.py` |
| `php/get_hcaptcha_sitekey.php` | `api/v1/public.py` or `api/v1/submissions.py` |
| `php/get_news.php` | `api/v1/news.py` |
| `auth/post_news.php` | `api/v1/news.py` |
| `php/submit_record.php` | `api/v1/admin_records.py` |
| `php/delete_record.php` | `api/v1/admin_records.py` |
| `php/set_questionable.php` | `api/v1/admin_records.py` |
| `php/assign_setup.php` | `api/v1/admin_records.py` |
| `php/add_map.php` | `api/v1/admin_catalog.py` |
| `php/add_vehicle.php` | `api/v1/admin_catalog.py` |
| `php/add_tuning_part.php` | `api/v1/admin_catalog.py` |
| `php/add_tuning_setup.php` | `api/v1/admin_catalog.py` |
| `auth/admin_pending.php` | `api/v1/admin_submissions.py` |
| `auth/admin_actions.php` | `api/v1/admin_ops.py` |

## Priorite de portage backend

1. Config + healthcheck + DB connection.
2. Models/schemas/repositories en lecture seule.
3. `load_data` compatible.
4. Auth/status compatible.
5. News public.
6. Public submissions avec hCaptcha mockable en tests.
7. Admin records/catalog/submissions.
8. Maintenance.
9. API records avec cle API.
10. Admin ops/backups en compatibilite.
