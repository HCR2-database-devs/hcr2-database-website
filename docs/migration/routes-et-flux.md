# Routes et flux existants

Date: 2026-04-20

Ce document cartographie les routes actuelles et les flux utilisateur/admin avant migration.

## Pages HTML

| Route actuelle | Fichier | Role | Protection |
| --- | --- | --- | --- |
| `/` ou `/index.php` | `index.php` | Entree principale, applique maintenance puis sert `index.html` | Maintenance |
| `/index.html` | `index.html` | Page publique statique | Check maintenance JS synchrone |
| `/maintenance.html` | `maintenance.html` | Page maintenance statique | Public |
| `/privacy.html` | `privacy.html` | Politique de confidentialite | Public |
| `/php/admin.php` | `php/admin.php` | Admin panel complet | JWT `WC_TOKEN` + allowlist |

## Endpoints publics

| Methode | Route | Fichier | Entree | Sortie | Notes |
| --- | --- | --- | --- | --- | --- |
| GET | `/php/maintenance_status.php` | `php/maintenance_status.php` | none | `{ maintenance, allowed }` | Utilise session admin si presente |
| GET | `/php/load_data.php?type=maps` | `php/load_data.php` | `type=maps` | liste maps | Maintenance JSON |
| GET | `/php/load_data.php?type=vehicles` | `php/load_data.php` | `type=vehicles` | liste vehicles | Maintenance JSON |
| GET | `/php/load_data.php?type=players` | `php/load_data.php` | `type=players` | liste players | Maintenance JSON |
| GET | `/php/load_data.php?type=tuning_parts` | `php/load_data.php` | `type=tuning_parts` | liste tuning parts | ordre `nameTuningPart` |
| GET | `/php/load_data.php?type=tuning_setups` | `php/load_data.php` | `type=tuning_setups` | liste setups + parts | `string_agg`, group by setup |
| GET | `/php/load_data.php?type=records` | `php/load_data.php` | `type=records` | records courants enrichis | `wr.current = 1` |
| GET | `/php/get_news.php?limit=10` | `php/get_news.php` | `limit` optionnel | `{ news: [...] }` | limite forcee 1..100 sinon 10 |
| GET | `/php/get_hcaptcha_sitekey.php` | `php/get_hcaptcha_sitekey.php` | none | `{ sitekey }` | Erreur si hCaptcha non configure |
| POST | `/php/public_submit.php` | `php/public_submit.php` | JSON/form | `{ success, message }` ou `{ error }` | hCaptcha, honeypot, rate limit |
| GET | `/php/api_records.php` | `php/api_records.php` | API key + filtres | `{ records, count }` | API key obligatoire |

## Endpoints auth

| Methode | Route | Fichier | Role |
| --- | --- | --- | --- |
| GET | `/auth/status.php` | `auth/status.php` | Retourne statut login/admin depuis `WC_TOKEN` |
| GET | `/auth/logout.php` | `auth/logout.php` | Supprime session/cookie puis redirige `/` |

Login:

- Le bouton public redirige vers `https://auth.hcr2.xyz/login`.
- Ce service externe doit poser le cookie `WC_TOKEN`.
- L'application locale verifie ensuite `WC_TOKEN`.

## Endpoints admin

| Methode | Route | Fichier | Role |
| --- | --- | --- | --- |
| POST | `/php/submit_record.php` | `php/submit_record.php` | Ajout/remplacement record |
| POST | `/php/delete_record.php` | `php/delete_record.php` | Suppression record |
| POST | `/php/set_questionable.php` | `php/set_questionable.php` | Met a jour `questionable` et note |
| POST | `/php/assign_setup.php` | `php/assign_setup.php` | Assigne tuning setup a un record sans setup |
| POST | `/php/add_vehicle.php` | `php/add_vehicle.php` | Cree vehicle et SVG optionnel |
| POST | `/php/add_map.php` | `php/add_map.php` | Cree map et SVG optionnel |
| POST | `/php/add_tuning_part.php` | `php/add_tuning_part.php` | Cree tuning part et SVG optionnel |
| POST | `/php/add_tuning_setup.php` | `php/add_tuning_setup.php` | Cree setup 3 ou 4 parts |
| GET | `/auth/admin_pending.php` | `auth/admin_pending.php` | Liste pending submissions |
| POST | `/auth/admin_pending.php` | `auth/admin_pending.php` | Approve/reject submission |
| POST | `/auth/post_news.php` | `auth/post_news.php` | Publie une news |
| GET | `/auth/admin_actions.php?action=download_db` | `auth/admin_actions.php` | Retourne 501 en PostgreSQL |
| POST | `/auth/admin_actions.php` | `auth/admin_actions.php` | list/delete backups, integrity; create/restore/import non supportes |
| POST | `/php/set_maintenance.php` | `php/set_maintenance.php` | Active/desactive/toggle maintenance |

