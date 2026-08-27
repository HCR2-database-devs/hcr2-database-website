import { useQuery } from "@tanstack/react-query";

import { formatDate } from "../lib/legacyDisplay";
import { getChangelog } from "../services/publicData";
import { FormattedText } from "../components/FormattedText";

const CATEGORIES: { key: "added" | "changed" | "fixed"; label: string }[] = [
  { key: "added", label: "Added" },
  { key: "changed", label: "Changed" },
  { key: "fixed", label: "Fixed" }
];

export function ChangelogPage() {
  const changelog = useQuery({
    queryKey: ["changelog"],
    queryFn: () => getChangelog(200)
  });

  return (
    <main className="changelog-page">
      <section className="page-hero page-hero--compact" aria-labelledby="changelog-title">
        <p className="eyebrow">Updates</p>
        <h1 id="changelog-title">Changelog</h1>
        <p>A record of changes and improvements to the site.</p>
      </section>

      <section className="data-section">
        {changelog.isLoading && <p className="loading-state">Loading changelog…</p>}
        {changelog.isError && <p className="frontend-error">Failed to load changelog.</p>}
        {!changelog.isLoading && changelog.data?.changelog.length === 0 && (
          <p className="empty-state">No changes logged yet.</p>
        )}
        <div className="changelog-list">
          {changelog.data?.changelog.map((item) => (
            <article className="changelog-entry" key={item.id}>
              <header className="changelog-entry-header">
                <h2 className="changelog-version">v{item.version}</h2>
                {item.title && <h3 className="changelog-title">{item.title}</h3>}
              </header>
              <div className="frontend-muted">
                {formatDate(item.created_at)}
                {item.author ? ` - ${item.author}` : ""}
              </div>
              {CATEGORIES.map(({ key, label }) => {
                const bullets = item[key];
                if (bullets.length === 0) {
                  return null;
                }
                return (
                  <div className="changelog-category" key={key}>
                    <h3 className="changelog-category-title">{label}</h3>
                    <ul className="changelog-bullets">
                      {bullets.map((bullet, index) => (
                        <li key={`${key}-${index}`}>
                          <FormattedText text={bullet} />
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}