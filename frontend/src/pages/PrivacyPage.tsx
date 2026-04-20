export function PrivacyPage() {
  return (
    <section className="about-section policy-container">
      <h2>Privacy Policy</h2>
      <p className="frontend-copy">Effective date: 26 December 2025</p>

      <h3>Summary</h3>
      <p className="frontend-copy">
        This site collects a minimal amount of information needed to operate: anonymous usage data
        for statistics, and optional user-submitted content. We do not sell personal data.
      </p>

      <h3>What we collect</h3>
      <ul className="frontend-list">
        <li>
          Public submissions: player names, map/vehicle selections, distances, and optional country
          text.
        </li>
        <li>
          Admin authentication uses Discord OAuth; only basic Discord info is used for access
          control.
        </li>
        <li>Server logs: IP addresses may be used for rate-limiting and spam prevention.</li>
      </ul>

      <h3>How we use your information</h3>
      <p className="frontend-copy">
        Submitted records are stored so admins can review and publish them. IP addresses are used
        only for rate-limiting and abuse prevention. Admin Discord IDs are used to determine
        administrative access.
      </p>

      <h3>Cookies and third-party services</h3>
      <p className="frontend-copy">
        We use standard session cookies for authenticated admin sessions. Third-party services such
        as Discord OAuth may also be used.
      </p>

      <h3>Contact</h3>
      <p className="frontend-copy">
        If you have questions or would like data removed, contact{" "}
        <a href="mailto:nipatsuplaying@gmail.com">nipatsuplaying@gmail.com</a>.
      </p>
    </section>
  );
}
