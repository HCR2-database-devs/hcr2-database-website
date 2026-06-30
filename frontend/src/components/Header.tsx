import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";

import { NewsModal } from "./NewsModal";
import { PublicSubmitModal } from "./PublicSubmitModal";
import { useAuthStatus } from "../hooks/useAuthStatus";
import { useDarkMode } from "../hooks/useDarkMode";

const navItems = [
  { label: "Maps", to: "/maps" },
  { label: "Vehicles", to: "/vehicles" },
  { label: "Players", to: "/players" },
  { label: "Tuning", to: "/tuning-parts" },
  { label: "Stats", to: "/stats" }
];

function navClassName({ isActive }: { isActive: boolean }) {
  return `nav-link${isActive ? " is-active" : ""}`;
}

export function Header() {
  const { data: authStatus } = useAuthStatus();
  const { isDark, toggleDarkMode } = useDarkMode();
  const [isMenuOpen, setMenuOpen] = useState(false);
  const [isNewsOpen, setNewsOpen] = useState(false);
  const [isSubmitOpen, setSubmitOpen] = useState(false);
  const [isRecordsOpen, setRecordsOpen] = useState(false);
  const recordsRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const closeTimer = useRef<ReturnType<typeof setTimeout>>();

  const isRecordsActive = location.pathname === "/records" || location.pathname.startsWith("/records");

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (recordsRef.current && !recordsRef.current.contains(e.target as Node)) {
        setRecordsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function handleRecordsEnter() {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    setRecordsOpen(true);
  }

  function handleRecordsLeave() {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    closeTimer.current = setTimeout(() => setRecordsOpen(false), 200);
  }

  function closeMobileMenu() {
    setMenuOpen(false);
  }

  return (
    <>
      <header className="site-header">
        <div className="header-inner">
          <Link className="branding" to="/" onClick={closeMobileMenu} aria-label="HCR2 Adventure Records home">
            <img src="/img/hcrdatabaselogo.png" alt="HCR2 Adventure Records" id="logo" />
            <span className="brand-copy">
              <span className="brand-title">HCR2 Records</span>
              <span className="brand-subtitle">Unofficial community database</span>
            </span>
          </Link>

          <button
            id="mobile-menu-btn"
            className="mobile-menu-btn"
            type="button"
            aria-expanded={isMenuOpen}
            aria-controls="mobile-menu"
            onClick={() => setMenuOpen((open) => !open)}
          >
            <span aria-hidden="true">Menu</span>
            <span className="sr-only">Toggle navigation</span>
          </button>

          <nav
            id="mobile-menu"
            className={`header-nav${isMenuOpen ? " is-open" : ""}`}
            aria-label="Primary navigation"
          >
            <div className="nav-links">
              {navItems.map((item) => (
                <NavLink key={item.to} to={item.to} className={navClassName} onClick={closeMobileMenu}>
                  {item.label}
                </NavLink>
              ))}
              <div
                className="nav-dropdown-wrapper"
                ref={recordsRef}
                onMouseEnter={handleRecordsEnter}
                onMouseLeave={handleRecordsLeave}
              >
                <span
                  className={`nav-link${isRecordsActive ? " is-active" : ""}`}
                  role="button"
                  tabIndex={0}
                  onClick={() => setRecordsOpen((prev) => !prev)}
                  onMouseEnter={handleRecordsEnter}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      setRecordsOpen((prev) => !prev);
                    }
                  }}
                >
                  Records
                </span>
                <div
                  className={`nav-dropdown-menu${isRecordsOpen ? " is-open" : ""}`}
                  onMouseEnter={handleRecordsEnter}
                  onMouseLeave={handleRecordsLeave}
                >
                  <NavLink
                    to="/records"
                    end
                    className={navClassName}
                    onClick={() => {
                      closeMobileMenu();
                      setRecordsOpen(false);
                    }}
                  >
                    Normal
                  </NavLink>
                  <NavLink
                    to="/records/mythic"
                    className={navClassName}
                    onClick={() => {
                      closeMobileMenu();
                      setRecordsOpen(false);
                    }}
                  >
                    Mythic
                  </NavLink>
                </div>
              </div>
            </div>

            <div className="header-actions">
              <button
                className="nav-action nav-action--primary"
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
                  className="nav-action"
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
                  className="nav-action discord-btn"
                  onClick={() => {
                    window.location.href = "https://auth.hcr2.xyz/login";
                  }}
                >
                  <img className="discord-logo" src="/img/Discord-Symbol-Blurple.png" alt="" />
                  <span>Discord</span>
                </button>
              )}

              {authStatus?.allowed && (
                <NavLink id="admin-btn" to="/admin" className="nav-action" onClick={closeMobileMenu}>
                  Admin
                </NavLink>
              )}

              {authStatus?.logged && (
                <button
                  id="logout-btn"
                  className="nav-action"
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
            className="theme-toggle"
            aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
            title={isDark ? "Light mode" : "Dark mode"}
            onClick={toggleDarkMode}
          >
            {isDark ? "Light" : "Dark"}
          </button>
        </div>

        <div id="auth-warning" />
      </header>
      {isNewsOpen && <NewsModal onClose={() => setNewsOpen(false)} />}
      {isSubmitOpen && <PublicSubmitModal onClose={() => setSubmitOpen(false)} />}
    </>
  );
}
