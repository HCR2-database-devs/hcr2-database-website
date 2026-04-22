import { useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  asText,
  CountryWithFlag,
  formatDistance,
  MapWithIcon,
  setupPartsLabel,
  TuningPartWithIcon,
  TuningPartsIcons,
  VehicleWithIcon
} from "../lib/legacyDisplay";
import { getPublicData } from "../services/publicData";
import type { DataRow, PublicDataView } from "../types/api";

const dataTypeByView: Record<PublicDataView, string> = {
  maps: "maps",
  vehicles: "vehicles",
  players: "players",
  "tuning-parts": "tuning_parts",
  "tuning-setups": "tuning_setups",
  records: "records"
};

const viewMeta: Record<PublicDataView, { eyebrow: string; title: string; description: string }> = {
  maps: {
    eyebrow: "Catalog",
    title: "Maps",
    description: "Every Adventure map currently represented in the public records database."
  },
  vehicles: {
    eyebrow: "Catalog",
    title: "Vehicles",
    description: "The vehicle list used to normalize records, submissions and admin workflows."
  },
  players: {
    eyebrow: "Community",
    title: "Players",
    description: "Published players with their country metadata and current world record counts."
  },
  "tuning-parts": {
    eyebrow: "Catalog",
    title: "Tuning Parts",
    description: "Individual tuning parts available for submitted and published record setups."
  },
  "tuning-setups": {
    eyebrow: "Catalog",
    title: "Tuning Setups",
    description: "Saved tuning combinations used to explain record performance context."
  },
  records: {
    eyebrow: "Leaderboard",
    title: "Records",
    description: "Search, filter and export the current public Adventure world records."
  }
};

type DataViewPageProps = {
  view: PublicDataView;
};

type MultiDropdownProps = {
  id: string;
  buttonLabel: string;
  title: string;
  options: { value: string; label: ReactNode }[];
  selected: string[];
  onToggle: (value: string) => void;
  onClear: () => void;
};

function numeric(row: DataRow, ...keys: string[]) {
  const value = keys.map((key) => row[key]).find((item) => item !== undefined && item !== null);
  return Number(value ?? 0);
}

function getRecordParts(row: DataRow): string[] {
  return asText(row.tuning_parts)
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

function TableFrame({ children }: { children: ReactNode }) {
  return (
    <div className="table-shell">
      <div className="table-scroll">{children}</div>
    </div>
  );
}

function MultiDropdown({ id, buttonLabel, title, options, selected, onToggle, onClear }: MultiDropdownProps) {
  const [open, setOpen] = useState(false);
  const wrapper = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) {
      return undefined;
    }
    function closeOnOutsideClick(event: MouseEvent) {
      if (wrapper.current && !wrapper.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("click", closeOnOutsideClick);
    return () => document.removeEventListener("click", closeOnOutsideClick);
  }, [open]);

  return (
    <div className="multi-dropdown" ref={wrapper}>
      <button
        id={`${id}-btn`}
        className="filter-btn"
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        {buttonLabel}
      </button>
      <div id={`${id}-panel`} className={`dropdown-panel${open ? " open" : ""}`}>
        <div className="dropdown-header">
          <strong>{title}</strong>
          <button type="button" className="dropdown-clear" onClick={onClear}>
            Clear
          </button>
        </div>
        <div className="dropdown-content">
          {options.map((option) => (
            <label key={option.value}>
              <input
                type="checkbox"
                value={option.value}
                checked={selected.includes(option.value)}
                onChange={() => onToggle(option.value)}
              />
              {option.label}
            </label>
          ))}
        </div>
      </div>
    </div>
  );
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
    [row.distance, row.map_name, row.vehicle_name, row.player_name, row.player_country].map(escapeCell).join(",")
  );
  return [headers.join(","), ...csvRows].join("\n");
}

