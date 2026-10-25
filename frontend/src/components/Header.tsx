import { useEffect, useRef, useState } from "react";
import type { KeyboardEvent as ReactKeyboardEvent } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";

import { NewsModal } from "./NewsModal";
import { NotificationBell } from "./NotificationBell";
import { PublicSubmitModal } from "./PublicSubmitModal";
import { UserAvatar } from "./UserAvatar";
import { BetaBadge } from "./BetaBadge";
import { discordAvatarUrl } from "../services/community";
import { useAuthStatus } from "../hooks/useAuthStatus";
import { useDarkMode } from "../hooks/useDarkMode";
import { useCanUseFeature } from "../lib/features";

type NavItem = {
  label: string;
  to: string;
  feature?: "community_members";
};

type DropdownId = "browse" | "records" | "account";

const browseNavItems: NavItem[] = [
  { label: "Maps", to: "/maps" },
  { label: "Vehicles", to: "/vehicles" },
  { label: "Players", to: "/players" },
  { label: "Tuning", to: "/tuning-parts" }
];

const primaryNavItems: NavItem[] = [
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
  const [openDropdown, setOpenDropdown] = useState<DropdownId | null>(null);
  const mobileMenuButtonRef = useRef<HTMLButtonElement>(null);
  const mobileMenuRef = useRef<HTMLElement>(null);
  const browseRef = useRef<HTMLDivElement>(null);
  const recordsRef = useRef<HTMLDivElement>(null);
  const accountRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const closeTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const isBrowseActive = browseNavItems.some(
    (item) => location.pathname === item.to || location.pathname.startsWith(`${item.to}/`)
  );
  const isRecordsActive = location.pathname === "/records" || location.pathname.startsWith("/records");

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      const target = e.target as Node;
      const isInsideDropdown = [browseRef, recordsRef, accountRef].some((ref) =>
        ref.current?.contains(target)
      );
      if (!isInsideDropdown) {
        setOpenDropdown(null);
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
      setOpenDropdown(null);
    }

    document.addEventListener("mousedown", handleOutsideMobileMenu);
    document.addEventListener("touchstart", handleOutsideMobileMenu);
    return () => {
      document.removeEventListener("mousedown", handleOutsideMobileMenu);
      document.removeEventListener("touchstart", handleOutsideMobileMenu);
    };
  }, [isMenuOpen]);

  function handleDropdownEnter(id: DropdownId) {
    if (!canUseHover()) return;
    if (closeTimer.current) clearTimeout(closeTimer.current);
    setOpenDropdown(id);
  }

  function handleDropdownLeave() {
    if (!canUseHover()) return;
    if (closeTimer.current) clearTimeout(closeTimer.current);
    closeTimer.current = setTimeout(() => setOpenDropdown(null), 200);
  }

  function toggleDropdown(id: DropdownId) {
    setOpenDropdown((current) => (current === id ? null : id));
  }

  function handleDropdownKeyDown(event: ReactKeyboardEvent, id: DropdownId) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggleDropdown(id);
    } else if (event.key === "Escape") {
      setOpenDropdown(null);
    }
  }

  function closeMenus() {
    setMenuOpen(false);
    setOpenDropdown(null);
  }

  function handleLogout() {
    window.location.href = "/auth/logout.php";
  }

  function renderNavLink(item: NavItem, mobileOnly = false) {
    if (item.feature === "community_members" && !canUseCommunity) {
      return null;
    }
    return (
      <NavLink
        key={item.to}
        to={item.to}
        className={({ isActive }) =>
          `${navClassName({ isActive })}${mobileOnly ? " header-mobile-only" : ""}`
        }
        onClick={closeMenus}
      >
        {item.label}
        {item.feature === "community_members" && (
          <BetaBadge feature="community_members" className="nav-beta-badge" />
        )}
      </NavLink>
    );
  }

  const displayName =
    authStatus?.community?.username ??
    authStatus?.community?.discord_username ??
    authStatus?.username ??
    authStatus?.id ??
    null;
  const avatarUrl = discordAvatarUrl(
    authStatus?.avatar ?? authStatus?.community?.discord_avatar,
    authStatus?.id
  );

  return (
    <>
      <header className="site-header">
        <div className="header-inner">
          <Link className="branding" to="/" onClick={closeMenus} aria-label="HCR2 Adventure Records home">
            <img
              src="/img/hcrdatabaselogo-96.webp"
              alt="HCR2 Adventure Records"
              id="logo"
              width={48}
              height={48}
              decoding="async"
              onError={(event) => {
                if (!event.currentTarget.src.endsWith(".png")) {
                  event.currentTarget.src = "/img/hcrdatabaselogo-96.png";
                }
              }}
            />
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
            onClick={() => {
              setMenuOpen((open) => !open);
              setOpenDropdown(null);
            }}
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
              <div
                className="nav-dropdown-wrapper header-desktop-only"
                ref={browseRef}
                onMouseEnter={() => handleDropdownEnter("browse")}
                onMouseLeave={handleDropdownLeave}
              >
                <span
                  className={`nav-link nav-dropdown-toggle${isBrowseActive ? " is-active" : ""}${
                    openDropdown === "browse" ? " is-open" : ""
                  }`}
                  role="button"
                  tabIndex={0}
                  aria-expanded={openDropdown === "browse"}
                  aria-controls="browse-nav-menu"
                  onClick={() => toggleDropdown("browse")}
                  onMouseEnter={() => handleDropdownEnter("browse")}
                  onKeyDown={(event) => handleDropdownKeyDown(event, "browse")}
                >
                  Browse
                </span>
                <div
                  id="browse-nav-menu"
                  className={`nav-dropdown-menu${openDropdown === "browse" ? " is-open" : ""}`}
                  onMouseEnter={() => handleDropdownEnter("browse")}
                  onMouseLeave={handleDropdownLeave}
                >
                  {browseNavItems.map((item) => (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      className={navClassName}
                      onClick={closeMenus}
                    >
                      {item.label}
                    </NavLink>
                  ))}
                </div>
              </div>

              {browseNavItems.map((item) => renderNavLink(item, true))}

              <div
                className="nav-dropdown-wrapper"
                ref={recordsRef}
                onMouseEnter={() => handleDropdownEnter("records")}
                onMouseLeave={handleDropdownLeave}
              >
                <span
                  className={`nav-link nav-dropdown-toggle${isRecordsActive ? " is-active" : ""}${
                    openDropdown === "records" ? " is-open" : ""
                  }`}
                  role="button"
                  tabIndex={0}
                  aria-expanded={openDropdown === "records"}
                  aria-controls="records-nav-menu"
                  onClick={() => toggleDropdown("records")}
                  onMouseEnter={() => handleDropdownEnter("records")}
                  onKeyDown={(event) => handleDropdownKeyDown(event, "records")}
                >
                  Records
                </span>
                <div
                  id="records-nav-menu"
                  className={`nav-dropdown-menu${openDropdown === "records" ? " is-open" : ""}`}
                  onMouseEnter={() => handleDropdownEnter("records")}
                  onMouseLeave={handleDropdownLeave}
                >
                  <NavLink to="/records" end className={navClassName} onClick={closeMenus}>
                    Normal
                  </NavLink>
                  <NavLink to="/records/mythic" className={navClassName} onClick={closeMenus}>
                    Mythic
                  </NavLink>
                </div>
              </div>

              {primaryNavItems.map((item) => renderNavLink(item))}
            </div>

            <div className="header-actions">
              <button
                className="nav-action nav-action--primary"
                type="button"
                onClick={() => {
                  closeMenus();
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
                    closeMenus();
                    setNewsOpen(true);
                  }}
                >
                  News
                </button>
                <span className="news-indicator" style={{ display: "none" }} />
              </span>

              <span className="header-action-divider" aria-hidden="true" />

              {!authStatus?.logged && (
                <button
                  id="login-btn"
                  type="button"
                  className="nav-action discord-btn"
                  onClick={() => {
                    window.location.href = "https://auth.hcr2.xyz/login";
                  }}
                >
                  <img className="discord-logo" src="/img/Discord-Symbol-Blurple.png" alt="" width={18} height={14} loading="lazy" decoding="async" />
                  <span>Discord</span>
                </button>
              )}

              {authStatus?.logged && <NotificationBell />}

              {authStatus?.logged && (
                <div
                  className="nav-dropdown-wrapper account-menu-wrapper header-desktop-only"
                  ref={accountRef}
                >
                  <button
                    id="account-menu-btn"
                    type="button"
                    className={`nav-action account-chip nav-dropdown-toggle${
                      openDropdown === "account" ? " is-open" : ""
                    }`}
                    aria-label="Account menu"
                    aria-haspopup="menu"
                    aria-expanded={openDropdown === "account"}
                    aria-controls="account-nav-menu"
                    onClick={() => toggleDropdown("account")}
                    onKeyDown={(event) => handleDropdownKeyDown(event, "account")}
                  >
                    <UserAvatar avatarUrl={avatarUrl} name={displayName} size={20} />
                    <span>{displayName}</span>
                  </button>
                  <div
                    id="account-nav-menu"
                    className={`nav-dropdown-menu nav-dropdown-menu--right${
                      openDropdown === "account" ? " is-open" : ""
                    }`}
                    role="menu"
                    aria-label="Account"
                  >
                    <Link to="/account" className="nav-action" role="menuitem" onClick={closeMenus}>
                      My account
                    </Link>
                    {authStatus?.allowed && (
                      <NavLink to="/admin" className={navClassName} role="menuitem" onClick={closeMenus}>
                        Admin
                      </NavLink>
                    )}
                    <button type="button" className="nav-action" role="menuitem" onClick={handleLogout}>
                      Logout
                    </button>
                  </div>
                </div>
              )}

              {authStatus?.logged && (
                <Link
                  id="account-btn"
                  to="/account"
                  className="nav-action account-chip header-mobile-only"
                  onClick={closeMenus}
                >
                  <UserAvatar avatarUrl={avatarUrl} name={displayName} size={20} />
                  <span>{displayName}</span>
                </Link>
              )}

              {authStatus?.allowed && (
                <NavLink
                  id="admin-btn"
                  to="/admin"
                  className="nav-action header-mobile-only"
                  onClick={closeMenus}
                >
                  Admin
                </NavLink>
              )}

              {authStatus?.logged && (
                <button
                  id="logout-btn"
                  className="nav-action header-mobile-only"
                  type="button"
                  onClick={handleLogout}
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
