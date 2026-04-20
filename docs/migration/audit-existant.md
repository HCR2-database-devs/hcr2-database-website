# Audit de l'existant

Date: 2026-04-20
Branche de travail: `refactor/fastapi-react-migration`
Objectif: documenter l'etat actuel avant migration FastAPI + React, sans modifier le comportement.

## Resume executif

Le projet actuel est une application PHP/HTML/CSS/JavaScript procedurale.

- Front public: `index.html` charge `css/style.css` et `js/script.js`.
- Entree publique principale: `index.php`, qui applique le mode maintenance puis sert `index.html`.
- Backend: endpoints PHP repartis entre `php/` et `auth/`.
- Admin: `php/admin.php` contient une page HTML complete avec CSS inline et JavaScript embarque.
- Auth admin: cookie `WC_TOKEN`, JWT HMAC SHA-256 signe avec `AUTH_SHARED_SECRET`, liste blanche `ALLOWED_DISCORD_IDS`.
- BDD active attendue par le code: PostgreSQL via PDO `pgsql`.
- BDD historique presente dans le repo: snapshots SQLite dans `backups/`.
- Styles et rendu: concentres dans `css/style.css`; `css/style_dark_mode.css` existe mais n'est pas reference par `index.html`.
- Assets: `img/` contient logos, favicons, images de maintenance, icones map/vehicle/tuning.

## Structure actuelle

```text
.
|-- index.php
|-- index.html
|-- maintenance.html
|-- privacy.html
|-- README.md
|-- test_curl.php
|-- auth/
|   |-- admin_actions.php
|   |-- admin_pending.php
|   |-- check_auth.php
|   |-- config.php
|   |-- logout.php
|   |-- post_news.php
|   `-- status.php
|-- php/
|   |-- add_map.php
|   |-- add_tuning_part.php
|   |-- add_tuning_setup.php
|   |-- add_vehicle.php
|   |-- admin.php
|   |-- api_records.php
|   |-- assign_setup.php
|   |-- delete_record.php
|   |-- get_hcaptcha_sitekey.php
|   |-- get_news.php
|   |-- load_data.php
|   |-- maintenance_helpers.php
|   |-- maintenance_status.php
|   |-- public_submit.php
|   |-- set_maintenance.php
|   |-- set_questionable.php
|   |-- submit_record.php
|   `-- test_curl.php
|-- js/
|   `-- script.js
|-- css/
|   |-- style.css
|   `-- style_dark_mode.css
|-- img/
|   |-- map_icons/
|   |-- vehicle_icons/
|   `-- tuning_parts_icons/
`-- backups/
    |-- main-20260326-023356.sqlite
    `-- main-20260403-073123.sqlite
