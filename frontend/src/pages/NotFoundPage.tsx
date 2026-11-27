import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <section className="content-section content-section--compact">
      <h1>Page not found</h1>
      <p>That page does not exist or has moved. Try one of these instead:</p>
      <ul>
        <li><Link to="/records">World records</Link></li>
        <li><Link to="/maps">Maps</Link></li>
        <li><Link to="/stats">Statistics</Link></li>
        <li><Link to="/community">Community</Link></li>
      </ul>
      <p>
        <Link className="button button--secondary" to="/">
          Return home
        </Link>
      </p>
    </section>
  );
}
