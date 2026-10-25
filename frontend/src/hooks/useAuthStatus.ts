import { useQuery } from "@tanstack/react-query";

import { getAuthStatus } from "../services/auth";

export function useAuthStatus() {
  return useQuery({
    queryKey: ["auth-status"],
    queryFn: getAuthStatus,
    staleTime: 60_000,
    refetchInterval: (query) => (query.state.data?.logged ? 60_000 : false)
  });
}
