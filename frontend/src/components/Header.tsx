import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";

import { NewsModal } from "./NewsModal";
import { NotificationBell } from "./NotificationBell";
import { PublicSubmitModal } from "./PublicSubmitModal";
import { UserAvatar } from "./UserAvatar";
import { BetaBadge } from "./BetaBadge";
import { useAuthStatus } from "../hooks/useAuthStatus";
import { useDarkMode } from "../hooks/useDarkMode";
import { useCanUseFeature } from "../lib/features";

type NavItem = {
  label: string;
  to: string;
  feature?: "community_members";
};

const navItems: NavItem[] = [
  { label: "Maps", to: "/maps" },
  { label: "Vehicles", to: "/vehicles" },
  { label: "Players", to: "/players" },
  { label: "Tuning", to: "/tuning-parts" },
  { label: "Community", to: "/community", feature: "community_members" },
  { label: "Stats", to: "/stats" }
];

function navClassName({ isActive }: { isActive: boolean }) {
  return `nav-link${isActive ? " is-active" : ""}`;
}

function canUseHover() {
  return window.matchMedia("(hover: hover) and (pointer: fine)").matches;
}

export function Header() {
  const { data: authStatus } = useAuthStatus();
  const { isDark, toggleDarkMode } = useDarkMode();
  const canUseCommunity = useCanUseFeature("community_members");
  const [isMenuOpen, setMenuOpen] = useState(false);
  const [isNewsOpen, setNewsOpen] = useState(false);
  const [isSubmitOpen, setSubmitOpen] = useState(false);
  const [isRecordsOpen, setRecordsOpen] = useState(false);
  const mobileMenuButtonRef = useRef<HTMLButtonElement>(null);
  const mobileMenuRef = useRef<HTMLElement>(null);
  const recordsRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const closeTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

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

  useEffect(() => {
    if (!isMenuOpen) return;

    function handleOutsideMobileMenu(e: MouseEvent | TouchEvent) {
      const target = e.target as Node;
      if (mobileMenuRef.current?.contains(target) || mobileMenuButtonRef.current?.contains(target)) {
        return;
      }
      setMenuOpen(false);
      setRecordsOpen(false);
    }

    document.addEventListener("mousedown", handleOutsideMobileMenu);
    document.addEventListener("touchstart", handleOutsideMobileMenu);
    return () => {
      document.removeEventListener("mousedown", handleOutsideMobileMenu);
      document.removeEventListener("touchstart", handleOutsideMobileMenu);
    };
  }, [isMenuOpen]);

  function handleRecordsEnter() {
    if (!canUseHover()) return;
    if (closeTimer.current) clearTimeout(closeTimer.current);
    setRecordsOpen(true);
  }

  function handleRecordsLeave() {
    if (!canUseHover()) return;
    if (closeTimer.current) clearTimeout(closeTimer.current);
    closeTimer.current = setTimeout(() => setRecordsOpen(false), 200);
  }

  function closeMobileMenu() {
    setMenuOpen(false);
    setRecordsOpen(false);
  }

  const displayName =
    authStatus?.community?.username ??
    authStatus?.community?.discord_username ??
    authStatus?.username ??
    authStatus?.id ??
    null;
  const avatarUrl = authStatus?.avatar ?? authStatus?.community?.discord_avatar ?? null;

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
            ref={mobileMenuButtonRef}
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
            ref={mobileMenuRef}
            id="mobile-menu"
            className={`header-nav${isMenuOpen ? " is-open" : ""}`}
            aria-label="Primary navigation"
          >
            <div className="nav-links">
              {navItems.map((item) => {
                if (item.feature === "community_members" && !canUseCommunity) {
                  return null;
                }
                return (
                  <NavLink key={item.to} to={item.to} className={navClassName} onClick={closeMobileMenu}>
                    {item.label}
                    {item.feature === "community_members" && (
                      <BetaBadge feature="community_members" className="nav-beta-badge" />
                    )}
                  </NavLink>
                );
              })}
              <div
                className="nav-dropdown-wrapper"
                ref={recordsRef}
                onMouseEnter={handleRecordsEnter}
                onMouseLeave={handleRecordsLeave}
              >
                <span
                  className={`nav-link nav-dropdown-toggle${isRecordsActive ? " is-active" : ""}${
                    isRecordsOpen ? " is-open" : ""
                  }`}
                  role="button"
                  tabIndex={0}
                  aria-expanded={isRecordsOpen}
                  aria-controls="records-nav-menu"
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
                  id="records-nav-menu"
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

              {authStatus?.logged && (
                <NotificationBell />
              )}

              {authStatus?.logged && (
                <Link
                  id="account-btn"
                  to="/account"
                  className="nav-action account-chip"
                  onClick={closeMobileMenu}
                >
                  <UserAvatar avatarUrl={avatarUrl} name={displayName} size={20} />
                  <span>{displayName}</span>
                </Link>
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
          </nav>
        </div>

        <div id="auth-warning" />
      </header>
      {isNewsOpen && <NewsModal onClose={() => setNewsOpen(false)} />}
      {isSubmitOpen && <PublicSubmitModal onClose={() => setSubmitOpen(false)} />}
    </>
  );
}
