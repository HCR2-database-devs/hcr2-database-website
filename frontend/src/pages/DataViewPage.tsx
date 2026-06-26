import { useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { useVirtualizer } from "@tanstack/react-virtual";

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
import { useBodyScrollLock } from "../hooks/useBodyScrollLock";
import { exportRecords, getPublicData, getRecordsPaginated } from "../services/publicData";
import type { DataRow, PaginatedRecordsResponse, PublicDataView, RecordFilters } from "../types/api";
import { emptyRecordFilters } from "../types/api";

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

function downloadCsv(rows: DataRow[]) {
  const blob = new Blob([buildCsv(rows)], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `HCR2_Records_${new Date().toISOString().split("T")[0]}.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
}

function RecordsFilters({
  filters,
  onChange,
  mapOptions,
  vehicleOptions,
  tuningOptions,
  onExport,
  isExporting
}: {
  filters: RecordFilters;
  onChange: (patch: Partial<RecordFilters>) => void;
  mapOptions: string[];
  vehicleOptions: string[];
  tuningOptions: string[];
  onExport: () => void;
  isExporting: boolean;
}) {
  function toggleList(current: string[], value: string, key: keyof RecordFilters) {
    const next = current.includes(value) ? current.filter((i) => i !== value) : [...current, value];
    onChange({ [key]: next });
  }

  return (
    <div id="filter-container" className="filter-container">
      <div className="filter-row filter-row--search">
        <input
          type="text"
          id="search-bar"
          className="filter-search"
          placeholder="Search by player, map, vehicle or note"
          value={filters.search}
          onChange={(e) => onChange({ search: e.target.value })}
        />
      </div>

      <div className="filter-row">
        <button
          id="export-btn"
          className="filter-btn filter-btn--primary"
          type="button"
          disabled={isExporting}
          onClick={onExport}
        >
          {isExporting ? "Exporting…" : "Export CSV"}
        </button>

        <div className="filter-group">
          <MultiDropdown
            id="map"
            buttonLabel="Maps"
            title="Maps"
            options={mapOptions.map((item) => ({ value: item, label: <MapWithIcon name={item} /> }))}
            selected={filters.maps}
            onToggle={(value) => toggleList(filters.maps, value, "maps")}
            onClear={() => onChange({ maps: [] })}
          />
          <MultiDropdown
            id="vehicle"
            buttonLabel="Vehicles"
            title="Vehicles"
            options={vehicleOptions.map((item) => ({ value: item, label: <VehicleWithIcon name={item} /> }))}
            selected={filters.vehicles}
            onToggle={(value) => toggleList(filters.vehicles, value, "vehicles")}
            onClear={() => onChange({ vehicles: [] })}
          />
          <MultiDropdown
            id="tuning"
            buttonLabel="Tuning"
            title="Tuning Parts"
            options={tuningOptions.map((item) => ({ value: item, label: <TuningPartWithIcon name={item} /> }))}
            selected={filters.tuningParts}
            onToggle={(value) => toggleList(filters.tuningParts, value, "tuningParts")}
            onClear={() => onChange({ tuningParts: [] })}
          />
        </div>

        <select
          id="sort-select"
          className="filter-select"
          value={filters.sort}
          onChange={(e) => onChange({ sort: e.target.value })}
        >
          <option value="default">Sort: Default</option>
          <option value="dist-asc">Sort: Distance ASC</option>
          <option value="dist-desc">Sort: Distance DESC</option>
          <option value="most-recent">Sort: Newest</option>
        </select>

        <div className="filter-distance">
          <select
            id="distance-op"
            className="filter-select"
            value={filters.distanceOp}
            onChange={(e) => onChange({ distanceOp: e.target.value as RecordFilters["distanceOp"] })}
          >
            <option value="">Distance</option>
            <option value="gte">&gt;=</option>
            <option value="lte">&lt;=</option>
          </select>
          <input
            type="number"
            id="distance-value"
            className="filter-input"
            placeholder="Value"
            value={filters.distance}
            onChange={(e) => onChange({ distance: e.target.value })}
          />
        </div>

        <label className="filter-label">
          <input
            type="checkbox"
            id="questionable-filter"
            className="filter-checkbox"
            checked={filters.questionableOnly}
            onChange={(e) => onChange({ questionableOnly: e.target.checked, verifiedOnly: false })}
          />
          <span>Questionable</span>
        </label>

        <label className="filter-label">
          <input
            type="checkbox"
            id="verified-filter"
            className="filter-checkbox"
            checked={filters.verifiedOnly}
            onChange={(e) => onChange({ verifiedOnly: e.target.checked, questionableOnly: false })}
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

const RECORDS_COL_COUNT = 9;
const PLAYERS_COL_COUNT = 4;
const RECORD_ROW_HEIGHT = 50;
const PLAYER_ROW_HEIGHT = 48;
const VIRTUAL_TABLE_HEIGHT = "72vh";
const MOBILE_BREAKPOINT = "(max-width: 720px)";

function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches);
  useEffect(() => {
    const mql = window.matchMedia(query);
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, [query]);
  return matches;
}

function recordRow(item: DataRow, index: number, onNote: (note: string) => void) {
  const recordId = asText(item.idRecord ?? item.record_id ?? item.idrecord);
  const note = asText(item.questionable_reason ?? item.questionableReason);
  const mapName = asText(item.map_name);
  const shareUrl = `${window.location.origin}/records?recordId=${encodeURIComponent(recordId)}&map=${encodeURIComponent(mapName)}`;
  return (
    <tr key={recordId || index} data-record-id={recordId}>
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
        <span className="tuning-parts-row">
          <TuningPartsIcons parts={item.tuning_parts} />
        </span>
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
}

function VirtualRecordsTable({
  rows,
  total,
  hasNextPage,
  isFetchingNextPage,
  onLoadMore,
  onNote,
  isMobile
}: {
  rows: DataRow[];
  total: number;
  hasNextPage: boolean;
  isFetchingNextPage: boolean;
  onLoadMore: () => void;
  onNote: (note: string) => void;
  isMobile: boolean;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sentinelRef = useRef<HTMLDivElement>(null);

  const rowVirtualizer = useVirtualizer({
    count: isMobile ? 0 : rows.length,
    getScrollElement: () => containerRef.current,
    estimateSize: () => RECORD_ROW_HEIGHT,
    overscan: 10
  });

  const virtualItems = rowVirtualizer.getVirtualItems();

  useEffect(() => {
    if (isMobile) {
      if (!sentinelRef.current || !hasNextPage || isFetchingNextPage) return;
      const sentinel = sentinelRef.current;
      const observer = new IntersectionObserver(
        (entries) => {
          if (entries[0]?.isIntersecting && hasNextPage && !isFetchingNextPage) {
            onLoadMore();
          }
        },
        { rootMargin: "400px" }
      );
      observer.observe(sentinel);
      return () => observer.disconnect();
    }
    if (!virtualItems.length) return;
    const lastItem = virtualItems[virtualItems.length - 1];
    if (lastItem.index >= rows.length - 15 && hasNextPage && !isFetchingNextPage) {
      onLoadMore();
    }
  }, [isMobile, virtualItems, rows.length, hasNextPage, isFetchingNextPage, onLoadMore]);

  if (isMobile) {
    return (
      <div className="table-shell">
        <div className="table-scroll table-scroll--virtual">
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
              {rows.map((item, index) => recordRow(item, index, onNote))}
            </tbody>
          </table>
          <div ref={sentinelRef} />
          {isFetchingNextPage && <p className="loading-state loading-state--inline">Loading more records…</p>}
        </div>
        <p className="table-count-info">
          {rows.length} / {total} records loaded
        </p>
      </div>
    );
  }

  const paddingTop = virtualItems[0]?.start ?? 0;
  const paddingBottom =
    virtualItems.length > 0 ? rowVirtualizer.getTotalSize() - (virtualItems[virtualItems.length - 1]?.end ?? 0) : 0;

  return (
    <div className="table-shell">
      <div
        ref={containerRef}
        className="table-scroll table-scroll--virtual"
        style={{ maxHeight: VIRTUAL_TABLE_HEIGHT }}
      >
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
            {paddingTop > 0 && (
              <tr>
                <td colSpan={RECORDS_COL_COUNT} style={{ height: paddingTop, padding: 0, border: "none" }} />
              </tr>
            )}
            {virtualItems.map((vRow) => recordRow(rows[vRow.index], vRow.index, onNote))}
            {paddingBottom > 0 && (
              <tr>
                <td colSpan={RECORDS_COL_COUNT} style={{ height: paddingBottom, padding: 0, border: "none" }} />
              </tr>
            )}
          </tbody>
        </table>
        {isFetchingNextPage && <p className="loading-state loading-state--inline">Loading more records…</p>}
      </div>
      <p className="table-count-info">
        {rows.length} / {total} records loaded
      </p>
    </div>
  );
}

function VirtualPlayersTable({
  rows,
  recordCounts
}: {
  rows: DataRow[];
  recordCounts: Record<string, number>;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => containerRef.current,
    estimateSize: () => PLAYER_ROW_HEIGHT,
    overscan: 10
  });

  const virtualItems = rowVirtualizer.getVirtualItems();
  const paddingTop = virtualItems[0]?.start ?? 0;
  const paddingBottom =
    virtualItems.length > 0 ? rowVirtualizer.getTotalSize() - (virtualItems[virtualItems.length - 1]?.end ?? 0) : 0;

  return (
    <div className="table-shell">
      <div
        ref={containerRef}
        className="table-scroll table-scroll--virtual"
        style={{ maxHeight: VIRTUAL_TABLE_HEIGHT }}
      >
        <table>
          <thead>
            <tr>
              <th>Player ID</th>
              <th>Player Name</th>
              <th>Country</th>
              <th>World Records</th>
            </tr>
          </thead>
          <tbody>
            {paddingTop > 0 && (
              <tr>
                <td colSpan={PLAYERS_COL_COUNT} style={{ height: paddingTop, padding: 0, border: "none" }} />
              </tr>
            )}
            {virtualItems.map((vRow) => {
              const item = rows[vRow.index];
              const playerName = asText(item.namePlayer ?? item.nameplayer);
              return (
                <tr key={vRow.key}>
                  <td>{numeric(item, "idPlayer", "idplayer")}</td>
                  <td>{playerName}</td>
                  <td>
                    <CountryWithFlag country={item.country} />
                  </td>
                  <td>{recordCounts[playerName] ?? 0}</td>
                </tr>
              );
            })}
            {paddingBottom > 0 && (
              <tr>
                <td colSpan={PLAYERS_COL_COUNT} style={{ height: paddingBottom, padding: 0, border: "none" }} />
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <p className="table-count-info">{rows.length} players</p>
    </div>
  );
}

function StaticTable({
  view,
  rows
}: {
  view: Exclude<PublicDataView, "records" | "players">;
  rows: DataRow[];
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
                <td><MapWithIcon name={item.nameMap ?? item.namemap} /></td>
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
                <td><VehicleWithIcon name={item.nameVehicle ?? item.namevehicle} /></td>
              </tr>
            ))}
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

  return (
    <TableFrame>
      <table>
        <tbody>
          <tr>
            <th>Setup ID</th>
            <th>Tuning Parts</th>
          </tr>
          {rows.map((item) => {
            const partNames: string[] = Array.isArray(item.parts)
              ? (item.parts as unknown[]).map((p) =>
                  typeof p === "object" && p !== null && "nameTuningPart" in p
                    ? asText((p as { nameTuningPart: unknown }).nameTuningPart)
                    : asText(p)
                ).filter(Boolean)
              : asText(item.parts).split(",").map((s) => s.trim()).filter(Boolean);
            return (
              <tr key={numeric(item, "idTuningSetup", "idtuningsetup")}>
                <td>{numeric(item, "idTuningSetup", "idtuningsetup")}</td>
                <td className="setup-parts-cell">
                  {partNames.length > 0
                    ? partNames.map((name) => <TuningPartWithIcon key={name} name={name} />)
                    : <span className="muted">—</span>}
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
  useBodyScrollLock();

  return (
    <div id="note-overlay" className="modal-overlay">
      <div className="modal-panel form-container" role="dialog" aria-modal="true" aria-labelledby="note-title">
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
  const [note, setNote] = useState("");
  const [isExporting, setIsExporting] = useState(false);
  const isMobile = useMediaQuery(MOBILE_BREAKPOINT);

  // ── Records view state ──────────────────────────────────────────────────────
  const [recordFilters, setRecordFilters] = useState<RecordFilters>(emptyRecordFilters);

  const recordsQuery = useInfiniteQuery({
    queryKey: ["records-paginated", recordFilters],
    queryFn: ({ pageParam }) => getRecordsPaginated(recordFilters, pageParam as number),
    initialPageParam: 0,
    getNextPageParam: (lastPage: PaginatedRecordsResponse, allPages: PaginatedRecordsResponse[]) => {
      if (!lastPage?.records) return undefined;
      const loaded = allPages.reduce((sum, p) => sum + (p.records?.length ?? 0), 0);
      return loaded < lastPage.total ? loaded : undefined;
    },
    enabled: view === "records"
  });

  const allRecords = useMemo(
    () => recordsQuery.data?.pages.flatMap((p) => p.records ?? []) ?? [],
    [recordsQuery.data]
  );
  const totalRecords = recordsQuery.data?.pages[0]?.total ?? 0;

  // Catalog data for filter dropdowns (small datasets, cached)
  const mapsData = useQuery({
    queryKey: ["public-data", "maps"],
    queryFn: () => getPublicData("maps"),
    enabled: view === "records"
  });
  const vehiclesData = useQuery({
    queryKey: ["public-data", "vehicles"],
    queryFn: () => getPublicData("vehicles"),
    enabled: view === "records"
  });
  const tuningPartsData = useQuery({
    queryKey: ["public-data", "tuning-parts"],
    queryFn: () => getPublicData("tuning-parts"),
    enabled: view === "records"
  });

  const mapOptions = useMemo(
    () => (mapsData.data ?? []).map((r) => asText(r.nameMap ?? r.namemap)).filter(Boolean).sort(),
    [mapsData.data]
  );
  const vehicleOptions = useMemo(
    () => (vehiclesData.data ?? []).map((r) => asText(r.nameVehicle ?? r.namevehicle)).filter(Boolean).sort(),
    [vehiclesData.data]
  );
  const tuningOptions = useMemo(
    () => (tuningPartsData.data ?? []).map((r) => asText(r.nameTuningPart ?? r.nametuningpart ?? r.name)).filter(Boolean).sort(),
    [tuningPartsData.data]
  );

  function patchRecordFilters(patch: Partial<RecordFilters>) {
    setRecordFilters((prev) => ({ ...prev, ...patch }));
  }

  async function handleExportCsv() {
    setIsExporting(true);
    try {
      const result = await exportRecords(recordFilters);
      if (result.records.length === 0) {
        window.alert("No records to export. Please check your filters.");
        return;
      }
      downloadCsv(result.records);
    } finally {
      setIsExporting(false);
    }
  }

  // ── Non-records views ───────────────────────────────────────────────────────
  const data = useQuery({
    queryKey: ["public-data", view],
    queryFn: () => getPublicData(view as Exclude<PublicDataView, "records">),
    enabled: view !== "records"
  });

  const rows = data.data ?? [];

  // Players: record_count now comes directly from the SQL query
  const playerRecordCounts = useMemo(() => {
    if (view !== "players") return {};
    const counts: Record<string, number> = {};
    rows.forEach((player) => {
      const name = asText(player.namePlayer ?? player.nameplayer);
      counts[name] = Number(player.recordCount ?? 0);
    });
    return counts;
  }, [view, rows]);

  const [visiblePlayers, setVisiblePlayers] = useState<DataRow[]>([]);
  const meta = viewMeta[view];

  return (
    <main className="data-page">
      <section className="page-hero page-hero--compact" aria-labelledby="data-view-title">
        <p className="eyebrow">{meta.eyebrow}</p>
        <h1 id="data-view-title">{meta.title}</h1>
        <p>{meta.description}</p>
      </section>

      {view === "records" && (
        <RecordsFilters
          filters={recordFilters}
          onChange={patchRecordFilters}
          mapOptions={mapOptions}
          vehicleOptions={vehicleOptions}
          tuningOptions={tuningOptions}
          onExport={handleExportCsv}
          isExporting={isExporting}
        />
      )}
      {view === "players" && data.data && (
        <PlayerFilters rows={rows} recordCounts={playerRecordCounts} onRowsChange={setVisiblePlayers} />
      )}

      <section id="data-container" className="data-section">
        <h2>{dataTypeByView[view].toUpperCase()}</h2>

        {/* ── Records view ── */}
        {view === "records" && (
          <>
            {recordsQuery.isLoading && <p className="loading-state">Loading records…</p>}
            {recordsQuery.isError && <p className="frontend-error">Error fetching records from server.</p>}
            {!recordsQuery.isLoading && allRecords.length === 0 && !recordsQuery.isError && (
              <p className="empty-state">No records match your filters.</p>
            )}
            {allRecords.length > 0 && (
              <VirtualRecordsTable
                rows={allRecords}
                total={totalRecords}
                hasNextPage={recordsQuery.hasNextPage}
                isFetchingNextPage={recordsQuery.isFetchingNextPage}
                onLoadMore={() => recordsQuery.fetchNextPage()}
                onNote={setNote}
                isMobile={isMobile}
              />
            )}
          </>
        )}

        {/* ── Players view ── */}
        {view === "players" && (
          <>
            {data.isLoading && <p className="loading-state">Loading data…</p>}
            {data.isError && <p className="frontend-error">Error fetching data from server.</p>}
            {data.data && visiblePlayers.length === 0 && <p className="empty-state">No players match your filters.</p>}
            {data.data && visiblePlayers.length > 0 && (
              <VirtualPlayersTable rows={visiblePlayers} recordCounts={playerRecordCounts} />
            )}
          </>
        )}

        {/* ── Other views ── */}
        {view !== "records" && view !== "players" && (
          <>
            {data.isLoading && <p className="loading-state">Loading data…</p>}
            {data.isError && <p className="frontend-error">Error fetching data from server.</p>}
            {data.data && (
              <StaticTable
                view={view as Exclude<PublicDataView, "records" | "players">}
                rows={rows}
              />
            )}
          </>
        )}
      </section>

      {note && <NoteModal note={note} onClose={() => setNote("")} />}
    </main>
  );
}
