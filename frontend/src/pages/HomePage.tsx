import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { AdSlot } from "../components/AdSlot";
import { BetaBadge } from "../components/BetaBadge";
import { DonatorBanner } from "../components/DonatorBanner";
import { useFeatureAccess } from "../lib/features";
import { asText, formatDistance, iconSlug, TuningPartsIcons } from "../lib/legacyDisplay";
import { getHomeSummary } from "../services/publicData";
import type { DataRow } from "../types/api";

const staff = [
  { name: "Nipatsu", role: "Owner", group: "owner" },
  { name: "Titanium", role: "Owner", group: "owner" },
  { name: "Danioduck", role: "Admin", group: "admin" },
  { name: "Noya", role: "Developer", group: "developer" },
  { name: "Adam", role: "Bot developer", group: "developer" },
  { name: "Psyduck", role: "Developer", group: "developer" },
  { name: "Eleco", role: "Developer", group: "developer" },
  { name: "Blackwing", role: "Developer", group: "developer" },
];

const partners = [
  {
    icon: "\u{1F916}",
    name: "Adam's HCR2 Bot",
    subtitle: "Discord integration and HCR2 database tools",
    invite: "https://discord.gg/PPEEg7BnNS",
  },
  {
    icon: "\u2694\uFE0F",
    name: "Adventure Lovers",
    subtitle: "The biggest HCR2 adventure community",
    invite: "https://discord.gg/mPEYwGsEEC",
  },
];

function AnimatedNumber({ value }: { value: number }) {
  const [display, setDisplay] = useState(0);
  const reducedMotion = useRef(
    typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );

  useEffect(() => {
    if (reducedMotion.current || !Number.isFinite(value)) {
      setDisplay(value);
      return;
    }
    let frame = 0;
    const start = performance.now();
    const duration = 900;
    const tick = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(eased * value));
      if (progress < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value]);

  return <>{display.toLocaleString()}</>;
}

function FeaturedRecordStatus({ row }: { row: DataRow }) {
  if (String(row.questionable) === "1") {
    return (
      <span
        className="status-pill status-pill--questionable"
        title={asText(row.questionable_reason) || "Questionable: unverified run"}
      >
        Questionable
      </span>
    );
  }
  if (row.isMythic === true) {
    return (
      <span className="status-pill status-pill--mythic" title="Mythic record (Echo or Amplifier part)">
        Mythic
      </span>
    );
  }
  return <span className="status-pill status-pill--verified">Verified</span>;
}

