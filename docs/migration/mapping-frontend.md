# Mapping frontend existant

Date: 2026-04-20

Ce document mappe l'interface actuelle vers l'architecture React + Vite + TypeScript cible.

## Etat actuel

Fichiers:

- `index.html`: structure publique et modales.
- `js/script.js`: toute la logique UI publique.
- `css/style.css`: rendu principal, responsive et dark mode.
- `css/style_dark_mode.css`: fichier alternatif/non reference par `index.html`.
- `php/admin.php`: admin HTML/CSS/JS embarque.
- `privacy.html`: page statique.
- `maintenance.html`: page statique.

Il n'y a pas de build frontend, pas de routing client, pas de typage, pas de composants.

## Architecture cible proposee

```text
frontend/
|-- index.html
|-- package.json
|-- tsconfig.json
|-- vite.config.ts
|-- src/
|   |-- app/
|   |   |-- App.tsx
|   |   |-- router.tsx
|   |   `-- queryClient.ts
|   |-- pages/
|   |   |-- PublicHomePage.tsx
|   |   |-- AdminPage.tsx
|   |   |-- PrivacyPage.tsx
|   |   `-- MaintenancePage.tsx
|   |-- components/
|   |   |-- layout/
|   |   |-- tables/
|   |   |-- modals/
|   |   `-- ui/
|   |-- features/
|   |   |-- auth/
|   |   |-- records/
|   |   |-- stats/
|   |   |-- submissions/
|   |   |-- news/
|   |   |-- admin/
|   |   `-- maintenance/
|   |-- services/
|   |   |-- apiClient.ts
|   |   |-- legacyEndpoints.ts
|   |   `-- queryKeys.ts
|   |-- hooks/
|   |-- lib/
|   |-- types/
|   |-- assets/
|   `-- styles/
|       |-- legacy.css
|       `-- globals.css
```

Regle de depart: importer le CSS existant tel quel comme `legacy.css`, puis extraire progressivement sans changer le rendu.

## Pages et vues actuelles

### Public home

Depuis `index.html`.

Elements:

- Header gradient bleu.
- Logo.
- Titre: `HCR2 Adventure Records (unofficial)`.
- Sous-titre: `Community world records & stats`.
- Boutons de navigation.
- Login Discord, Admin, Logout.
- Dark mode button.
- Zone warnings auth.
- Containers dynamiques stats/data.
- Section about/guidelines/viewing/submitting/statistics/news/follow.
- Footer GitHub/version/privacy.

Cible React:

- `PublicHomePage`
- `Header`
- `PublicNav`
- `DataViewContainer`
- `AboutSections`
- `Footer`
- `DarkModeToggle`

### Vues dynamiques publiques

Actuel: bouton -> `fetchData(type)` -> table.

Types:

- maps
- vehicles
- players
- tuning_parts
- records

Cible:

- React Router peut garder une route principale avec query param:
  - `/`
  - `/?view=records`
  - `/?view=players`
- ou routes internes:
  - `/records`
  - `/players`

Choix prudent:

- Conserver les query params legacy dans une premiere passe.
- Ajouter React Router pour structurer les pages sans casser les liens actuels.

### Stats

Actuel: `fetchStats()` charge les records puis rend plusieurs blocs.

Blocs:

- Vehicle Statistics avec select:
  - Total Distance
  - Longest Distance
  - Average Placement
  - Highest Placement
  - Lowest Placement
- Vehicle Rankings by Adventure Stars.
- Top 10 Players by Record Count.
- Records by Country avec canvas pie chart.
- Map Statistics.
- Map Rankings by Adventure Stars.
- Tuning Part Statistics.
- Overall Statistics.

Regle metier a conserver:

- Special maps: `Forest Trials`, `Intense City`, `Raging Winter`.
- Stars special map: distance >= 5000 => 15000, sinon distance * 3.
- Stars autres maps: distance >= 10000 => 10000, sinon distance.
- Country counts <= 5 regroupes en `Other countries`.

Cible:

- `features/stats/StatsView.tsx`
- fonctions pures dans `features/stats/statsCalculations.ts`
- tests unitaires sur calculs.

### Records

Colonnes:

- Distance
- Status
- Notes
- Map Name
- Vehicle Name
- Tuning Parts
- Player Name
- Player Country
- Share

Filtres:

- recherche texte player/map/vehicle/notes,
- map multi-select,
- vehicle multi-select,
- tuning multi-select avec `every`,
- distance `gte/lte`,
- questionable only,
- verified only.

Tri:

- default: map name, vehicle id si dispo, puis vehicle name.
- distance asc.
- distance desc.
- most recent par `idRecord`.

Cible:

- `features/records/RecordsTable.tsx`
- `features/records/RecordsFilters.tsx`
- `features/records/useRecordsViewModel.ts`
- conserver exactement les labels, ordre des colonnes et formats.

### Players

Actuel:

- Table player id/name/country/world records.
- World records calcule cote front en chargeant aussi records.
- Filtres: recherche player/country, country multi-select, record count gte/lte.

Cible:

- `features/players/PlayersView.tsx`
- `usePlayersQuery`, `useRecordsQuery`.

### Public submission

Actuel:

- Modale.
- Form fields: map, vehicle, distance, player name, country optional, tuning parts, hCaptcha, honeypots.
- Validation front.
- POST `php/public_submit.php`.

Cible:

- `features/submissions/PublicSubmissionModal.tsx`
- `services/submissionsApi.ts`
- TanStack mutation.
- Garder hCaptcha integration et champs honeypot.

### News

Actuel:

- Bouton News.
- Modale.
- Fetch `php/get_news.php`.
- `localStorage.unreadNews`.

Cible:

- `features/news/NewsModal.tsx`
- `useNewsQuery`.

### Auth UI

Actuel:

- Poll `/auth/status.php` au load, retry 1s, puis toutes les 30s.
- Login redirige `https://auth.hcr2.xyz/login`.
- Logout `auth/logout.php`.
- Admin button vers `php/admin.php`.

