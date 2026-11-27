import { AUTH_LOGIN_URL } from "../lib/siteConfig";

export function MaintenancePage() {
  return (
    <main className="maintenance-page">
      <div className="maintenance-card">
        <h1>We'll be back soon</h1>
        <p>Our site is temporarily under maintenance. We're working on improvements. Please check back later.</p>
        <div className="meta">
          If you are an admin, please <a href={AUTH_LOGIN_URL}>log in</a> to manage maintenance.
        </div>
      </div>
    </main>
  );
}
