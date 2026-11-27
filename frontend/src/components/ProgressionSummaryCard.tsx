import type { ProgressionSummary } from "../types/api";

type ProgressionSummaryCardProps = {
  progression: ProgressionSummary;
  compact?: boolean;
};

export function ProgressionSummaryCard({ progression, compact = false }: ProgressionSummaryCardProps) {
  return (
    <section className={`progression-card${compact ? " progression-card--compact" : ""}`}>
      <div className="progression-card__head">
        <span className="progression-card__level">Level {progression.level}</span>
        <span className="progression-card__xp">{progression.total_xp.toLocaleString()} XP</span>
      </div>
      <div className="progression-card__track" aria-hidden="true">
        <span style={{ width: `${progression.progress_percent}%` }} />
      </div>
      <p className="progression-card__meta">
        {progression.xp_to_next > 0
          ? `${progression.xp_to_next.toLocaleString()} XP to level ${progression.level + 1}`
          : "Maximum tracked level reached"}
      </p>
    </section>
  );
}
