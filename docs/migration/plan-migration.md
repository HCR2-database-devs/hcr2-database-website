# Plan de migration progressif

Date: 2026-04-20

Objectif: migrer vers FastAPI + React/Vite/TypeScript sans regression fonctionnelle ni visuelle.

## Principes non negociables

- Aucun big bang.
- Aucun changement produit non demande.
- Les routes legacy restent utilisables tant que le front legacy en depend.
- Les shapes JSON restent compatibles.
- Les styles et assets existants servent de reference visuelle.
- Les comportements douteux existants sont documentes avant correction.
- Les suppressions de code legacy arrivent seulement apres bascule verifiee.

## Architecture cible

```text
.
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- api/
|   |   |-- core/
|   |   |-- db/
|   |   |-- models/
|   |   |-- schemas/
|   |   |-- services/
|   |   |-- repositories/
|   |   `-- utils/
|   `-- tests/
|-- frontend/
|   |-- src/
|   |   |-- app/
|   |   |-- pages/
|   |   |-- components/
|   |   |-- features/
|   |   |-- services/
|   |   |-- hooks/
|   |   |-- lib/
|   |   |-- types/
|   |   |-- assets/
|   |   `-- styles/
|   `-- tests/
|-- docs/
|   `-- migration/
|-- scripts/
|-- infra/
`-- legacy/
```

Note: le dossier `legacy/` ne doit etre cree qu'au moment ou les fichiers legacy sont stabilises et que les chemins publics restent preserves via serveur/proxy. Dans les premieres phases, il est plus prudent de laisser les fichiers PHP/HTML/CSS/JS a leur place.

## Phase A - Stabilisation et contrats

But: figer l'existant avant migration.

Livrables:

- Documentation d'audit dans `docs/migration/`.
- Contrats endpoints legacy.
- Inventaire assets et flux.
- Verification PHP lint.
- Plan de tests de non-regression.

Actions:

1. Creer branche dediee.
2. Ajouter documentation initiale.
3. Ajouter si possible des tests de contrat read-only sur les JSON legacy, avec mocks ou fixtures.
4. Ajouter une documentation `.env.example` plus claire sans changer le chargement runtime.
5. Ajouter README d'architecture cible.

Risques:

- Impossible de tester fonctionnellement sans `.env` et BDD PostgreSQL.
- Encodage terminal affiche des caracteres corrompus; verifier dans navigateur avant toute correction.

Critere de sortie:

- Audit commite.
- Liste des routes connue.
- Plan de migration valide dans le repo.

## Phase B - Backend FastAPI compatible

But: creer un backend FastAPI qui reproduit les endpoints PHP.

Ordre de travail:

1. Bootstrap `backend/`:
   - `pyproject.toml` ou `requirements.txt`,
   - FastAPI,
   - Pydantic Settings,
   - Uvicorn,
   - client PostgreSQL,
   - pytest.
2. Config:
   - lire les memes variables d'environnement,
   - ajouter `.env.example` backend documente.
3. DB:
   - connexion PostgreSQL,
   - repositories SQL alignes sur PHP.
4. Public read-only:
   - maps,
   - vehicles,
   - players,
   - tuning parts,
   - tuning setups,
   - records.
5. Auth:
   - verifier `WC_TOKEN`,
   - status/logout compatibles.
6. News public/admin.
7. Public submissions:
   - hCaptcha,
   - honeypots,
   - rate limit,
   - PendingSubmission.
8. Admin records/catalog/submissions.
9. Maintenance.
10. API records avec API key.
11. Admin actions/backups en compatibilite stricte.

Strategie routes:

- Exposer d'abord les routes propres `/api/v1/...`.
- Ajouter des aliases legacy compatibles ou un adaptateur pour:
  - `/php/load_data.php`
  - `/auth/status.php`
  - etc.
- Le front legacy peut ensuite etre pointe vers FastAPI via proxy sans changement UI.

Tests backend:

- Tests unitaires services.
- Tests repositories avec DB de test ou mocks.
- Tests de contrat pour chaque endpoint.
- Tests auth JWT.
- Tests validations hCaptcha en mock.

Critere de sortie:

- FastAPI retourne les memes JSON que PHP pour les endpoints read-only.
- Mutations admin reproduisent les effets existants.
- Aucun endpoint sensible n'est migre sans test de contrat.

## Phase C - Frontend React/Vite/TypeScript

But: reconstruire l'interface actuelle sans changement visuel.

Ordre de travail:

