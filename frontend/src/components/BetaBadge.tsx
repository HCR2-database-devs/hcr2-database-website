import { useFeatureState } from "../lib/features";
import type { FeatureName } from "../types/api";

type BetaBadgeProps = {
  feature: FeatureName;
  className?: string;
};

export function BetaBadge({ feature, className }: BetaBadgeProps) {
  const state = useFeatureState(feature);
  if (state !== "BETA") return null;
  return <span className={`beta-badge${className ? ` ${className}` : ""}`}>BETA</span>;
}