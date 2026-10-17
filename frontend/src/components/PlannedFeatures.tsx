import { PLANNED_FEATURES } from "../lib/communityInfo";

export function PlannedFeatures() {
  return (
    <div className="vision-features">
      {PLANNED_FEATURES.map((feature) => (
        <span className="vision-feature" key={feature.id}>
          {feature.label}
        </span>
      ))}
      <span className="vision-feature vision-feature--soon">More coming soon</span>
    </div>
  );
}