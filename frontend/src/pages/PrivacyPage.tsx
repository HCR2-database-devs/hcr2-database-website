export function PrivacyPage() {
  return (
    <main className="standalone-page">
      <div className="policy-container">
        <h1>Privacy Policy</h1>
        <p>Effective date: 26 December 2025</p>

        <h2>Summary</h2>
        <p>
          This site collects a minimal amount of information needed to operate: anonymous usage data
          for statistics, and optional user-submitted content (records and news). We do not sell
          personal data.
        </p>

        <h2>What we collect</h2>
        <ul>
          <li>
            Public submissions: player names, map/vehicle selections and distances, and optional
            country text. These are stored in the site database for review and display.
          </li>
          <li>
            Admin authentication uses Discord OAuth; only basic Discord info is stored in the
            session for access control (Discord id and username).
          </li>
          <li>Server logs: IP addresses are recorded for rate-limiting and spam prevention of public submissions.</li>
        </ul>

        <h2>How we use your information</h2>
        <p>
          Submitted records are stored so admins can review and (if approved) publish them as world
          records. IP addresses are used only for rate-limiting and abuse prevention. Admin Discord
          IDs are used to determine administrative access.
        </p>

        <h2>Cookies and third-party services</h2>
        <p>
          We use standard session cookies to maintain authenticated admin sessions. Third-party
          services (for example, GitHub links or Discord OAuth) are used for convenience; please
          review those providers&apos; privacy policies for details.
        </p>

        <h2>Data retention</h2>
        <p>
          Public submissions and published news are retained until an admin removes them. If you want
          data removed, contact the site administrator (see contact section).
        </p>

        <h2>Security</h2>
        <p>We take reasonable measures to secure the database and server. However, no online service can guarantee absolute security.</p>

        <h2>Children</h2>
        <p>This site is not intended for children under 13. Do not submit personal information about minors.</p>

        <h2>Contact</h2>
        <p>
          If you have questions or would like data removed, contact:{" "}
          <a href="mailto:nipatsuplaying@gmail.com">nipatsuplaying@gmail.com</a>
        </p>

        <p className="policy-note">
          This policy may be updated; the effective date above indicates the latest revision.
        </p>
        <p>
          <a href="/">Back to site</a>
        </p>
      </div>
    </main>
  );
}
