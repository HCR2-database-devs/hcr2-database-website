import { useEffect, useState } from "react";
import { Outlet, useNavigate } from "react-router-dom";

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
      <Header />
      <main>
        <Outlet />
        <Footer />
      </main>
    </>
  );
}