```

## Inventaire par type

- PHP: 27 fichiers.
- HTML: 3 fichiers.
- JavaScript: 1 fichier principal, `js/script.js` environ 1913 lignes.
- CSS: 2 fichiers, `style.css` environ 2058 lignes et `style_dark_mode.css` environ 1372 lignes.
- SVG: 75 assets d'icones.
- PNG: 10 assets.
- SQLite: 2 backups historiques.

## Points d'entree

- `/index.php`: applique `enforce_maintenance_html()` puis sert `/index.html`.
- `/index.html`: page publique principale, peut aussi etre servie directement.
- `/maintenance.html`: page statique de maintenance.
- `/privacy.html`: politique de confidentialite statique.
- `/php/admin.php`: page admin protegee.
- `/php/*.php` et `/auth/*.php`: endpoints JSON ou actions admin.
- `/php/api_records.php`: API publique protegee par cle API.
- `/test_curl.php` et `/php/test_curl.php`: scripts de diagnostic HTTP.

## Validation statique effectuee

Commande executee:

```powershell
Get-ChildItem -Recurse -File -Filter *.php | ForEach-Object { php -l $_.FullName }
```

Resultat: aucun fichier PHP ne presente d'erreur de syntaxe.

## Technologies detectees

- PHP 7.4 disponible localement.
- JavaScript vanilla cote navigateur.
- CSS vanilla responsive.
- PDO PostgreSQL cote backend.
- hCaptcha cote soumission publique.
- Discord OAuth externe via `https://auth.hcr2.xyz/login`, puis cookie `WC_TOKEN`.
- Appels GitHub publics depuis le front pour afficher la version/release.

## Variables d'environnement actuelles

Documentees dans `.env.example`:

```text
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASS
AUTH_SHARED_SECRET
ALLOWED_DISCORD_IDS
API_KEYS
HCAPTCHA_SITE_KEY
HCAPTCHA_SECRET_KEY
```

Notes:

- Le code exige `AUTH_SHARED_SECRET` au chargement de `auth/config.php`.
- La connexion BDD est construite en DSN `pgsql:host=...;port=...;dbname=...`.
- `ALLOWED_DISCORD_IDS` et `API_KEYS` sont des listes separees par virgule ou retour ligne.
- Les secrets ne sont pas presents dans le repo.

## Authentification et securite

Fichiers principaux:

- `auth/config.php`: charge `.env`, configure les cookies de session, expose `get_database_connection()`, definit les headers de securite.
- `auth/check_auth.php`: verifie le JWT `WC_TOKEN`, reconstruit `$_SESSION['discord']`, fournit `ensure_authorized()` et `ensure_authorized_json()`.
- `auth/status.php`: retourne `{ logged, allowed, id, username }`.
- `auth/logout.php`: detruit session et cookie `WC_TOKEN`, puis redirige vers `/`.

Comportement a conserver:

- Cookie `WC_TOKEN` requis pour l'admin.
- Signature HMAC SHA-256 via `AUTH_SHARED_SECRET`.
- Rejet si JWT expire ou invalide.
- Admin autorise uniquement si `sub` est dans `ALLOWED_DISCORD_IDS`.
- Cookie `WC_TOKEN` supprime si token invalide.
- Sessions avec `secure`, `httponly`, `samesite=Lax`, domaine `.hcr2.xyz`.

## Front public

`index.html` contient:

- Header avec logo, titre, sous-titre, note mobile.
- Boutons: Get Maps, Get Vehicles, Get Players, Get Tuning Parts, Get Records, Stats, Submit Record, News.
- Bouton login Discord.
- Bouton Admin affiche seulement si autorise.
- Bouton Logout affiche si connecte.
- Toggle dark mode.
- Sections dynamiques `#stats-container` et `#data-container`.
- Section About / Guidelines / Viewing Records / Submitting Records / Statistics / News / Follow Us.
- Modales:
  - soumission publique,
  - news,
  - note de record.
- Footer avec source GitHub, version GitHub et lien privacy.

`js/script.js` gere:

- Cache fetch JSON simple avec TTL 60s.
- Dark mode via `localStorage.darkMode`.
- Indicateur news via `localStorage.unreadNews`.
- Chargement paresseux d'images `data-src`.
- Echappement HTML `esc()`.
- Rendu des pays avec flags `flagcdn.com`.
- Rendu des icones maps/vehicles/tuning depuis `img/*_icons/`.
- Appels backend `php/load_data.php`.
- Tables maps, vehicles, players, tuning parts, records.
- Filtres records: recherche texte, map, vehicle, tuning, distance, questionable, verified.
- Tri records: default, distance asc/desc, most recent.
- Export CSV.
- Stats detaillees.
- Auth status avec retries et refresh toutes les 30s.
- Modale hCaptcha et soumission publique.
- News publiques.
- Deep links `?view=...&recordId=...&map=...`.
- Menu mobile avec focus management.

## Admin

`php/admin.php` est une page PHP protegee qui rend HTML + CSS inline + JS inline.

Fonctions admin visibles:

- Ajouter/remplacer un record.
- Supprimer un record.
- Marquer un record comme questionable/verifie avec note.
- Assigner un tuning setup a un record existant.
- Ajouter un vehicle avec icone SVG optionnelle.
- Ajouter une map avec icone SVG optionnelle.
- Ajouter une tuning part avec icone SVG optionnelle.
- Ajouter un tuning setup.
- Voir/approver/rejeter les soumissions publiques en attente.
- Poster des news.
- Lister/supprimer des backups.
- Integrity check BDD.
- Activer/desactiver le mode maintenance.

## Mode maintenance

Fichiers:

- `php/maintenance_helpers.php`
- `php/maintenance_status.php`
- `php/set_maintenance.php`
- `maintenance.html`

Mecanisme:

- Flag fichier `MAINTENANCE` a la racine.
- Si actif et utilisateur non-admin:
  - HTML: reponse 503 avec page maintenance.
  - JSON: reponse 503 `{ "error": "Site is under maintenance. Please try again later." }`.
- Admin detecte via session Discord et `ALLOWED_DISCORD_IDS`.

## Assets critiques

Assets publics:

- `img/hcrdatabaselogo.png`
- `img/Discord-Symbol-Blurple.png`
- `img/image copy.png`
- `img/image.png`
- `img/maintenanceon.png`
- favicons et manifest dans `img/`

Icones dynamiques:

- Maps: `img/map_icons/<nom_normalise>.svg`
- Vehicles: `img/vehicle_icons/<nom_normalise>.svg`
- Tuning parts: `img/tuning_parts_icons/<nom_normalise>.svg`

Regle de normalisation front:

- lowercase
- espaces remplaces par `_`
- suppression des caracteres hors `[a-z0-9_-]`

Les endpoints admin d'upload SVG doivent conserver cette convention de nommage.

## Scripts critiques

- `test_curl.php` et `php/test_curl.php`: diagnostic de capacite HTTP sortante vers hCaptcha.
- `.github/ISSUE_TEMPLATE/bug_report.md`: template GitHub.
- Pas de `package.json`, `requirements.txt`, `composer.json` ou systeme de build detecte dans l'etat actuel.

## Points sensibles detectes

- Le comportement metier est fortement disperse dans `js/script.js`, `php/admin.php` et les endpoints PHP.
- Le rendu public depend de HTML genere en chaine dans `js/script.js`.
- `php/admin.php` duplique une partie de la logique front/admin.
- Les tables de production semblent prefixees `_map`, `_vehicle`, `_player`, `_worldrecord`, etc., alors que les backups SQLite contiennent `Map`, `Vehicle`, `Player`, `WorldRecord`, etc.
- Le champ `questionable_reason` est attendu par le code PostgreSQL mais absent des snapshots SQLite inspectes.
- `php/delete_record.php` contient `require_once __DIR__ . '/auth/check_auth.php'`, qui pointe vers `php/auth/check_auth.php`; ce chemin semble incoherent avec le reste du projet. Il est documente comme risque existant, pas corrige dans cette etape.
- `php/add_tuning_setup.php` impose cote backend 3 ou 4 parts, mais `php/admin.php` valide cote front 2 a 4 parts. Ce decalage existe deja et doit etre preserve/documente avant correction eventuelle explicite.
- `auth/admin_actions.php` affiche des controles backups/import/restore, mais les actions backup creation, restore et import renvoient maintenant des erreurs car PostgreSQL n'est pas supporte par cet endpoint.
- Les textes affiches par PowerShell montrent des caracteres mal decodes, mais cela semble lie a l'affichage terminal; le comportement navigateur doit etre verifie avant toute normalisation d'encodage.

## Regle de migration issue de l'audit

La migration doit partir des contrats existants, pas d'une reinterpretation produit:

1. Documenter les routes et payloads avant de coder.
2. Construire FastAPI en compatibilite avec les endpoints PHP.
3. Garder les endpoints PHP actifs pendant la transition.
4. Porter d'abord les retours JSON puis seulement les ecrans React.
5. Garder les assets et CSS existants comme reference visuelle.
6. Ajouter des tests de contrat avant de remplacer les routes.