## Flux public: consultation

1. L'utilisateur arrive sur `/`.
2. `index.php` bloque en maintenance si necessaire.
3. `index.html` fait un check synchrone `/php/maintenance_status.php`.
4. Les boutons appellent `fetchData(type)` ou `fetchStats()`.
5. `fetchData(type)` appelle `/php/load_data.php?type=...`.
6. Les donnees sont rendues en table HTML par `displayData`.
7. Les records ajoutent filtres, tri, export CSV et liens de partage.

Types consultables:

- `maps`
- `vehicles`
- `players`
- `tuning_parts`
- `records`
- `stats` via records

## Flux public: records

1. Bouton `Get Records`.
2. Appel `/php/load_data.php?type=records`.
3. Tri par defaut:
   - map name alphabetique,
   - vehicle id si disponible,
   - sinon vehicle name alphabetique.
4. Colonnes:
   - Distance
   - Status
   - Notes
   - Map Name
   - Vehicle Name
   - Tuning Parts
   - Player Name
   - Player Country
   - Share
5. Filtres:
   - recherche player/map/vehicle/notes,
   - map,
   - vehicle,
   - tuning parts avec logique `every`,
   - distance `>=` ou `<=`,
   - only questionable,
   - only verified.
6. Export CSV:
   - Distance,
   - Map Name,
   - Vehicle Name,
   - Player Name,
   - Country.

## Flux public: soumission record

1. Bouton `Submit Record`.
2. Ouverture modale.
3. Chargement maps, vehicles, tuning parts via `load_data`.
4. Chargement sitekey via `/php/get_hcaptcha_sitekey.php`.
5. hCaptcha rendu dans `#hcaptcha-widget`.
6. Validation front:
   - map, vehicle, distance, player requis,
   - distance > 0,
   - 3 ou 4 tuning parts,
   - hCaptcha present.
7. POST `/php/public_submit.php`.
8. Validation backend:
   - hCaptcha valide,
   - champs requis,
   - honeypots vides,
   - temps de remplissage minimum,
   - distance positive,
   - 3 ou 4 tuning parts,
   - max 5 soumissions par IP sur 1h.
9. Insertion `PendingSubmission`.
10. Message: `Submission received and is pending review by admins.`

## Flux public: news

1. Bouton `News`.
2. Ouverture modale.
3. Appel `/php/get_news.php`.
4. Affichage title/content/author/created_at.
5. `localStorage.unreadNews` passe a `false`.

## Flux public: auth/admin visibility

1. `checkAuthAndInit()` appelle `/auth/status.php`.
2. Si `logged=false`: bouton login visible, logout/admin caches.
3. Si `logged=true`: login cache, logout visible.
4. Si `allowed=true`: bouton admin visible et redirige vers `php/admin.php`.
5. Refresh toutes les 30s.

## Flux admin: acces

1. L'utilisateur va sur `/php/admin.php`.
2. `ensure_authorized()` verifie `WC_TOKEN`.
3. Le payload JWT est place en `$_SESSION['discord']`.
4. Le `sub` doit etre present dans `ALLOWED_DISCORD_IDS`.
5. Sinon:
   - token absent/invalide: redirection `/`,
   - non admin: 403 HTML.

## Flux admin: ajout/remplacement record

1. Formulaire `record-form`.
2. Charge maps, vehicles, players, tuning setups, tuning parts.
3. Validations front:
   - map, vehicle, distance HTML required,
   - player existant ou new player,
   - country requis si new player.
4. POST `/php/submit_record.php`.
5. Backend:
   - admin requis,
   - map/vehicle/distance requis,
   - distance positive,
   - player existant verifie si `playerId`,
   - transaction,
   - suppression des records existants pour map+vehicle,
   - insertion `_worldrecord` courant,
   - commit,
   - retour des noms map/vehicle/player.

