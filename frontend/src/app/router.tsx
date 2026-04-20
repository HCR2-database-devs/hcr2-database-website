import { createBrowserRouter } from "react-router-dom";

import { App } from "./App";
import { DataViewPage } from "../pages/DataViewPage";
import { HomePage } from "../pages/HomePage";
import { MaintenancePage } from "../pages/MaintenancePage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { PrivacyPage } from "../pages/PrivacyPage";
import { StatsPage } from "../pages/StatsPage";

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
      { path: "stats", element: <StatsPage /> },
      { path: "privacy", element: <PrivacyPage /> },
      { path: "maintenance", element: <MaintenancePage /> },
      { path: "*", element: <NotFoundPage /> }
    ]
  }
]);
