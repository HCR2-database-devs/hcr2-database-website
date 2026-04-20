import { useQuery } from "@tanstack/react-query";

import { DataTable } from "../features/public-data/DataTable";
import { getPublicData } from "../services/publicData";
import type { PublicDataView } from "../types/api";

const titles: Record<PublicDataView, string> = {
  maps: "Maps",
  vehicles: "Vehicles",
  players: "Players",
  "tuning-parts": "Tuning Parts",
  "tuning-setups": "Tuning Setups",
  records: "Records"
};

type DataViewPageProps = {
  view: PublicDataView;
};

export function DataViewPage({ view }: DataViewPageProps) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["public-data", view],
    queryFn: () => getPublicData(view)
  });

  return (
    <section id="data-container">
      <h2>{titles[view]}</h2>
      {isLoading && <p>Loading data...</p>}
      {isError && <p className="frontend-error">{error.message}</p>}
      {data && <DataTable rows={data} />}
    </section>
  );
}
