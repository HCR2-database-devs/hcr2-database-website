export function HomePage() {
  return (
    <>
      <div id="stats-container"></div>
      <div id="data-container"></div>

      <div className="about-section" id="about-section">
        <img
          src="/img/image copy.png"
          alt="Info Icon"
          style={{ height: 200, verticalAlign: "middle", marginBottom: 10 }}
        />

        <h2>About this website ℹ️</h2>
        <p id="about-text" style={{ maxWidth: 800, margin: "0 auto", fontSize: 16, lineHeight: 1.5 }}>
          Welcome to the unofficial Hill Climb Racing 2 Adventure Records page ! Here, players from
          around the world can view the best distance records achieved in various maps using different
          vehicles. Our goal is to create a comprehensive leaderboard that showcases the skills and
          achievements of the HCR2 community, which includes every record from leaderboards as well as
          challenge runs.
        </p>

        <h2>Record Guidelines 📝</h2>
        <div id="rules-text">
          <ul
            style={{
              fontSize: 16,
              lineHeight: 1.5,
              listStyleType: "disc",
              margin: "0 auto",
              maxWidth: 800,
              paddingLeft: 20
            }}
          >
            <li>
              We will be including records from the official Adventure leaderboards, but runs from
              Adventure challenges will also be accepted.
            </li>
            <li>
              No records using patched glitches or vehicles before nerfs (eg : Eco-Thrust Bug
              Moonlander, Pre-nerf Minibus) will be added here, for the sake of consistency.
            </li>
            <li>Obviously, no records using respawns will be added, as they offer an unfair advantage.</li>
            <li>
              In case of a tie, the first player to achieve the record distance will be considered the
              World Record Holder.
            </li>
            <li>
              Admins will review all submissions and may remove records if they are found to be invalid
              or in violation of these rules.
            </li>
          </ul>
        </div>

        <h2>Viewing Records 🏆</h2>
        <p id="viewing-text" style={{ maxWidth: 800, margin: "0 auto", fontSize: 16, lineHeight: 1.5 }}>
          To view records, go to the "Get Records" section. The records will be displayed in a table
          format, showing the map name, vehicle name, player name, and the distance achieved. Select a
          map / vehicle of your choice from the checkboxes to filter the records by map and / or
          vehicle, enter a specific distance value to filter records that are lower or higher than the
          specified value, or type in a specific player name to search for their records. You can also
          sort the records by distance to see the highest or lowest records first.
        </p>
        <p style={{ maxWidth: 800, margin: "0 auto", fontSize: 14, lineHeight: 1.5, color: "#666" }}>
          <strong>❓ Questionable Records:</strong> A question mark (❓) next to a record indicates that
          it was trained using TAS (Tool-Assisted Speedrun) techniques or that its legitimacy is
          uncertain. These records are included for reference but may be distinguished from standard
          records. You can filter to view only questionable records using the "Show only Questionable ❓"
          checkbox in the filter options.
        </p>

        <h2>Submitting Records ✍️</h2>
        <p id="viewing-text-2" style={{ maxWidth: 800, margin: "0 auto", fontSize: 16, lineHeight: 1.5 }}>
          To submit a record, click on the "Submit Record" button. Fill out the form with the required
          information, including the map name, vehicle name, distance achieved, player name, and country
          (optional). Once you submit the form, the record will be sent for admin review. If approved, it
          will be added to the database and displayed in the records section.
        </p>

        <h2>Statistics 📊</h2>
        <p id="stats-text" style={{ maxWidth: 800, margin: "0 auto", fontSize: 16, lineHeight: 1.5 }}>
          Our stats section provides detailed insights into the performance of vehicles, maps, and players
          in the HCR2 community. You can explore various statistics such as the number of records held by
          top players, the vehicles with the highest total distance, and the distribution of records across
          different maps.
        </p>

        <h2>News & Updates 📰</h2>
        <p id="news-text" style={{ maxWidth: 800, margin: "0 auto", fontSize: 16, lineHeight: 1.5 }}>
          Stay informed about the latest news and updates related to this website. Our news section
          provides information on recent updates, changes to the database, and other relevant announcements.
        </p>

        <h2>Follow Us 📢</h2>
        <div id="follow-text" style={{ maxWidth: 800, margin: "0 auto", fontSize: 16, lineHeight: 1.5 }}>
          <ul>
            <li className="social-link">
              <a rel="noopener noreferrer" href="https://www.youtube.com/@titaniumhcr2" target="_blank">
                Titanium Gaming HCR2
              </a>
            </li>
            <li className="social-link">
              <a rel="noopener noreferrer" href="https://www.youtube.com/@nipatsu" target="_blank">
                Nipatsu HCR2
              </a>
            </li>
          </ul>
        </div>
      </div>
    </>
  );
}
