import { useQuery } from "@tanstack/react-query";

import { getAuthStatus } from "../services/auth";

export function useAuthStatus() {
  return useQuery({
    queryKey: ["auth-status"],
    queryFn: getAuthStatus,
    refetchInterval: 30_000
  });
}
