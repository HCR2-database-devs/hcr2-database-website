import { useAuthStatus } from "../hooks/useAuthStatus";
import type { FeatureName, FeatureState } from "../types/api";

type FeatureAccess = {
  state: FeatureState;
  canUse: boolean;
  isLoading: boolean;
};

function computeCanUse(
  state: FeatureState,
  logged: boolean,
  beta: boolean,
  allowed: boolean,
): boolean {
  if (state === "DISABLED") return false;
  if (state === "ENABLED") return true;
  if (!logged) return false;
  return beta || allowed;
}

function resolveFeature(
  name: FeatureName,
  authStatus: ReturnType<typeof useAuthStatus>["data"],
): FeatureAccess {
  const state: FeatureState = authStatus?.features?.[name] ?? "DISABLED";
  const canUse = computeCanUse(
    state,
    authStatus?.logged ?? false,
    authStatus?.beta ?? false,
    authStatus?.allowed ?? false,
  );
  return { state, canUse, isLoading: authStatus === undefined };
}

export function useFeatureAccess(name: FeatureName): FeatureAccess {
  const { data: authStatus } = useAuthStatus();
  return resolveFeature(name, authStatus);
}

export function useFeatureState(name: FeatureName): FeatureState {
  const { data: authStatus } = useAuthStatus();
  return authStatus?.features?.[name] ?? "DISABLED";
}

export function useCanUseFeature(name: FeatureName): boolean {
  return useFeatureAccess(name).canUse;
}
