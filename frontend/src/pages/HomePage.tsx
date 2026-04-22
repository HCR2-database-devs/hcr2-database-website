import { Link } from "react-router-dom";

const principles = [
  {
    title: "Verified records",
    text: "World records are reviewed before publication, with questionable runs clearly separated from standard records."
  },
  {
    title: "Canonical data",
    text: "Maps, vehicles, players, tuning parts and setups are presented from the same PostgreSQL-backed public API."
  },
  {
    title: "Community submissions",
    text: "Players can submit runs for admin review without changing the public leaderboard until a decision is made."
  }
];

const guidelines = [
  "Official Adventure leaderboard runs and Adventure challenge runs can be accepted.",
  "Patched glitches, pre-nerf vehicle exploits and respawn-based records are excluded for consistency.",
  "If two players reach the same distance, the first known achievement is treated as the record holder.",
  "Admins may revise or remove records when evidence changes or a rule violation is found."
];

export function HomePage() {
  return (
    <main className="home-page">
      <section className="home-hero" aria-labelledby="home-title">
        <div className="home-hero__copy">
          <p className="eyebrow">Unofficial HCR2 adventure database</p>
          <h1 id="home-title">Community world records, cleaned up and easy to verify.</h1>
          <p className="hero-copy">
            Explore the best Hill Climb Racing 2 adventure distances by map, vehicle, player and
            tuning setup. The site keeps the public experience focused on trusted records while
            preserving transparent context for uncertain runs.
          </p>
          <div className="hero-actions">
            <Link className="button button--primary" to="/records">
              Browse Records
            </Link>
            <Link className="button button--secondary" to="/stats">
              View Stats
            </Link>
          </div>
        </div>
        <div className="home-hero__asset" aria-hidden="true">
          <img src="/img/hcrdatabaselogo.png" alt="" />
        </div>
      </section>

      <section className="content-section" id="about-section" aria-labelledby="about-title">
        <div className="section-heading">
          <p className="eyebrow">Purpose</p>
          <h2 id="about-title">About this website</h2>
        </div>
        <p id="about-text" className="section-copy">
          This website is a focused, unofficial reference for Hill Climb Racing 2 Adventure records.
          It brings together leaderboard records, challenge runs, player context and tuning data so
          the community can compare results without searching across disconnected sources.
        </p>
        <div className="feature-grid">
          {principles.map((item) => (
            <article className="feature-card" key={item.title}>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="content-section content-section--split" aria-labelledby="guidelines-title">
        <div className="section-heading">
          <p className="eyebrow">Rules</p>
          <h2 id="guidelines-title">Record Guidelines</h2>
        </div>
        <ul id="rules-text" className="rule-list">
          {guidelines.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="content-section content-section--split" aria-labelledby="workflow-title">
        <div className="section-heading">
          <p className="eyebrow">Workflow</p>
          <h2 id="workflow-title">Viewing and submitting records</h2>
        </div>
        <div className="workflow-grid">
          <div>
            <h3>Explore</h3>
            <p id="viewing-text">
              Use the records page to search by player, map or vehicle, filter by distance and
              status, then sort the result set for faster comparison.
            </p>
          </div>
          <div>
            <h3>Submit</h3>
            <p id="viewing-text-2">
              Submit a record with map, vehicle, distance, player and tuning parts. It remains
              pending until an admin approves it for publication.
            </p>
          </div>
          <div>
            <h3>Analyze</h3>
            <p id="stats-text">
              The statistics page aggregates records by vehicle, map, player, country and tuning
              setup so trends are easier to inspect.
            </p>
          </div>
        </div>
      </section>

      <section className="content-section content-section--compact" aria-labelledby="updates-title">
        <div className="section-heading">
          <p className="eyebrow">Updates</p>
          <h2 id="updates-title">News and community links</h2>
        </div>
        <p id="news-text" className="section-copy">
          Admin news covers site changes, database updates and moderation notes. Community channels:
          <a rel="noopener noreferrer" href="https://www.youtube.com/@titaniumhcr2" target="_blank">
            Titanium Gaming HCR2
          </a>
          <span aria-hidden="true"> / </span>
          <a rel="noopener noreferrer" href="https://www.youtube.com/@nipatsu" target="_blank">
            Nipatsu HCR2
          </a>
        </p>
      </section>
    </main>
  );
}
