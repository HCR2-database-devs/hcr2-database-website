import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer id="footer" className="site-footer">
      <div className="footer-inner">
        <p id="copyright">
          2026 - Adventure Records - Made by Titanium Gaming HCR2 / Nipatsu HCR2.
          <br />
          Hill Climb Racing 2 materials are trademarks and/or copyrighted works of Fingersoft Ltd.
          This unofficial community site is not endorsed by Fingersoft.
        </p>
        <p className="github-meta">
          <a
            id="github-link"
            href="https://github.com/HCR2-database-devs/hcr2-database-website"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub
          </a>
          <span>Version: </span>
          <span id="github-version">loading...</span>
          <Link to="/privacy" id="privacy-link">
            Privacy Policy
          </Link>
        </p>
      </div>
    </footer>
  );
}
