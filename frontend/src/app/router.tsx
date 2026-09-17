import { lazy } from "react";
import { createBrowserRouter } from "react-router-dom";

import { App } from "./App";

const AccountPage = lazy(() => import("../pages/AccountPage").then((m) => ({ default: m.AccountPage })));
const AdminPage = lazy(() => import("../pages/AdminPage").then((m) => ({ default: m.AdminPage })));
const ChangelogPage = lazy(() => import("../pages/ChangelogPage").then((m) => ({ default: m.ChangelogPage })));
const CommunityPage = lazy(() => import("../pages/CommunityPage").then((m) => ({ default: m.CommunityPage })));
const CommunityProfilePage = lazy(() =>
  import("../pages/CommunityProfilePage").then((m) => ({ default: m.CommunityProfilePage }))
);
const DataViewPage = lazy(() => import("../pages/DataViewPage").then((m) => ({ default: m.DataViewPage })));
const GuidelinesPage = lazy(() => import("../pages/GuidelinesPage").then((m) => ({ default: m.GuidelinesPage })));
const HomePage = lazy(() => import("../pages/HomePage").then((m) => ({ default: m.HomePage })));
const MaintenancePage = lazy(() => import("../pages/MaintenancePage").then((m) => ({ default: m.MaintenancePage })));
const NotFoundPage = lazy(() => import("../pages/NotFoundPage").then((m) => ({ default: m.NotFoundPage })));
const OnboardingPage = lazy(() => import("../pages/OnboardingPage").then((m) => ({ default: m.OnboardingPage })));
const PrivacyPage = lazy(() => import("../pages/PrivacyPage").then((m) => ({ default: m.PrivacyPage })));
const StatsPage = lazy(() => import("../pages/StatsPage").then((m) => ({ default: m.StatsPage })));
const TermsOfServicePage = lazy(() =>
  import("../pages/TermsOfServicePage").then((m) => ({ default: m.TermsOfServicePage }))
);

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "account", element: <AccountPage /> },
      { path: "onboarding", element: <OnboardingPage /> },
      { path: "maps", element: <DataViewPage view="maps" /> },
      { path: "vehicles", element: <DataViewPage view="vehicles" /> },
      { path: "players", element: <DataViewPage view="players" /> },
      { path: "tuning-parts", element: <DataViewPage view="tuning-parts" /> },
      { path: "tuning-setups", element: <DataViewPage view="tuning-setups" /> },
      { path: "records", element: <DataViewPage view="records" /> },
      { path: "records/mythic", element: <DataViewPage view="records" mythic /> },
      { path: "stats", element: <StatsPage /> },
      { path: "community", element: <CommunityPage /> },
      { path: "community/:id", element: <CommunityProfilePage /> },
      { path: "changelog", element: <ChangelogPage /> },
      { path: "guidelines", element: <GuidelinesPage /> },
      { path: "*", element: <NotFoundPage /> }
    ]
  },
  { path: "/admin", element: <AdminPage /> },
  { path: "/privacy", element: <PrivacyPage /> },
  { path: "/terms", element: <TermsOfServicePage /> },
  { path: "/maintenance", element: <MaintenancePage /> }
]);