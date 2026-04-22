# Rapport d'alignement refonte / main

Date: 2026-04-22

## Base de comparaison

- Branche de refonte: `refactor/fastapi-react-migration`
- Branche cible: `origin/main`
- Base commune: `ff55f47629d4100f9b80cd0ad5cfee7090cf4972`

`main` a continué sur le runtime PHP historique, tandis que la refonte a basculé le runtime officiel vers FastAPI + React/Vite et a isolé l'ancien PHP dans `to_delete/`. La fusion ne pouvait donc pas être un merge direct: elle aurait supprimé le backend/frontend de refonte et restauré l'ancienne structure racine.

## Grands écarts identifiés

### Structure applicative

- `main` remet les assets, PHP, CSS et JS legacy en racine.
- La refonte conserve:
  - `backend/` pour FastAPI;
  - `frontend/` pour React/Vite;
  - `infra/dev/` pour PostgreSQL local;
  - `to_delete/` comme référence legacy temporaire.

Arbitrage: conserver la refonte comme runtime officiel et porter les corrections métier/BDD de `main` dans FastAPI/React.

### Base de données

`main` introduit une normalisation PostgreSQL complète:

- tables sans préfixe underscore: `map`, `vehicle`, `player`, `tuning_part`, `tuning_setup`, `tuning_setup_part`, `world_record`, `pending_submission`, `news`;
- colonnes `snake_case`: `id_map`, `name_map`, `id_record`, `id_tuning_setup`, etc.;
- séquences PostgreSQL explicites: `map_id_seq`, `world_record_id_seq`, `pending_submission_id_seq`, etc.;
- clés primaires et étrangères;
- contrainte `pending_submission_status_check`;
- index de lecture et d'intégrité;
- consolidation de `_news` vers `news` et de `_pendingsubmission` vers `pending_submission`;
- suppression de l'hypothèse `MAX(id)+1` côté application.

### Contrats API

`main` standardise les requêtes SQL en `snake_case`, mais restaure des clés camelCase dans les réponses publiques PHP, par exemple `idMap`, `nameVehicle`, `idTuningSetup`.

Arbitrage: utiliser le schéma `snake_case` en interne, mais préserver les réponses camelCase attendues par le front et les routes compat PHP.

## Changements repris depuis main

- Ajout des migrations SQL de `main` dans `migrations/`.
- Mise à jour du schéma dev PostgreSQL:
  - `infra/dev/postgres/init/001_schema.sql`
  - `infra/dev/postgres/init/002_seed_demo.sql`
- Port des accès BDD FastAPI vers les tables/colonnes canoniques.
- Passage des créations d'entités aux séquences PostgreSQL avec `RETURNING`, sans `MAX(id)+1`.
- Port des validations importantes de `main`:
  - longueurs max map/vehicle/tuning part/player/country;
  - `distance > 0`;
  - `questionable` limité à `0` ou `1`;
  - statuts pending `pending|approved|rejected`;
  - compatibilité `news` et `pending_submission` canoniques.
- Port de `/php/api_records.php` dans la façade FastAPI, avec API key, filtres, pagination et format `{ records, count }`.
- Ajout de routes de compatibilité admin PHP sensibles vers les services FastAPI:
  - record create/delete/questionable/assign;
  - add map/vehicle/tuning part/tuning setup;
  - pending approve/reject;
  - post news;
  - maintenance;
  - admin backup/integrity actions.
- Support des variables PostgreSQL `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `DB_SCHEMA` et `PGSCHEMA`.

## Conflits et arbitrages

- Le layout PHP racine de `main` n'a pas été restauré: il contredit l'objectif de refonte FastAPI/React.
- Les scripts PHP de dry-run de `main` n'ont pas été repris comme runtime: ils dépendent de `auth/config.php` et des endpoints PHP racine. Leur logique utile a été portée côté FastAPI.
- Les migrations SQL de `main` sont conservées comme chemin de production depuis la BDD legacy vers la BDD canonique.
- Le frontend garde ses fallbacks vers quelques anciennes clés lowercase, mais le backend renvoie maintenant les clés camelCase propres.
- Les backups FastAPI restent disponibles, contrairement à l'endpoint PHP de `main` qui désactive la création PostgreSQL; ils ont été alignés sur les tables canoniques.

## Fichiers sensibles modifiés

- Backend API/compat:
  - `backend/app/api/compat.py`
  - `backend/app/api/v1/public.py`
- Backend config/DB:
  - `backend/app/core/config.py`
  - `backend/app/db/session.py`
- Backend data/services:
  - `backend/app/repositories/public_data.py`
  - `backend/app/repositories/news.py`
  - `backend/app/services/admin_service.py`
  - `backend/app/services/public_data_service.py`
  - `backend/app/services/public_submission_service.py`
- Tests:
  - `backend/tests/test_config.py`
  - `backend/tests/test_public_data_service.py`
  - `backend/tests/test_public_endpoints.py`
- BDD/dev:
  - `infra/dev/postgres/init/001_schema.sql`
  - `infra/dev/postgres/init/002_seed_demo.sql`
  - `migrations/*.sql`
- Smoke:
  - `scripts/dev/test_system_smoke.mjs`

## Vérifications effectuées

Commandes passées:

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check app tests
.\.venv\Scripts\python.exe -m pytest
python -m compileall app tests

cd frontend
npm run build

git diff --check

.\scripts\dev\reset-dev-database.ps1
.\scripts\dev\start-app-stack.ps1 -RestartFastApi -RestartFrontend
node .\scripts\dev\test_system_smoke.mjs
```

Résultats:

- Ruff: OK.
- Tests backend: 29 passed.
- Compilation Python: OK.
- Build frontend TypeScript/Vite: OK.
- Diff check: OK, uniquement avertissements CRLF attendus sous Windows.
- Reset PostgreSQL Docker: OK.
- Démarrage FastAPI/Vite: OK.
- Smoke système DB/API/UI: OK.

Le premier lancement du smoke a exposé une incompatibilité des données de test avec les nouvelles limites BDD (`map <= 19`, `vehicle <= 16`, `tuning_part <= 17`). Le script `scripts/dev/test_system_smoke.mjs` utilise maintenant des noms courts conformes au schéma canonique.

## Points à surveiller

- Rejouer les migrations SQL sur un clone/staging avant production.
- Valider les données de production après migration: unicité des noms, absence d'orphelins FK, et présence de `id_record`.
- Vérifier les anciens clients externes de `/php/api_records.php` avec leurs filtres réels.
- Vérifier les uploads SVG admin en environnement réel, surtout chemins et permissions d'écriture dans `frontend/public/img`.