Cible:

- `features/auth/useAuthStatus.ts`
- TanStack Query avec refetchInterval 30000.
- Garder les URLs au debut.

### Admin page

Actuel:

- `php/admin.php` autonome.
- HTML/CSS/JS inline.

Cible:

- Phase initiale: garder `php/admin.php` tant que le backend FastAPI n'a pas tous les endpoints admin.
- Phase React admin:
  - `pages/AdminPage.tsx`
  - `features/admin/*`
  - acces preserve via auth status/admin guard.

Ne pas migrer l'admin trop tot: c'est la zone la plus sensible.

## Assets frontend a conserver

Copie ou reference depuis `img/`:

- `hcrdatabaselogo.png`
- `Discord-Symbol-Blurple.png`
- `image copy.png`
- `image.png`
- `maintenanceon.png`
- favicons et manifest
- `map_icons/*.svg`
- `vehicle_icons/*.svg`
- `tuning_parts_icons/*.svg`

Convention d'URL actuelle:

- `/img/map_icons/<icon>.svg`
- `/img/vehicle_icons/<icon>.svg`
- `/img/tuning_parts_icons/<icon>.svg`

Choix prudent:

- Garder ces assets servis au meme chemin pendant une phase de compatibilite.
- Dans Vite, configurer `public/img/...` ou proxy/static copy pour conserver `/img/...`.

## Styles a preserver

Source visuelle principale:

- `css/style.css`

Themes:

- Variables CSS `:root`.
- Dark mode via `[data-theme="dark"]`.
- Toggle stocke `localStorage.darkMode`.

Composants styles importants:

- Header/branding/menu mobile.
- Buttons.
- Tables.
- Modales.
- Form containers.
- Filters/dropdowns.
- Icons map/vehicle/tuning.
- Charts/stats.
- Public records table responsive.

Regle:

- Premiere migration React doit importer le CSS legacy.
- Aucune refonte UI ou changement de palette.
- Les classes CSS existantes doivent etre reutilisees.

## Services API cibles

```text
services/
|-- apiClient.ts
|-- publicDataApi.ts
|-- recordsApi.ts
|-- authApi.ts
|-- submissionsApi.ts
|-- newsApi.ts
|-- adminApi.ts
`-- maintenanceApi.ts
```

TanStack Query:

- `useMapsQuery`
- `useVehiclesQuery`
- `usePlayersQuery`
- `useTuningPartsQuery`
- `useTuningSetupsQuery`
- `useRecordsQuery`
- `useAuthStatusQuery`
- `useNewsQuery`
- mutations admin/public.

## Types TypeScript initiaux

```ts
export interface MapItem {
  idMap: number;
  nameMap: string;
}

export interface VehicleItem {
  idVehicle: number;
  nameVehicle: string;
}

export interface PlayerItem {
  idPlayer: number;
  namePlayer: string;
  country?: string | null;
}

export interface TuningPart {
  idTuningPart: number;
  nameTuningPart: string;
}

export interface TuningSetup {
  idTuningSetup: number;
  parts: Array<{ nameTuningPart: string }>;
}

export interface RecordItem {
  idRecord: number;
  distance: number;
  current: number;
  idTuningSetup?: number | null;
  questionable: number;
  questionable_reason?: string;
  map_name: string;
  vehicle_name: string;
  player_name: string;
  player_country?: string | null;
  tuning_parts?: string | null;
}
```

## Decoupage progressif recommande

1. Copier CSS/assets dans `frontend` en conservant chemins publics.
2. Creer Vite React TS minimal.
3. Monter `PublicHomePage` avec HTML statique equivalent.
4. Brancher `AuthStatus`, dark mode, mobile menu.
5. Migrer une vue read-only simple: maps.
6. Migrer vehicles, tuning parts, players.
7. Migrer records avec filtres/tri/export.
8. Migrer stats et tests calculs.
9. Migrer modales public submit/news/note.
10. Migrer privacy/maintenance.
11. Migrer admin seulement apres backend FastAPI complet.

## Risques front

- HTML genere en string dans `script.js`; port React peut changer subtilement l'ordre DOM ou l'echappement.
- Styles responsive tres sensibles aux classes existantes.
- Dark mode depend de `data-theme` sur `documentElement`.
- hCaptcha depend d'un script externe charge dans le HTML.
- Flags pays dependent de `flagcdn.com`.
- GitHub version fetch peut echouer hors ligne; fallback `unknown`.
- Deep links doivent continuer a fonctionner.
- Certains textes dans les fichiers semblent mal affiches dans terminal; ne pas "corriger" l'encodage sans verification navigateur.

## Definition de non-regression visuelle front

Pour chaque vue migree:

- comparer capture legacy vs React desktop.
- comparer capture legacy vs React mobile.
- verifier header, boutons, tables, modales, dark mode.
- verifier absence de chevauchement texte.
- verifier icones chargees.
- verifier filtres et tri.
- verifier que les textes utilisateur restent identiques.