function RecordsFilters({ rows, onRowsChange }: { rows: DataRow[]; onRowsChange: (rows: DataRow[]) => void }) {
  const [search, setSearch] = useState("");
  const [maps, setMaps] = useState<string[]>([]);
  const [vehicles, setVehicles] = useState<string[]>([]);
  const [tuningParts, setTuningParts] = useState<string[]>([]);
  const [distanceOp, setDistanceOp] = useState("");
  const [distance, setDistance] = useState("");
  const [questionableOnly, setQuestionableOnly] = useState(false);
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [sort, setSort] = useState("default");

  const mapOptions = useMemo(() => [...new Set(rows.map((row) => asText(row.map_name)).filter(Boolean))].sort(), [rows]);
  const vehicleOptions = useMemo(
    () => [...new Set(rows.map((row) => asText(row.vehicle_name)).filter(Boolean))].sort(),
    [rows]
  );
  const tuningOptions = useMemo(() => [...new Set(rows.flatMap(getRecordParts))].sort(), [rows]);

  const filteredRows = useMemo(() => {
    const query = search.trim().toLowerCase();
    const distanceNumber = Number(distance);
    const output = rows.filter((row) => {
      const notesText = asText(row.questionable_reason ?? row.questionableReason).toLowerCase();
      const matchesSearch =
        !query ||
        asText(row.player_name).toLowerCase().includes(query) ||
        asText(row.map_name).toLowerCase().includes(query) ||
        asText(row.vehicle_name).toLowerCase().includes(query) ||
        notesText.includes(query);
      const matchesMap = maps.length === 0 || maps.includes(asText(row.map_name));
      const matchesVehicle = vehicles.length === 0 || vehicles.includes(asText(row.vehicle_name));
      const rowParts = getRecordParts(row);
      const matchesTuning = tuningParts.length === 0 || tuningParts.some((part) => rowParts.includes(part));
      let matchesDistance = true;
      if (distanceOp === "gte" && !Number.isNaN(distanceNumber)) {
        matchesDistance = Number(row.distance) >= distanceNumber;
      } else if (distanceOp === "lte" && !Number.isNaN(distanceNumber)) {
        matchesDistance = Number(row.distance) <= distanceNumber;
      }
      const matchesQuestionable = !questionableOnly || Number(row.questionable) === 1;
      const matchesVerified = !verifiedOnly || Number(row.questionable) === 0;
      return matchesSearch && matchesMap && matchesVehicle && matchesTuning && matchesDistance && matchesQuestionable && matchesVerified;
    });

    output.sort((a, b) => {
      if (sort === "dist-asc") {
        return Number(a.distance) - Number(b.distance);
      }
      if (sort === "dist-desc") {
        return Number(b.distance) - Number(a.distance);
      }
      if (sort === "most-recent") {
        return Number(b.idRecord ?? b.record_id ?? b.idrecord ?? 0) - Number(a.idRecord ?? a.record_id ?? a.idrecord ?? 0);
      }
      const mapComparison = asText(a.map_name).localeCompare(asText(b.map_name));
      if (mapComparison !== 0) {
        return mapComparison;
      }
      return Number(a.idVehicle ?? a.vehicle_id ?? a.idvehicle ?? 0) - Number(b.idVehicle ?? b.vehicle_id ?? b.idvehicle ?? 0);
    });
    return output;
  }, [distance, distanceOp, maps, questionableOnly, rows, search, sort, tuningParts, vehicles, verifiedOnly]);

  useEffect(() => {
    onRowsChange(filteredRows);
  }, [filteredRows, onRowsChange]);

  function toggleSelected(current: string[], value: string, setter: (next: string[]) => void) {
    setter(current.includes(value) ? current.filter((item) => item !== value) : [...current, value]);
  }

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
    <div id="filter-container" className="filter-container">
      <div className="filter-row filter-row--search">
        <input
          type="text"
          id="search-bar"
          className="filter-search"
          placeholder="Search by player, map, vehicle or note"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
      </div>

      <div className="filter-row">
        <button id="export-btn" className="filter-btn filter-btn--primary" type="button" onClick={exportCsv}>
          Export CSV
        </button>

        <div className="filter-group">
          <MultiDropdown
            id="map"
            buttonLabel="Maps"
            title="Maps"
            options={mapOptions.map((item) => ({ value: item, label: <MapWithIcon name={item} /> }))}
            selected={maps}
            onToggle={(value) => toggleSelected(maps, value, setMaps)}
            onClear={() => setMaps([])}
          />
          <MultiDropdown
            id="vehicle"
            buttonLabel="Vehicles"
            title="Vehicles"
            options={vehicleOptions.map((item) => ({ value: item, label: <VehicleWithIcon name={item} /> }))}
            selected={vehicles}
            onToggle={(value) => toggleSelected(vehicles, value, setVehicles)}
            onClear={() => setVehicles([])}
          />
          <MultiDropdown
            id="tuning"
            buttonLabel="Tuning"
            title="Tuning Parts"
            options={tuningOptions.map((item) => ({ value: item, label: <TuningPartWithIcon name={item} /> }))}
            selected={tuningParts}
            onToggle={(value) => toggleSelected(tuningParts, value, setTuningParts)}
            onClear={() => setTuningParts([])}
          />
        </div>

        <select id="sort-select" className="filter-select" value={sort} onChange={(event) => setSort(event.target.value)}>
          <option value="default">Sort: Default</option>
          <option value="dist-asc">Sort: Distance ASC</option>
          <option value="dist-desc">Sort: Distance DESC</option>
          <option value="most-recent">Sort: Newest</option>
        </select>

        <div className="filter-distance">
          <select id="distance-op" className="filter-select" value={distanceOp} onChange={(event) => setDistanceOp(event.target.value)}>
            <option value="">Distance</option>
            <option value="gte">&gt;=</option>
            <option value="lte">&lt;=</option>
          </select>
          <input
            type="number"
            id="distance-value"
            className="filter-input"
            placeholder="Value"
            value={distance}
            onChange={(event) => setDistance(event.target.value)}
          />
        </div>

        <label className="filter-label">
          <input
            type="checkbox"
            id="questionable-filter"
            className="filter-checkbox"
            checked={questionableOnly}
            onChange={(event) => setQuestionableOnly(event.target.checked)}
          />
          <span>Questionable</span>
        </label>

        <label className="filter-label">
          <input
            type="checkbox"
            id="verified-filter"
            className="filter-checkbox"
            checked={verifiedOnly}
            onChange={(event) => setVerifiedOnly(event.target.checked)}
          />
          <span>Verified</span>
        </label>
      </div>
    </div>
  );
}

