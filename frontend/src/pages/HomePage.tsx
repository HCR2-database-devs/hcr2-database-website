export function HomePage() {
  return (
    <section className="about-section" id="about-section">
      <img
        src="/img/image copy.png"
        alt="Info Icon"
        className="frontend-about-image"
      />

      <h2>About this website</h2>
      <p className="frontend-copy">
        Welcome to the unofficial Hill Climb Racing 2 Adventure Records page! Here, players from
        around the world can view the best distance records achieved in various maps using different
        vehicles. Our goal is to create a comprehensive leaderboard that showcases the skills and
        achievements of the HCR2 community, which includes every record from leaderboards as well as
        challenge runs.
      </p>

      <h2>Record Guidelines</h2>
      <ul className="frontend-list">
        <li>
          We will be including records from the official Adventure leaderboards, but runs from
          Adventure challenges will also be accepted.
        </li>
        <li>
          No records using patched glitches or vehicles before nerfs will be added here, for the sake
          of consistency.
        </li>
        <li>No records using respawns will be added, as they offer an unfair advantage.</li>
        <li>
          In case of a tie, the first player to achieve the record distance will be considered the
          World Record Holder.
        </li>
        <li>
          Admins will review all submissions and may remove records if they are found to be invalid
          or in violation of these rules.
        </li>
      </ul>

      <h2>Viewing Records</h2>
      <p className="frontend-copy">
        To view records, open the Get Records section. The records are displayed in a table format,
        showing the map name, vehicle name, player name and achieved distance. Use the filters,
        sorting controls and CSV export to narrow the record list.
      </p>
    </section>
  );
}
