import { useState } from "react";
import { Link, NavLink } from "react-router-dom";

import { NewsModal } from "./NewsModal";
import { PublicSubmitModal } from "./PublicSubmitModal";
import { useAuthStatus } from "../hooks/useAuthStatus";
import { useDarkMode } from "../hooks/useDarkMode";

const navItems = [
  { label: "Get Maps", to: "/maps" },
  { label: "Get Vehicles", to: "/vehicles" },
  { label: "Get Players", to: "/players" },
  { label: "Get Tuning Parts", to: "/tuning-parts" },
  { label: "Get Records", to: "/records" },
  { label: "Stats", to: "/stats" }
];

export function Header() {
  const { data: authStatus } = useAuthStatus();
  const { isDark, toggleDarkMode } = useDarkMode();
  const [isMenuOpen, setMenuOpen] = useState(false);
  const [isNewsOpen, setNewsOpen] = useState(false);
  const [isSubmitOpen, setSubmitOpen] = useState(false);

  function closeMobileMenu() {
    setMenuOpen(false);
  }

  return (
    <>
      <header>
        <div className="device-note" id="device-note">
          💻 Works best on laptop / PC for full functionality
        </div>
        <div className="header-inner">
          <Link className="branding" to="/" onClick={closeMobileMenu}>
            <img src="/img/hcrdatabaselogo.png" alt="Logo" id="logo" />
            <div>
              <h1>HCR2 Adventure Records (unofficial)</h1>
              <div style={{ fontSize: "16px", opacity: 0.9 }}>Community world records & stats</div>
            </div>
          </Link>

          <button
            id="mobile-menu-btn"
            className="mobile-menu-btn"
            type="button"
            aria-expanded={isMenuOpen}
            aria-controls="mobile-menu"
            onClick={() => setMenuOpen((open) => !open)}
          >
            <span className="sr-only">Open menu</span>☰
          </button>

          <nav id="mobile-menu" className="header-right" aria-hidden={isMenuOpen ? "false" : "true"}>
            <div className="header-buttons" aria-hidden="false">
              {navItems.map((item) => (
                <NavLink key={item.to} to={item.to} onClick={closeMobileMenu}>
                  {() => <button type="button">{item.label}</button>}
                </NavLink>
              ))}

              <button
                type="button"
                onClick={() => {
                  closeMobileMenu();
                  setSubmitOpen(true);
                }}
              >
                Submit Record
              </button>
              <span id="news-btn-container">
                <button
                  type="button"
                  onClick={() => {
                    closeMobileMenu();
                    setNewsOpen(true);
                  }}
                >
                  News
                </button>
                <span className="news-indicator" style={{ display: "none" }} />
              </span>

              {!authStatus?.logged && (
                <button
                  id="login-btn"
                  type="button"
                  className="discord-btn"
                  onClick={() => {
                    window.location.href = "https://auth.hcr2.xyz/login";
                  }}
                >
                  <img className="discord-logo" src="/img/Discord-Symbol-Blurple.png" alt="Discord" />
                  <span>Sign in with Discord</span>
                </button>
              )}

              {authStatus?.allowed && (
                <NavLink to="/admin" onClick={closeMobileMenu}>
                  {() => (
                    <button id="admin-btn" type="button">
                      Admin
                    </button>
                  )}
                </NavLink>
              )}

              {authStatus?.logged && (
                <button
                  id="logout-btn"
                  type="button"
                  onClick={() => {
                    window.location.href = "/auth/logout.php";
                  }}
                >
                  Logout
                </button>
              )}
            </div>
          </nav>
          <button
            type="button"
            id="dark-mode-toggle"
            className="dark-mode-btn"
            aria-label="Toggle dark mode"
            title="Toggle dark mode"
            onClick={toggleDarkMode}
          >
            {isDark ? "☀️" : "🌙"}
          </button>
        </div>

        <div id="auth-warning" style={{ color: "orange", padding: "8px 0", textAlign: "left" }} />
      </header>
      {isNewsOpen && <NewsModal onClose={() => setNewsOpen(false)} />}
      {isSubmitOpen && <PublicSubmitModal onClose={() => setSubmitOpen(false)} />}
    </>
  );
}