1. Bootstrap `frontend/`:
   - Vite React TS,
   - React Router,
   - TanStack Query,
   - configuration build.
2. Styles/assets:
   - importer `style.css` comme CSS legacy,
   - conserver `/img/...`.
3. Layout public statique:
   - header,
   - boutons,
   - about,
   - footer.
4. Auth status:
   - reproduire affichage login/logout/admin.
5. Dark mode:
   - `localStorage.darkMode`,
   - `data-theme`.
6. Vues read-only:
   - maps,
   - vehicles,
   - tuning parts,
   - players.
7. Records:
   - table,
   - tri,
   - filtres,
   - export CSV,
   - share links,
   - note modal.
8. Stats:
   - port des calculs en fonctions pures,
   - rendu identique.
9. Public submit:
   - hCaptcha,
   - validations,
   - honeypots.
10. News.
11. Privacy/Maintenance.
12. Admin React seulement apres stabilisation backend.

Tests frontend:

- TypeScript strict.
- Tests unitaires calculs stats/filtres.
- Playwright captures desktop/mobile:
  - page initiale,
  - records,
  - players,
  - stats,
  - submit modal,
  - news modal,
  - dark mode.

Critere de sortie:

- React reproduit le rendu public legacy.
- Les liens existants fonctionnent.
- Aucun parcours public perdu.

## Phase D - Bascule controlee

But: connecter front React au back FastAPI, puis retirer progressivement le legacy.

Actions:

1. Mettre proxy/dev config:
   - frontend -> FastAPI.
2. Comparer legacy PHP vs FastAPI sur endpoints.
3. Comparer legacy UI vs React UI.
4. Activer front React en environnement local.
5. Garder rollback simple vers legacy.
6. Bascule admin apres validation manuelle.
7. Nettoyer code mort uniquement quand:
   - equivalent migre,
   - tests passent,
   - captures comparees,
   - aucun endpoint encore consomme.

Critere de sortie:

- Front React + FastAPI fonctionnent ensemble.
- Docs README a jour.
- Legacy isole ou supprime uniquement si certain.

## Plan de commits recommande

1. `docs: add existing architecture migration audit`
2. `chore: scaffold backend FastAPI project`
3. `feat: add FastAPI config and health checks`
4. `feat: port public read-only data endpoints`
5. `feat: add auth compatibility endpoints`
6. `feat: port public submissions and news endpoints`
7. `feat: port admin record management endpoints`
8. `chore: scaffold React Vite TypeScript frontend`
9. `refactor: port public shell with legacy styles`
10. `feat: port public data views with TanStack Query`
11. `feat: port records filters and stats views`
12. `feat: port public submission and news modals`
13. `feat: connect React frontend to FastAPI`
14. `docs: finalize migration runbook`

## Risques majeurs

| Risque | Impact | Mitigation |
| --- | --- | --- |
| Schema PostgreSQL different des backups SQLite | Bugs data | Auditer schema production avant mutations |
| UI generee par string HTML | Ecart visuel React | Import CSS legacy + screenshots |
| Auth depend d'un service externe | Tests locaux incomplets | Fixtures JWT et mocks |
| hCaptcha externe | Tests instables | Service mockable |
| Admin concentre dans un seul fichier | Regression admin | Migrer tard, avec tests de contrat |
| Backups PostgreSQL non supportes | Confusion admin | Reproduire comportement actuel avant amelioration |
| Encodage | Textes alteres | Ne pas normaliser sans verification navigateur |

## Checklists de non-regression

### Backend

- `load_data` retourne les memes champs.
- Les erreurs restent exploitables par le front.
- Auth status garde `logged`, `allowed`, `id`, `username`.
- Maintenance retourne 503 comme avant.
- Public submit garde hCaptcha/honeypot/rate limit.
- Admin approve remplace bien le record map+vehicle.
- Tuning setup refuse les doublons.
- API key records garde filtres/limit/offset.

### Frontend

- Header identique.
- Boutons identiques.
- About text conserve.
- Tables et filtres identiques.
- Stats calculees identiquement.
- Dark mode conserve.
- Modales conservees.
- Icons et flags visibles.
- Deep links records fonctionnels.
- Export CSV identique.

## Decision actuelle

Ne pas commencer la migration technique lourde avant que cette documentation initiale soit commitee.

La prochaine etape technique prudente apres ce commit sera le bootstrap backend FastAPI minimal, avec healthcheck et configuration, sans remplacer les endpoints PHP existants.
