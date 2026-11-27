import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { BadgeIcon } from "../components/BadgeIcon";
import { FeatureGate } from "../components/FeatureGate";
import { ProgressionSummaryCard } from "../components/ProgressionSummaryCard";
import { RequireAuth } from "../components/RequireAuth";
import { useAuthStatus } from "../hooks/useAuthStatus";
import { useCanUseFeature } from "../lib/features";
import {
  getBadgeCatalog,
  getOwnFeaturedBadges,
  getOwnProgression,
  setOwnFeaturedBadges
} from "../services/badges";
import type { BadgeCatalogItem } from "../types/api";

type Scope = "all" | "owned" | "locked";

function BadgeGridCard({ badge }: { badge: BadgeCatalogItem }) {
  return (
    <article className={`badge-card${badge.unlocked ? " badge-card--unlocked" : ""}`}>
      <BadgeIcon name={badge.unlocked ? badge.name : "?"} src={badge.icon_url} size={64} />
      <div className="badge-card__copy">
        <h3>{badge.name}</h3>
        <p className="badge-card__category">{badge.category.name}</p>
        <p className="badge-card__description">{badge.description}</p>
        {badge.progress && (
          <div className="badge-card__progress">
            <div className="badge-card__progress-track">
              <span style={{ width: `${badge.progress.percent}%` }} />
            </div>
            <small>
              {badge.progress.current} / {badge.progress.target}
            </small>
          </div>
        )}
        {badge.award_method === "manual" && !badge.unlocked && (
          <p className="badge-card__hint">Awarded by the community team</p>
        )}
      </div>
      <span className={`badge-card__rarity badge-card__rarity--${badge.rarity}`}>
        {badge.rarity}
      </span>
    </article>
  );
}

function BadgesContent() {
  const queryClient = useQueryClient();
  const { data: authStatus } = useAuthStatus();
  const canUseXp = useCanUseFeature("community_xp");
  const [scope, setScope] = useState<Scope>("all");
  const [category, setCategory] = useState("");
  const [selected, setSelected] = useState<number[]>([]);
  const [message, setMessage] = useState("");

  const catalogQuery = useQuery({
    queryKey: ["badges", "catalog", scope, category],
    queryFn: () => getBadgeCatalog({ scope, category: category || undefined })
  });
  const featuredQuery = useQuery({
    queryKey: ["badges", "featured"],
    queryFn: getOwnFeaturedBadges,
    enabled: authStatus?.logged === true
  });
  const progressionQuery = useQuery({
    queryKey: ["progression", "me"],
    queryFn: getOwnProgression,
    enabled: authStatus?.logged === true && canUseXp,
    retry: false
  });

  const featuredMutation = useMutation({
    mutationFn: setOwnFeaturedBadges,
    onSuccess: () => {
      setMessage("Featured badges updated.");
      queryClient.invalidateQueries({ queryKey: ["badges"] });
      queryClient.invalidateQueries({ queryKey: ["community", "profile"] });
    },
    onError: (error: Error) => setMessage(error.message)
  });

  const badges = catalogQuery.data?.badges ?? [];
  const categories = catalogQuery.data?.categories ?? [];
  const owned = badges.filter((badge) => badge.unlocked && badge.featureable);
  const featuredIds = featuredQuery.data?.featured.map((badge) => badge.badge_id) ?? [];

  function toggleSelected(badgeId: number) {
    setSelected((current) =>
      current.includes(badgeId)
        ? current.filter((id) => id !== badgeId)
        : current.length >= 5
          ? current
          : [...current, badgeId]
    );
  }

  return (
    <div className="page-container badges-page">
      <header className="badges-page__head">
        <div>
          <p className="eyebrow">Community collection</p>
          <h1>Badges</h1>
          <p>
            Earn recognition for records, submissions and community contributions. Badges are cosmetic
            and never change your permissions.
          </p>
        </div>
        {progressionQuery.data && <ProgressionSummaryCard progression={progressionQuery.data} />}
      </header>

      {featuredQuery.data && featuredQuery.data.featured.length > 0 && (
        <section className="badges-featured" aria-labelledby="badges-featured-heading">
          <h2 id="badges-featured-heading">Featured</h2>
          <div className="badges-featured__list">
            {featuredQuery.data.featured.map((badge) => (
              <div key={badge.id} className="badges-featured__item">
                <BadgeIcon name={badge.badge_name} src={badge.icon_path} size={48} />
                <span>{badge.badge_name}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="badges-toolbar">
        <div className="badges-tabs" role="group" aria-label="Badge scope">
          {(["all", "owned", "locked"] as Scope[]).map((item) => (
            <button
              key={item}
              type="button"
              className={`badges-tab${scope === item ? " is-active" : ""}`}
              onClick={() => setScope(item)}
            >
              {item === "all" ? "All" : item === "owned" ? "Unlocked" : "Locked"}
            </button>
          ))}
        </div>
        <label className="badges-filter">
          Category
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">All categories</option>
            {categories.map((item) => (
              <option key={item.id} value={item.identifier}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {catalogQuery.isLoading && <p className="frontend-muted">Loading badges…</p>}
      {catalogQuery.isError && <p className="frontend-error">Could not load the badge catalog.</p>}
      {!catalogQuery.isLoading && badges.length === 0 && (
        <p className="frontend-muted">No badges match this filter.</p>
      )}

      <div className="badge-grid">
        {badges.map((badge) => (
          <BadgeGridCard key={badge.id} badge={badge} />
        ))}
      </div>

      {authStatus?.logged && owned.length > 0 && (
        <section className="badges-feature-editor" aria-labelledby="badges-feature-editor-heading">
          <h2 id="badges-feature-editor-heading">Choose up to five featured badges</h2>
          <p className="frontend-muted">Featured badges appear on your public profile.</p>
          <div className="badges-feature-editor__list">
            {owned.map((badge) => {
              const initial = selected.length > 0 ? selected : featuredIds;
              const checked = initial.includes(badge.id);
              return (
                <label key={badge.id} className="badges-feature-editor__option">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleSelected(badge.id)}
                  />
                  <BadgeIcon name={badge.name} src={badge.icon_url} size={32} />
                  <span>{badge.name}</span>
                </label>
              );
            })}
          </div>
          <button
            type="button"
            className="button"
            disabled={featuredMutation.isPending}
            onClick={() => featuredMutation.mutate(selected.length > 0 ? selected : featuredIds)}
          >
            Save featured badges
          </button>
          {message && <p className="frontend-muted">{message}</p>}
        </section>
      )}

      <p className="badges-page__footer">
        Looking for your level progress? Visit <Link to="/account">your account page</Link>.
      </p>
    </div>
  );
}

export function BadgesPage() {
  return (
    <RequireAuth>
      <FeatureGate feature="community_badges">
        <BadgesContent />
      </FeatureGate>
    </RequireAuth>
  );
}
