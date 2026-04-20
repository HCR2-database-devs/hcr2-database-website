import { Link, NavLink } from "react-router-dom";

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

  return (
    <header>
      <div className="device-note">Works best on laptop / PC for full functionality</div>
      <div className="header-inner">
        <Link className="branding" to="/">
          <img src="/img/hcrdatabaselogo.png" alt="Logo" id="logo" />
          <div>
            <h1>HCR2 Adventure Records (unofficial)</h1>
            <div className="frontend-subtitle">Community world records & stats</div>
          </div>
        </Link>

        <nav className="header-right" aria-label="Primary navigation">
          <div className="header-buttons" aria-hidden="false">
            {navItems.map((item) => (
              <NavLink key={item.to} to={item.to}>
                {({ isActive }) => (
                  <button type="button" data-active={isActive}>
                    {item.label}
                  </button>
                )}
              </NavLink>
            ))}

            <button type="button" disabled title="Public submission migration is pending">
              Submit Record
            </button>
            <button type="button" disabled title="News modal migration is pending">
              News
            </button>

            {!authStatus?.logged && (
              <button
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
              <button
                type="button"
                onClick={() => {
                  window.location.href = "/php/admin.php";
                }}
              >
                Admin
              </button>
            )}

            {authStatus?.logged && (
              <button
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
          {isDark ? "☀" : "☾"}
        </button>
      </div>
    </header>
  );
}