function LiveStatsSection() {
  const summaryQuery = useQuery({
    queryKey: ["home-summary"],
    queryFn: () => getHomeSummary(8),
  });

  const reducedMotion = useRef(
    typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  const [featuredIndex, setFeaturedIndex] = useState(0);
  const lastCycleRef = useRef(-1);

  const summary = summaryQuery.data;
  const randomRecords = summary?.random_records ?? [];

  useEffect(() => {
    if (reducedMotion.current || randomRecords.length <= 1) return;
    const interval = window.setInterval(() => {
      setFeaturedIndex((prev) => prev + 1);
    }, 12000);
    return () => window.clearInterval(interval);
  }, [reducedMotion.current, randomRecords.length]);

  useEffect(() => {
    if (reducedMotion.current || randomRecords.length === 0) return;
    if (featuredIndex < randomRecords.length) return;
    const cycle = Math.floor(featuredIndex / randomRecords.length);
    if (cycle <= lastCycleRef.current) return;
    lastCycleRef.current = cycle;
    summaryQuery.refetch();
  }, [featuredIndex, randomRecords.length, summaryQuery]);

  const featured =
    randomRecords.length > 0
      ? randomRecords[featuredIndex % randomRecords.length]
      : undefined;

  const tiles = [
    { label: "Records", value: summary?.records ?? 0 },
    { label: "Players", value: summary?.players ?? 0 },
    { label: "Vehicles", value: summary?.vehicles ?? 0 },
    { label: "Maps", value: summary?.maps ?? 0 },
  ];

  return (
    <section className="content-section" aria-labelledby="live-heading">
      <div className="section-heading">
        <p className="eyebrow">Live data</p>
        <h2 id="live-heading">Straight from the database</h2>
      </div>
      <div className="live-stats-layout">
        <div className="live-stats-grid">
          {tiles.map((tile) => (
            <div className="live-stat-tile" key={tile.label}>
              <strong>
                <AnimatedNumber value={tile.value} />
              </strong>
              <span>{tile.label}</span>
            </div>
          ))}
          <Link className="live-stats-link" to="/stats">
            Full stats →
          </Link>
        </div>

        {featured && (
          <article key={featuredIndex} className="featured-record featured-record--swap">
            <div className="featured-record__head">
              <p className="featured-record__eyebrow">Random world record</p>
              <FeaturedRecordStatus row={featured} />
            </div>
            <div className="featured-record__main">
              <img
                className="featured-record__vehicle"
                src={`/img/vehicle_icons/${iconSlug(featured.vehicle_name)}.svg`}
                alt=""
                onError={(event) => {
                  event.currentTarget.style.display = "none";
                }}
              />
              <div className="featured-record__distance">
                <strong>{formatDistance(featured.distance)}</strong>
                <span>meters</span>
              </div>
            </div>
            <div className="featured-record__meta">
              <span className="map-cell">
                <img
                  className="map-icon"
                  src={`/img/map_icons/${iconSlug(featured.map_name)}.svg`}
                  alt=""
                  onError={(event) => {
                    event.currentTarget.style.display = "none";
                  }}
                />
                {asText(featured.map_name)}
              </span>
              <span className="featured-record__player">{asText(featured.player_name)}</span>
            </div>
            <div className="featured-record__tuning">
              <TuningPartsIcons parts={featured.tuning_parts} />
              {asText(featured.echoAffectedPart) && (
                <span className="echo-affected-badge">
                  Echo → {asText(featured.echoAffectedPart)}
                </span>
              )}
            </div>
            <Link className="featured-record__link" to="/records">
              Browse all records →
            </Link>
          </article>
        )}
      </div>
    </section>
  );
}

function CommunityHighlight() {
  const { canUse, isLoading } = useFeatureAccess("community_members");

  if (isLoading) return null;

  return (
    <section className="content-section" aria-labelledby="community-heading">
      <div className="community-highlight__card">
        <div className="community-highlight__copy">
          <p className="eyebrow">
            Community <BetaBadge feature="community_members" />
          </p>
          <h2 id="community-heading">More than just records</h2>
          <p>
            We're building a proper HCR2 community here. Create your own
            profile, find other players, and connect through Discord.
          </p>
        </div>
        <div className="community-highlight__action">
          {canUse ? (
            <Link className="button button--primary" to="/community">
              Explore Community
            </Link>
          ) : (
            <span className="button button--secondary community-highlight__coming-soon">
              Coming Soon
            </span>
          )}
        </div>
      </div>
    </section>
  );
}

function BrowseSection() {
  return (
    <section className="content-section" aria-labelledby="browse-heading">
      <div className="section-heading">
        <p className="eyebrow">Database</p>
        <h2 id="browse-heading">Browse the world records</h2>
      </div>
      <div className="browse-grid">
        <Link to="/maps" className="browse-card feature-card">
          <img src="/img/map_icons/countryside.svg" alt="" className="browse-card__icon" />
          <h3 className="browse-card__title">Maps</h3>
          <p className="browse-card__desc">All adventure maps and their records</p>
        </Link>
        <Link to="/vehicles" className="browse-card feature-card">
          <img src="/img/vehicle_icons/hill_climber.svg" alt="" className="browse-card__icon" />
          <h3 className="browse-card__title">Vehicles</h3>
          <p className="browse-card__desc">Browse records by vehicle</p>
        </Link>
        <Link to="/players" className="browse-card feature-card">
          <div className="browse-card__text-icon" aria-hidden="true">P</div>
          <h3 className="browse-card__title">Players</h3>
          <p className="browse-card__desc">See who holds the most records</p>
        </Link>
        <Link to="/tuning-parts" className="browse-card feature-card">
          <img src="/img/tuning_parts_icons/nitro.svg" alt="" className="browse-card__icon" />
          <h3 className="browse-card__title">Tuning</h3>
          <p className="browse-card__desc">Setups and tuning part usage</p>
        </Link>
      </div>
    </section>
  );
}

function WhySection() {
  return (
    <section className="content-section" aria-labelledby="why-heading">
      <div className="section-heading">
        <p className="eyebrow">Why hcr2.xyz?</p>
        <h2 id="why-heading">Built for the community</h2>
      </div>
      <div className="feature-grid">
        <article className="feature-card">
          <h3>Verified world records</h3>
          <p>
            Every world record is reviewed by our team before it goes live.
            Questionable runs are clearly marked so you always know what you're looking at.
          </p>
        </article>
        <article className="feature-card">
          <h3>Easy to search</h3>
          <p>
            Filter by map, vehicle, player, or tuning setup. Find the exact record you're looking for without digging through spreadsheets or in-game leaderboards.
          </p>
        </article>
        <article className="feature-card">
          <h3>Community built</h3>
          <p>
            Made by HCR2 players, for HCR2 players. Anyone can submit world record runs for review. No account required.
          </p>
        </article>
      </div>
    </section>
  );
}

function HowItWorksSection() {
  return (
    <section className="content-section content-section--split" aria-labelledby="how-heading">
      <div className="section-heading">
        <p className="eyebrow">How it works</p>
        <h2 id="how-heading">Three steps</h2>
      </div>
      <div className="how-grid">
        <div className="how-step">
          <span className="how-step__number">1</span>
          <div>
            <h3>Explore</h3>
            <p>Browse records by map, vehicle, or player. Use the stats page to see the bigger picture.</p>
          </div>
        </div>
        <div className="how-step">
          <span className="how-step__number">2</span>
          <div>
            <h3>Submit</h3>
            <p>Got a world record run? Submit your adventure distance for our team to review.</p>
          </div>
        </div>
        <div className="how-step">
          <span className="how-step__number">3</span>
          <div>
            <h3>Verify</h3>
            <p>Our team reviews every submission. Approved records go live in the database.</p>
          </div>
        </div>
      </div>
    </section>
  );
}

function CommunityVisionSection() {
  return (
    <section className="content-section content-section--compact" aria-labelledby="vision-heading">
      <div className="vision-card">
        <div className="vision-card__copy">
          <p className="eyebrow">What's next</p>
          <h2 id="vision-heading">More things are coming</h2>
          <p>
            We're working on making hcr2.xyz the go-to place for the HCR2
            adventure community. Here's what's on the way.
          </p>
        </div>
        <div className="vision-features">
          <span className="vision-feature">Notifications</span>
          <span className="vision-feature">Achievements</span>
          <span className="vision-feature">XP system</span>
          <span className="vision-feature">Community leaderboard</span>
          <span className="vision-feature">Discord integration</span>
          <span className="vision-feature vision-feature--soon">More coming soon</span>
        </div>
      </div>
    </section>
  );
}

function TeamSection() {
  return (
    <section className="content-section content-section--compact" aria-labelledby="team-heading">
      <div className="section-heading">
        <p className="eyebrow">Team</p>
        <h2 id="team-heading">The people behind this</h2>
      </div>
      <div className="team-grid">
        {staff.map((member) => (
          <div className={`team-member team-member--${member.group}`} key={member.name}>
            <span className="team-member__name">{member.name}</span>
            <span className="team-member__role">{member.role}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function PartnersSection() {
  return (
    <section className="content-section content-section--compact" aria-labelledby="partners-heading">
      <div className="section-heading">
        <p className="eyebrow">Partners</p>
        <h2 id="partners-heading">Community partners</h2>
      </div>
      <div className="partners-grid">
        {partners.map((partner) => (
          <article className="partner-card feature-card" key={partner.name}>
            <div className="partner-card__header">
              <span className="partner-card__icon">{partner.icon}</span>
              <div>
                <h3>{partner.name}</h3>
                <p className="partner-card__subtitle">{partner.subtitle}</p>
              </div>
            </div>
            <a
              className="partner-card__discord-btn"
              href={partner.invite}
              target="_blank"
              rel="noopener noreferrer"
            >
              Join server
            </a>
          </article>
        ))}
      </div>
    </section>
  );
}

function LinksSection() {
  return (
    <section className="content-section content-section--compact" aria-labelledby="links-heading">
      <div className="section-heading">
        <p className="eyebrow">Links</p>
        <h2 id="links-heading">Stay connected</h2>
      </div>
      <div className="links-grid">
        <a
          className="link-card feature-card"
          href="https://github.com/anomalyco/hcr2-database-website"
          target="_blank"
          rel="noopener noreferrer"
        >
          <h3>GitHub</h3>
          <p>Source code and issue tracker</p>
        </a>
        <a
          className="link-card feature-card"
          href="https://www.tipeee.com/hcr2-database"
          target="_blank"
          rel="noopener noreferrer"
        >
          <h3>Support us</h3>
          <p>Help keep the site running</p>
        </a>
        <Link to="/guidelines" className="link-card feature-card">
          <h3>Record Guidelines</h3>
          <p>Full rules and submission details</p>
        </Link>
        <Link to="/changelog" className="link-card feature-card">
          <h3>Changelog</h3>
          <p>What's been updated recently</p>
        </Link>
      </div>
    </section>
  );
}

export function HomePage() {
  return (
    <main className="home-page">
      <section className="home-hero" aria-labelledby="home-title">
        <div className="home-hero__copy">
          <p className="eyebrow">Unofficial HCR2 Adventure Database</p>
          <h1 id="home-title">
            Hill Climb Racing 2
            <br />
            Adventure Records.
          </h1>
          <p className="hero-copy">
            Every verified adventure world record, every map, every vehicle, in one
            place. Built and maintained by the HCR2 community.
          </p>
          <div className="hero-actions">
            <Link className="button button--primary" to="/records">
              Browse Records
            </Link>
            <Link className="button button--secondary" to="/stats">
              View Stats
            </Link>
          </div>
        </div>
        <div className="home-hero__asset" aria-hidden="true">
          <img src="/img/hcrdatabaselogo.png" alt="" />
        </div>
      </section>

      <AdSlot slotId="7228862095" />

      <LiveStatsSection />

      <CommunityHighlight />

      <BrowseSection />

      <WhySection />

      <HowItWorksSection />

      <CommunityVisionSection />

      <TeamSection />

      <PartnersSection />

      <DonatorBanner />

      <LinksSection />
    </main>
  );
}