function PlayerFilters({
  rows,
  recordCounts,
  onRowsChange
}: {
  rows: DataRow[];
  recordCounts: Record<string, number>;
  onRowsChange: (rows: DataRow[]) => void;
}) {
  const [search, setSearch] = useState("");
  const [countries, setCountries] = useState<string[]>([]);
  const [recordCountOp, setRecordCountOp] = useState("");
  const [recordCountValue, setRecordCountValue] = useState("");
  const countryOptions = useMemo(() => [...new Set(rows.map((row) => asText(row.country)).filter(Boolean))].sort(), [rows]);

  const filteredRows = useMemo(() => {
    const countValue = Number(recordCountValue);
    return rows.filter((row) => {
      const name = asText(row.namePlayer);
      const count = recordCounts[name] ?? 0;
      const matchesSearch = !search || name.toLowerCase().includes(search.toLowerCase());
      const matchesCountry = countries.length === 0 || countries.includes(asText(row.country));
      let matchesCount = true;
      if (recordCountOp === "gte" && !Number.isNaN(countValue)) {
        matchesCount = count >= countValue;
      } else if (recordCountOp === "lte" && !Number.isNaN(countValue)) {
        matchesCount = count <= countValue;
      }
      return matchesSearch && matchesCountry && matchesCount;
    });
  }, [countries, recordCountOp, recordCountValue, recordCounts, rows, search]);

  useEffect(() => {
    onRowsChange(filteredRows);
  }, [filteredRows, onRowsChange]);

  return (
    <div id="filter-container" className="filter-container filter-container--compact">
      <input
        type="text"
        id="player-search"
        className="filter-search"
        placeholder="Search by player name"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
      />
      <MultiDropdown
        id="country"
        buttonLabel="Countries"
        title="Countries"
        options={countryOptions.map((country) => ({ value: country, label: country }))}
        selected={countries}
        onToggle={(value) =>
          setCountries((current) =>
            current.includes(value) ? current.filter((item) => item !== value) : [...current, value]
          )
        }
        onClear={() => setCountries([])}
      />
      <select id="record-count-op" className="filter-select" value={recordCountOp} onChange={(event) => setRecordCountOp(event.target.value)}>
        <option value="">Record Count</option>
        <option value="gte">&gt;=</option>
        <option value="lte">&lt;=</option>
      </select>
      <input
        type="number"
        id="record-count-value"
        className="filter-input"
        placeholder="Count"
        value={recordCountValue}
        onChange={(event) => setRecordCountValue(event.target.value)}
      />
    </div>
  );
}

