import { createBrowserRouter } from "react-router-dom";

import { AdminPage } from "../pages/AdminPage";
import { App } from "./App";
import { ChangelogPage } from "../pages/ChangelogPage";
import { DataViewPage } from "../pages/DataViewPage";
import { HomePage } from "../pages/HomePage";
import { MaintenancePage } from "../pages/MaintenancePage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { PrivacyPage } from "../pages/PrivacyPage";
import { StatsPage } from "../pages/StatsPage";
import { TermsOfServicePage } from "../pages/TermsOfServicePage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "maps", element: <DataViewPage view="maps" /> },
      { path: "vehicles", element: <DataViewPage view="vehicles" /> },
      { path: "players", element: <DataViewPage view="players" /> },
      { path: "tuning-parts", element: <DataViewPage view="tuning-parts" /> },
      { path: "tuning-setups", element: <DataViewPage view="tuning-setups" /> },
      { path: "records", element: <DataViewPage view="records" /> },
      { path: "records/mythic", element: <DataViewPage view="records" mythic /> },
      { path: "stats", element: <StatsPage /> },
      { path: "changelog", element: <ChangelogPage /> },
      { path: "*", element: <NotFoundPage /> }
    ]
  },
  { path: "/admin", element: <AdminPage /> },
  { path: "/privacy", element: <PrivacyPage /> },
  { path: "/terms", element: <TermsOfServicePage /> },
  { path: "/maintenance", element: <MaintenancePage /> }
]);
