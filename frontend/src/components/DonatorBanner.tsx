import { useQuery } from "@tanstack/react-query";

import { getTippers } from "../services/tippers";

export function DonatorBanner() {
  const { data } = useQuery({
    queryKey: ["tippers"],
    queryFn: getTippers,
    refetchInterval: 3_600_000,
  });

  const names = data?.tippers?.map((t) => t.pseudo) ?? [];

  if (names.length === 0) return null;

  const list = names.join(" \u2022 ");

  return (
    <div className="donator-banner" aria-label="Supporters">
      <span className="donator-banner__label">Supporters</span>
      <div className="donator-banner__track">
        <span className="donator-banner__names">
          {list}
          {" \u2022 "}
          {list}
        </span>
      </div>
    </div>
  );
}
