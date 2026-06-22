import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <section className="content-section content-section--compact">
      <h1>Page not found</h1>
      <p>
        <Link className="button button--secondary" to="/">
          Return home
        </Link>
      </p>
    </section>
  );
}
