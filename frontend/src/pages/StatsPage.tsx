import { useQuery } from "@tanstack/react-query";

import { getPublicData } from "../services/publicData";

export function StatsPage() {
  const records = useQuery({
    queryKey: ["public-data", "records"],
    queryFn: () => getPublicData("records")
  });

  const recordRows = records.data ?? [];
  const players = new Set(recordRows.map((row) => row.player_name).filter(Boolean));
  const maps = new Set(recordRows.map((row) => row.map_name).filter(Boolean));
  const vehicles = new Set(recordRows.map((row) => row.vehicle_name).filter(Boolean));

  return (
    <section id="stats-container">
      <h2>Stats</h2>
      {records.isLoading && <p>Loading stats...</p>}
      {records.isError && <p className="frontend-error">{records.error.message}</p>}
      {records.data && (
        <div className="stats-grid">
          <div>
            <strong>{recordRows.length}</strong>
            <span>Records</span>
          </div>
          <div>
            <strong>{players.size}</strong>
            <span>Players</span>
          </div>
          <div>
            <strong>{maps.size}</strong>
            <span>Maps</span>
          </div>
          <div>
            <strong>{vehicles.size}</strong>
            <span>Vehicles</span>
          </div>
        </div>
      )}
    </section>
  );
}
