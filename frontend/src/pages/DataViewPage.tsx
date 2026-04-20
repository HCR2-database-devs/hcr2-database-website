import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { DataTable } from "../features/public-data/DataTable";
import { getPublicData } from "../services/publicData";
import type { DataRow, PublicDataView } from "../types/api";

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

function asText(value: unknown): string {
  return value === null || value === undefined ? "" : String(value);
}

function getRecordParts(row: DataRow): string[] {
  const value = row.tuning_parts;
  if (Array.isArray(value)) {
    return value.map(String);
  }
  return asText(value)
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

function buildCsv(rows: DataRow[]) {
  const headers = ["Distance", "Map Name", "Vehicle Name", "Player Name", "Country"];
  const escapeCell = (value: unknown) => {
    const text = asText(value);
    if (text.includes(",") || text.includes('"') || text.includes("\n")) {
      return `"${text.replace(/"/g, '""')}"`;
    }
    return text;
  };
  const csvRows = rows.map((row) =>
    [row.distance, row.map_name, row.vehicle_name, row.player_name, row.player_country]
      .map(escapeCell)
      .join(",")
  );
  return [headers.join(","), ...csvRows].join("\n");
}

function RecordsFilters({ rows }: { rows: DataRow[] }) {
  const [search, setSearch] = useState("");
  const [map, setMap] = useState("");
  const [vehicle, setVehicle] = useState("");
  const [tuningPart, setTuningPart] = useState("");
  const [distanceOp, setDistanceOp] = useState("");
  const [distance, setDistance] = useState("");
  const [status, setStatus] = useState("");
  const [sort, setSort] = useState("default");

  const maps = useMemo(
    () => [...new Set(rows.map((row) => asText(row.map_name)).filter(Boolean))].sort(),
    [rows]
  );
  const vehicles = useMemo(
    () => [...new Set(rows.map((row) => asText(row.vehicle_name)).filter(Boolean))].sort(),
    [rows]
  );
  const tuningParts = useMemo(
    () => [...new Set(rows.flatMap(getRecordParts))].sort(),
    [rows]
  );

  const filteredRows = useMemo(() => {
    const query = search.trim().toLowerCase();
    const distanceNumber = Number(distance);
    const output = rows.filter((row) => {
      const notes = asText(row.questionable_reason ?? row.notes).toLowerCase();
      const matchesSearch =
        !query ||
        asText(row.player_name).toLowerCase().includes(query) ||
        asText(row.map_name).toLowerCase().includes(query) ||
        asText(row.vehicle_name).toLowerCase().includes(query) ||
        notes.includes(query);
      const matchesMap = !map || row.map_name === map;
      const matchesVehicle = !vehicle || row.vehicle_name === vehicle;
      const matchesTuning = !tuningPart || getRecordParts(row).includes(tuningPart);
      const matchesStatus =
        !status ||
        (status === "questionable" && Number(row.questionable) === 1) ||
        (status === "verified" && Number(row.questionable) === 0);
      let matchesDistance = true;
      if (distanceOp && !Number.isNaN(distanceNumber)) {
        matchesDistance =
          distanceOp === "gte"
            ? Number(row.distance) >= distanceNumber
            : Number(row.distance) <= distanceNumber;
      }
      return (
        matchesSearch &&
        matchesMap &&
        matchesVehicle &&
        matchesTuning &&
        matchesStatus &&
        matchesDistance
      );
    });

    output.sort((a, b) => {
      if (sort === "dist-asc") {
        return Number(a.distance) - Number(b.distance);
      }
      if (sort === "dist-desc") {
        return Number(b.distance) - Number(a.distance);
      }
      if (sort === "most-recent") {
        return Number(b.idRecord ?? b.idrecord ?? 0) - Number(a.idRecord ?? a.idrecord ?? 0);
      }
      const mapComparison = asText(a.map_name).localeCompare(asText(b.map_name));
      if (mapComparison !== 0) {
        return mapComparison;
      }
      return asText(a.vehicle_name).localeCompare(asText(b.vehicle_name));
    });

    return output;
  }, [distance, distanceOp, map, rows, search, sort, status, tuningPart, vehicle]);

  function exportCsv() {
    if (filteredRows.length === 0) {
      window.alert("No records to export. Please check your filters.");
      return;
    }
    const blob = new Blob([buildCsv(filteredRows)], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `HCR2_Records_${new Date().toISOString().split("T")[0]}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  return (
    <>
      <div id="filter-container" className="filter-container">
        <input
          id="search-bar"
          type="text"
          placeholder="Search by player, map, vehicle or note..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <select value={map} onChange={(event) => setMap(event.target.value)}>
          <option value="">All maps</option>
          {maps.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <select value={vehicle} onChange={(event) => setVehicle(event.target.value)}>
          <option value="">All vehicles</option>
          {vehicles.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <select value={tuningPart} onChange={(event) => setTuningPart(event.target.value)}>
          <option value="">All tuning parts</option>
          {tuningParts.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <select value={distanceOp} onChange={(event) => setDistanceOp(event.target.value)}>
          <option value="">Distance</option>
          <option value="gte">At least</option>
          <option value="lte">At most</option>
        </select>
        <input
          type="number"
          placeholder="Distance"
          value={distance}
          onChange={(event) => setDistance(event.target.value)}
        />
        <select value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">All statuses</option>
          <option value="verified">Verified only</option>
          <option value="questionable">Questionable only</option>
        </select>
        <select id="sort-select" value={sort} onChange={(event) => setSort(event.target.value)}>
          <option value="default">Default order</option>
          <option value="dist-desc">Distance high to low</option>
          <option value="dist-asc">Distance low to high</option>
          <option value="most-recent">Most recent</option>
        </select>
        <button type="button" onClick={exportCsv}>
          Export CSV
        </button>
      </div>
      <DataTable rows={filteredRows} />
    </>
  );
}

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
      {data && view === "records" && <RecordsFilters rows={data} />}
      {data && view !== "records" && <DataTable rows={data} />}
    </section>
  );
}
