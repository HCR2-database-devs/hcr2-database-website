import { Link } from "react-router-dom";

import { REPO_URL } from "../lib/communityInfo";

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
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub
          </a>
          <a
            href="https://en.tipeee.com/hcr2-database"
            target="_blank"
            rel="noopener noreferrer"
          >
            Support
          </a>
          <Link to="/privacy" id="privacy-link">
            Privacy Policy
          </Link>
          <Link to="/terms" id="terms-link">
            Terms of Service
          </Link>
          <Link to="/changelog" id="changelog-link">
            Changelog
          </Link>
        </p>
      </div>
    </footer>
  );
}