function StatusBadge({ questionable, note }: { questionable: unknown; note: string }) {
  if (Number(questionable) === 1) {
    return (
      <span title={`Questionable: ${note || "No note provided"}`} className="status-pill status-pill--questionable">
        Questionable
      </span>
    );
  }
  return (
    <span title="Verified: confirmed legitimate record" className="status-pill status-pill--verified">
      Verified
    </span>
  );
}

function PublicTable({
  view,
  rows,
  recordCounts,
  onNote
}: {
  view: PublicDataView;
  rows: DataRow[];
  recordCounts: Record<string, number>;
  onNote: (note: string) => void;
}) {
  if (rows.length === 0) {
    return <p className="empty-state">No data available.</p>;
  }

  if (view === "maps") {
    return (
      <TableFrame>
        <table>
          <tbody>
            <tr>
              <th>Map ID</th>
              <th>Map Name</th>
            </tr>
            {rows.map((item) => (
              <tr key={numeric(item, "idMap", "idmap")}>
                <td>{numeric(item, "idMap", "idmap")}</td>
                <td>{asText(item.nameMap ?? item.namemap)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableFrame>
    );
  }

  if (view === "vehicles") {
    return (
      <TableFrame>
        <table>
          <tbody>
            <tr>
              <th>Vehicle ID</th>
              <th>Vehicle Name</th>
            </tr>
            {rows.map((item) => (
              <tr key={numeric(item, "idVehicle", "idvehicle")}>
                <td>{numeric(item, "idVehicle", "idvehicle")}</td>
                <td>{asText(item.nameVehicle ?? item.namevehicle)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableFrame>
    );
  }

  if (view === "players") {
    return (
      <TableFrame>
        <table>
          <tbody>
            <tr>
              <th>Player ID</th>
              <th>Player Name</th>
              <th>Country</th>
              <th>World Records</th>
            </tr>
            {rows.map((item) => {
              const playerName = asText(item.namePlayer ?? item.nameplayer);
              return (
                <tr key={numeric(item, "idPlayer", "idplayer")}>
                  <td>{numeric(item, "idPlayer", "idplayer")}</td>
                  <td>{playerName}</td>
                  <td>
                    <CountryWithFlag country={item.country} />
                  </td>
                  <td>{recordCounts[playerName] ?? 0}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </TableFrame>
    );
  }

  if (view === "tuning-parts") {
    return (
      <TableFrame>
        <table>
          <tbody>
            <tr>
              <th>Part ID</th>
              <th>Part Name</th>
            </tr>
            {rows.map((item) => {
              const name = asText(item.nameTuningPart ?? item.nametuningpart ?? item.name);
              return (
                <tr key={numeric(item, "idTuningPart", "idtuningpart", "id")}>
                  <td>{numeric(item, "idTuningPart", "idtuningpart", "id")}</td>
                  <td>
                    <TuningPartWithIcon name={name} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </TableFrame>
    );
  }

  if (view === "tuning-setups") {
    return (
      <TableFrame>
        <table>
          <tbody>
            <tr>
              <th>Setup ID</th>
              <th>Tuning Parts</th>
            </tr>
            {rows.map((item) => (
              <tr key={numeric(item, "idTuningSetup", "idtuningsetup")}>
                <td>{numeric(item, "idTuningSetup", "idtuningsetup")}</td>
                <td>{setupPartsLabel(item.parts)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableFrame>
    );
  }

  return (
    <TableFrame>
      <table className="public-records-table">
        <thead>
          <tr>
            <th>Distance</th>
            <th>Status</th>
            <th>Notes</th>
            <th>Map Name</th>
            <th>Vehicle Name</th>
            <th>Tuning Parts</th>
            <th>Player Name</th>
            <th>Player Country</th>
            <th>Share</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((item) => {
            const recordId = asText(item.idRecord ?? item.record_id ?? item.idrecord);
            const note = asText(item.questionable_reason ?? item.questionableReason);
            const mapName = asText(item.map_name);
            const shareUrl = `${window.location.origin}/records?recordId=${encodeURIComponent(recordId)}&map=${encodeURIComponent(mapName)}`;
            return (
              <tr key={recordId} data-record-id={recordId}>
                <td data-label="Distance">{formatDistance(item.distance)}</td>
                <td data-label="Status">
                  <StatusBadge questionable={item.questionable} note={note} />
                </td>
                <td data-label="Notes">
                  {note && (
                    <button className="note-btn" type="button" onClick={() => onNote(note)}>
                      Note
                    </button>
                  )}
                </td>
                <td data-label="Map">
                  <MapWithIcon name={item.map_name} />
                </td>
                <td data-label="Vehicle">
                  <VehicleWithIcon name={item.vehicle_name} />
                </td>
                <td data-label="Tuning Parts">
                  <TuningPartsIcons parts={item.tuning_parts} />
                </td>
                <td data-label="Player">{asText(item.player_name)}</td>
                <td data-label="Country">
                  <CountryWithFlag country={item.player_country} />
                </td>
                <td data-label="Share">
                  <button className="share-btn" type="button" onClick={() => navigator.clipboard?.writeText(shareUrl)}>
                    Copy
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </TableFrame>
  );
}

function NoteModal({ note, onClose }: { note: string; onClose: () => void }) {
  return (
    <div id="note-overlay" className="modal-overlay">
      <div className="modal-panel form-container" role="dialog" aria-modal="true" aria-labelledby="note-title">
        <button className="modal-close" type="button" onClick={onClose} aria-label="Close">
          Close
        </button>
        <h2 id="note-title">Record Note</h2>
        <div id="note-content" className="modal-scroll frontend-pre-wrap">
          {note}
        </div>
        <div className="frontend-modal-actions">
          <button className="close-note-btn" type="button" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export function DataViewPage({ view }: DataViewPageProps) {
  const [visibleRows, setVisibleRows] = useState<DataRow[]>([]);
  const [note, setNote] = useState("");
  const data = useQuery({
    queryKey: ["public-data", view],
    queryFn: () => getPublicData(view)
  });
  const records = useQuery({
    enabled: view === "players",
    queryKey: ["public-data", "records"],
    queryFn: () => getPublicData("records")
  });

  const rows = data.data ?? [];
  const playerRecordCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    (records.data ?? []).forEach((record) => {
      const name = asText(record.player_name);
      counts[name] = (counts[name] ?? 0) + 1;
    });
    return counts;
  }, [records.data]);

  const displayedRows = view === "records" || view === "players" ? visibleRows : rows;
  const meta = viewMeta[view];

  return (
    <main className="data-page">
      <section className="page-hero page-hero--compact" aria-labelledby="data-view-title">
        <p className="eyebrow">{meta.eyebrow}</p>
        <h1 id="data-view-title">{meta.title}</h1>
        <p>{meta.description}</p>
      </section>

      {view === "records" && data.data && <RecordsFilters rows={rows} onRowsChange={setVisibleRows} />}
      {view === "players" && data.data && (
        <PlayerFilters rows={rows} recordCounts={playerRecordCounts} onRowsChange={setVisibleRows} />
      )}

      <section id="data-container" className="data-section">
        <h2>{dataTypeByView[view].toUpperCase()}</h2>
        {data.isLoading && <p className="loading-state">Loading data...</p>}
        {data.isError && <p className="frontend-error">Error fetching data from server.</p>}
        {data.data && (
          <PublicTable
            view={view}
            rows={displayedRows}
            recordCounts={playerRecordCounts}
            onNote={(nextNote) => setNote(nextNote)}
          />
        )}
      </section>
      {note && <NoteModal note={note} onClose={() => setNote("")} />}
    </main>
  );
}