Attention: `newPlayerName` est accepte dans le payload, mais le backend actuel n'insere pas le nouveau player dans `submit_record.php`; ce comportement doit etre preserve tant qu'il n'est pas explicitement corrige.

## Flux admin: suppression record

1. Charge records.
2. Selection record.
3. POST `/php/delete_record.php`.
4. Suppression `_worldrecord` par `idRecord`.

Risque existant: chemin `require_once` incoherent dans `php/delete_record.php`.

## Flux admin: questionable

1. Selection record.
2. Choix status `0` ou `1`.
3. Note optionnelle.
4. POST `/php/set_questionable.php`.
5. Verifie record existant.
6. UPDATE `_worldrecord SET questionable=?, questionable_reason=?`.

## Flux admin: assign tuning setup

1. Liste les records sans `idTuningSetup`.
2. Liste tuning setups.
3. POST `/php/assign_setup.php`.
4. Backend:
   - session admin requise,
   - record existe,
   - record n'a pas deja de setup,
   - setup existe,
   - update record.

## Flux admin: ajout referentiels

Vehicule, map, tuning part:

1. POST FormData avec nom et icone SVG optionnelle.
2. Check doublon par nom.
3. Creation.
4. Si icone:
   - MIME ou extension SVG,
   - taille <= 1MB,
   - contenu contient `<svg`,
   - sauvegarde dans dossier d'icones avec nom normalise.

Tuning setup:

1. POST JSON `{ partIds }`.
2. Backend exige 3 ou 4 parts.
3. Trie les ids.
4. Verifie qu'un setup identique n'existe pas.
5. Insert setup puis lignes `_tuningsetupparts`.

## Flux admin: pending submissions

GET:

- Liste `PendingSubmission` avec map/vehicle labels.
- Filtre `status = 'pending'`.
- Tri `submitted_at DESC`.

Approve:

1. Charge submission.
2. Transaction.
3. Supprime `_worldrecord` pour map+vehicle.
4. Trouve ou cree player par `playerName`.
5. Insert `_worldrecord` courant.
6. Si tuning parts sont valides:
   - resout les ids par nom,
   - cree nouveau setup,
   - associe le setup au record.
7. Marque submission `approved`.

Reject:

- Marque submission `rejected`.

## Flux admin: news

1. POST `/auth/post_news.php`.
2. Requiert title/content.
3. `strip_tags`.
4. Author depuis `$_SESSION['discord']['username']`.
5. Insert `News`.

## Flux admin: backups et integrity

Actions existantes:

- `list_backups`: liste les fichiers dans `backups/`.
- `delete`: supprime un fichier de backup dans le dossier.
- `integrity`: execute `SELECT 1`.

Actions non supportees depuis passage PostgreSQL:

- `download_db`: HTTP 501.
- `create_backup`: erreur.
- `restore`: erreur.
- `import`: erreur.

## Flux maintenance

1. Admin appelle `/php/set_maintenance.php` avec action `enable`, `disable`, `on`, `off`, `1`, `0`, ou absent.
2. Creation/suppression du fichier racine `MAINTENANCE`.
3. Les endpoints avec `enforce_maintenance_json()` retournent 503 si maintenance et non-admin.
4. `index.php` retourne une page HTML 503 si maintenance et non-admin.

## Deep links

Parametres supportes:

- `view`: `maps`, `vehicles`, `players`, `tuning_parts`, `records`, `tuning_setups`.
- `recordId`: scroll/highlight de la ligne record.
- `map`: scroll vers une map dans les records.
- `mapId`: genere dans `copyShareLink('map')`, mais pas consomme explicitement dans `handleDeepLinkParams()`.

## Contrats a proteger pendant migration

- Noms de routes historiques tant que le front legacy existe.
- Shapes JSON exacts.
- Codes d'erreur et messages utiles au front.
- Conventions `idMap`, `nameMap`, `idVehicle`, `nameVehicle`, `idPlayer`, `namePlayer`.
- Champs records enrichis: `idRecord`, `distance`, `current`, `idTuningSetup`, `questionable`, `questionable_reason`, `map_name`, `vehicle_name`, `player_name`, `player_country`, `tuning_parts`.
- Regles de filtre et de tri records.
- Mode maintenance.
- JWT `WC_TOKEN` et allowlist Discord.
- hCaptcha, honeypots et rate limit.
