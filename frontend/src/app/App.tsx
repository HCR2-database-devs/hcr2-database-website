import { useEffect, useState } from "react";
import { Outlet, useNavigate } from "react-router-dom";

import { AdBlockerDetector } from "../components/AdBlockerDetector";
import { AdSenseLoader } from "../components/AdSenseLoader";
import { AdSlot } from "../components/AdSlot";
import { Footer } from "../components/Footer";
import { Header } from "../components/Header";
import { getMaintenanceStatus } from "../services/admin";

export function App() {
  const navigate = useNavigate();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    getMaintenanceStatus()
      .then((data) => {
        if (data.maintenance && !data.allowed) {
          navigate("/maintenance", { replace: true });
        } else {
          setChecking(false);
        }
      })
      .catch(() => setChecking(false));
  }, [navigate]);

  if (checking) return null;

  return (
    <>
      <AdBlockerDetector />
      <AdSenseLoader />
      <Header />
      <main>
        <Outlet />
        <AdSlot slotId="9695011824" />
        <Footer />
      </main>
    </>
  );
}
