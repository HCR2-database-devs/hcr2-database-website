export function MaintenancePage() {
  return (
    <div className="maintenance-legacy-page">
      <div className="maintenance-card">
        <h1>We'll be back soon</h1>
        <p>Our site is temporarily under maintenance. We're working on improvements — please check back later.</p>
        <div className="meta">
          If you are an admin, please <a href="https://auth.hcr2.xyz/login">log in</a> to manage
          maintenance.
        </div>
      </div>
    </div>
  );
}
