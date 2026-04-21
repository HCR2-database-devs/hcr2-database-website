import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer id="footer">
      <p id="copyright" style={{ textAlign: "center", marginTop: 24, fontSize: 14, color: "#777" }}>
        2026 - Adventure Records - Made by : Titanium Gaming HCR2 / Nipatsu HCR2
        <br />
        Portions of the materials used are trademarks and/or copyrighted works of Fingersoft Ltd. All rights
        reserved by Fingersoft. This material is not official and is not endorsed by Fingersoft.
      </p>
      <p className="github-meta" style={{ marginTop: 8, fontSize: 13, color: "#555" }}>
        Source code:{" "}
        <a
          id="github-link"
          href="https://github.com/Nipatsuplayer/hcr2-database-with-website"
          target="_blank"
          rel="noopener noreferrer"
        >
          GitHub
        </a>
        &nbsp;—&nbsp;Version: <span id="github-version">loading...</span>&nbsp;—&nbsp;
        <Link to="/privacy" id="privacy-link">
          Privacy Policy
        </Link>
      </p>
    </footer>
  );
}
