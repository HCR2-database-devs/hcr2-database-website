import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <section className="about-section">
      <h2>Page not found</h2>
      <p>
        <Link to="/">Return home</Link>
      </p>
    </section>
  );
}
