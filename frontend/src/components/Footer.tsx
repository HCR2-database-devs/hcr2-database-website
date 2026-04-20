import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer>
      <p>Unofficial Hill Climb Racing 2 adventure records website.</p>
      <p>
        <Link to="/privacy">Privacy</Link>
      </p>
    </footer>
  );
}
