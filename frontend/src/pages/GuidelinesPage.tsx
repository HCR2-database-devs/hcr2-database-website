import { Link } from "react-router-dom";

const guidelines = [
  "Official Adventure leaderboard runs and Adventure challenge runs can be accepted.",
  "Patched glitches, pre-nerf vehicle exploits and respawn-based records are excluded for consistency.",
  "If two players reach the same distance, the first known achievement is treated as the record holder.",
  "Admins may revise or remove records when evidence changes or a rule violation is found.",
  "Records for newly released vehicles are added once the public event where the vehicle can be obtained for free begins."
];

const moderationNotes = [
  "Questionable records include runs from players with a cheating history or records with missing, unclear or insufficient proof.",
  "A questionable record can be reviewed again when better proof, a clear video or a reliable replay is provided.",
  "Blacklisted records are removed from the public record set instead of being kept as uncertain entries.",
  "TAS-assisted records are allowed when disclosed and can be marked verified when the evidence is clear."
];

export function GuidelinesPage() {
  return (
    <main className="data-page">
      <section className="page-hero page-hero--compact">
        <p className="eyebrow">Rules</p>
        <h1>Record Guidelines</h1>
        <p className="section-copy">
          Everything you need to know about what records we accept, how they're reviewed, and what happens when something doesn't quite fit.
        </p>
      </section>

      <section className="content-section content-section--split" aria-labelledby="guidelines-heading">
        <div className="section-heading">
          <h2 id="guidelines-heading">What we accept</h2>
        </div>
        <ul className="rule-list">
          {guidelines.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="content-section content-section--split" aria-labelledby="moderation-heading">
        <div className="section-heading">
          <h2 id="moderation-heading">Questionable records</h2>
        </div>
        <ul className="rule-list">
          {moderationNotes.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="content-section content-section--split" aria-labelledby="workflow-heading">
        <div className="section-heading">
          <h2 id="workflow-heading">Submitting records</h2>
        </div>
        <div className="workflow-grid">
          <div>
            <h3>Find a record</h3>
            <p>
              Check the existing records for your map and vehicle combo. If your distance beats the current record, you can submit it.
            </p>
          </div>
          <div>
            <h3>Submit your run</h3>
            <p>
              Use the submit form to send in your record with map, vehicle, distance, player name and tuning parts. You can submit through the site or via Discord bot.
            </p>
          </div>
          <div>
            <h3>We review it</h3>
            <p>
              Every submission is reviewed by an admin before it goes live. This keeps the database accurate and trustworthy. Most reviews happen quickly.
            </p>
          </div>
        </div>
      </section>

      <div className="content-section" style={{ borderTop: 0, paddingTop: 0 }}>
        <Link className="button button--secondary" to="/">
          Back to Home
        </Link>
      </div>
    </main>
  );
}
