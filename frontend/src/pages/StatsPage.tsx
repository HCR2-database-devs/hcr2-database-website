import { useEffect, useMemo, useRef, useState } from "react";
import type { MouseEvent, ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  asText,
  formatDistance,
  getCountryCode,
  MapWithIcon,
  TuningPartWithIcon,
  TuningPartsIcons,
  VehicleWithIcon
} from "../lib/legacyDisplay";
import { exportRecords } from "../services/publicData";
import { emptyRecordFilters } from "../types/api";
import type { DataRow } from "../types/api";

type ChartEntry = {
  label: string;
  value: number;
  accent?: string;
};

type CountrySlice = {
  country: string;
  count: number;
  endAngle: number;
  fraction: number;
  index: number;
  midAngle: number;
  startAngle: number;
};

type HoveredCountry = {
  country: string;
  count: number;
  x: number;
  y: number;
};

const specialMaps = ["Forest Trials", "Intense City", "Raging Winter"];
const chartVariables = ["--accent", "--chart-2", "--chart-3", "--chart-4", "--chart-5", "--chart-6"];
const tuningStatsSlots = Array.from({ length: 10 }, (_, index) => index);
const pieStartAngle = -0.5 * Math.PI;
const pieCanvasWidth = 500;
const pieCanvasHeight = 375;
const pieLabelThreshold = 0.12;
const pieCx = pieCanvasWidth / 2;
const pieCy = pieCanvasHeight / 2;
const pieRadius = Math.min(pieCanvasWidth, pieCanvasHeight) / 2 - 10;

function distance(row: DataRow) {
  return Number(row.distance ?? 0);
}

function adventureStars(row: DataRow) {
  const value = distance(row);
  return specialMaps.includes(asText(row.map_name)) ? (value >= 5000 ? 15000 : value * 3) : value >= 10000 ? 10000 : value;
}

function cssValue(name: string, fallback: string) {
  if (typeof window === "undefined") {
    return fallback;
  }
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;
}

function chartColor(index: number) {
  return `var(${chartVariables[index % chartVariables.length]})`;
}

function CountryFlag({ country }: { country: string }) {
  const code = getCountryCode(country);
  if (!code) {
    return null;
  }
  if (code === "question") {
    return <span className="country-flag">?</span>;
  }
  return <img className="country-flag" src={`https://flagcdn.com/20x15/${code}.png`} alt={`${country} flag`} />;
}

function TableFrame({ children }: { children: ReactNode }) {
  return (
    <div className="table-shell">
      <div className="table-scroll">{children}</div>
    </div>
  );
}

function ChartBars({ entries }: { entries: ChartEntry[] }) {
  const max = Math.max(...entries.map((entry) => entry.value), 1);
  if (entries.length === 0) {
    return <p className="empty-state">No statistics available.</p>;
  }
  return (
    <>
      {entries.map((entry, index) => (
        <div className="chart-bar" key={`${entry.label}-${index}`}>
          <span className="player-rank">{index + 1}.</span>
          <span className="player-name">{entry.label}</span>
          <div className="bar-wrap">
            <div
              className="bar-fill"
              style={{
                width: `${(entry.value / max) * 100}%`,
                backgroundColor: entry.accent ?? "var(--accent)"
              }}
            >
              <span className="bar-value">{formatDistance(entry.value)}</span>
            </div>
          </div>
        </div>
      ))}
    </>
  );
}

function countBy(rows: DataRow[], key: string) {
  const output: Record<string, number> = {};
  rows.forEach((row) => {
    const name = asText(row[key]) || "Unknown";
    output[name] = (output[name] ?? 0) + 1;
  });
  return output;
}

export function StatsPage() {
  const [vehicleSort, setVehicleSort] = useState("total-distance");
  const [mapSort, setMapSort] = useState("total-distance");
  const [hoveredCountry, setHoveredCountry] = useState<HoveredCountry | null>(null);
  const [showAllLabels, setShowAllLabels] = useState(false);
  const countryCanvas = useRef<HTMLCanvasElement | null>(null);
  const records = useQuery({
    queryKey: ["public-data", "records"],
    queryFn: () => exportRecords(emptyRecordFilters).then((r) => r.records)
  });

  const rows = records.data ?? [];
  const stats = useMemo(() => {
    const vehicleTotals: Record<string, number> = {};
    const vehicleLongest: Record<string, { distance: number; map: string }> = {};
    const mapTotals: Record<string, { distance: number; count: number }> = {};
    const vehicleStars: Record<string, number> = {};
    const mapStars: Record<string, number> = {};
    const tuningParts: Record<string, number> = {};
    const tuningSetups: Record<string, { count: number; parts: string }> = {};
    const mapPlacements: Record<string, DataRow[]> = {};

    rows.forEach((row) => {
      const vehicle = asText(row.vehicle_name) || "Unknown";
      const map = asText(row.map_name) || "Unknown";
      const value = distance(row);
      vehicleTotals[vehicle] = (vehicleTotals[vehicle] ?? 0) + value;
      vehicleStars[vehicle] = (vehicleStars[vehicle] ?? 0) + adventureStars(row);
      mapStars[map] = (mapStars[map] ?? 0) + adventureStars(row);
      mapTotals[map] = mapTotals[map] ?? { distance: 0, count: 0 };
      mapTotals[map].distance += value;
      mapTotals[map].count += 1;
      mapPlacements[map] = [...(mapPlacements[map] ?? []), row];
      if (!vehicleLongest[vehicle] || value > vehicleLongest[vehicle].distance) {
        vehicleLongest[vehicle] = { distance: value, map };
      }
      asText(row.tuning_parts)
        .split(",")
        .map((part) => part.trim())
        .filter(Boolean)
        .forEach((part) => {
          tuningParts[part] = (tuningParts[part] ?? 0) + 1;
        });
      if (row.idTuningSetup) {
        const setupKey = `Setup ${row.idTuningSetup}`;
        tuningSetups[setupKey] = tuningSetups[setupKey] ?? { count: 0, parts: asText(row.tuning_parts) };
        tuningSetups[setupKey].count += 1;
      }
    });

    const placements: Record<string, number[]> = {};
    Object.values(mapPlacements).forEach((mapRows) => {
      [...mapRows]
        .sort((a, b) => distance(b) - distance(a))
        .forEach((row, index) => {
          const vehicle = asText(row.vehicle_name) || "Unknown";
          placements[vehicle] = [...(placements[vehicle] ?? []), index + 1];
        });
    });

    return {
      countryCounts: countBy(rows, "player_country"),
      mapStars,
      mapTotals,
      placements,
      playerCounts: countBy(rows, "player_name"),
      tuningParts,
      tuningSetups,
      vehicleLongest,
      vehicleStars,
      vehicleTotals
    };
  }, [rows]);

  const countryEntries = useMemo(() => {
    let otherCount = 0;
    const grouped: Record<string, number> = {};
    Object.entries(stats.countryCounts).forEach(([country, count]) => {
      if (count <= 5) {
        otherCount += count;
      } else {
        grouped[country] = count;
      }
    });
    if (otherCount > 0) {
      grouped["Other countries"] = otherCount;
    }
    return Object.entries(grouped).sort((a, b) => b[1] - a[1]);
  }, [stats.countryCounts]);

  const countrySlices = useMemo<CountrySlice[]>(() => {
    const total = countryEntries.reduce((sum, [, count]) => sum + count, 0) || 1;
    let currentAngle = pieStartAngle;
    return countryEntries.map(([country, count], index) => {
      const fraction = count / total;
      const sliceAngle = fraction * Math.PI * 2;
      const startAngle = currentAngle;
      const endAngle = currentAngle + sliceAngle;
      currentAngle = endAngle;
      return {
        country,
        count,
        endAngle,
        fraction,
        index,
        midAngle: startAngle + sliceAngle / 2,
        startAngle
      };
    });
  }, [countryEntries]);

  useEffect(() => {
    const canvas = countryCanvas.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx || countrySlices.length === 0) {
      return;
    }
    const surface = cssValue("--surface", "#ffffff");
    const border = cssValue("--surface", "#ffffff");
    const palette = chartVariables.map((item) => cssValue(item, "#0f766e"));
    ctx.fillStyle = surface;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const radius = Math.min(canvas.width, canvas.height) / 2 - 10;
    countrySlices.forEach((slice) => {
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, radius, slice.startAngle, slice.endAngle);
      ctx.closePath();
      ctx.fillStyle = palette[slice.index % palette.length];
      ctx.fill();
      ctx.strokeStyle = border;
      ctx.lineWidth = 2;
      ctx.stroke();
    });
  }, [countrySlices]);

  function countrySliceAtPoint(x: number, y: number) {
    const cx = pieCanvasWidth / 2;
    const cy = pieCanvasHeight / 2;
    const radius = Math.min(pieCanvasWidth, pieCanvasHeight) / 2 - 10;
    const dx = x - cx;
    const dy = y - cy;
    if (Math.sqrt(dx * dx + dy * dy) > radius) {
      return null;
    }

    let angle = Math.atan2(dy, dx);
    if (angle < pieStartAngle) {
      angle += Math.PI * 2;
    }
    return countrySlices.find((slice) => angle >= slice.startAngle && angle <= slice.endAngle) ?? null;
  }

  function handleCountryPieMove(event: MouseEvent<HTMLCanvasElement>) {
    const canvas = event.currentTarget;
    const bounds = canvas.getBoundingClientRect();
    const x = ((event.clientX - bounds.left) / bounds.width) * pieCanvasWidth;
    const y = ((event.clientY - bounds.top) / bounds.height) * pieCanvasHeight;
    const slice = countrySliceAtPoint(x, y);
    if (!slice || slice.fraction >= pieLabelThreshold) {
      setHoveredCountry(null);
      return;
    }
    setHoveredCountry({
      country: slice.country,
      count: slice.count,
      x: event.clientX - bounds.left,
      y: event.clientY - bounds.top
    });
  }

  const vehicleTableRows = useMemo(() => {
    const allVehicles = new Set([
      ...Object.keys(stats.vehicleTotals),
      ...Object.keys(stats.vehicleLongest),
      ...Object.keys(stats.vehicleStars),
      ...Object.keys(stats.placements)
    ]);
    const rows = Array.from(allVehicles).map((vehicle) => {
      const placementValues = stats.placements[vehicle] ?? [];
      return {
        vehicle,
        totalDistance: stats.vehicleTotals[vehicle] ?? 0,
        longestDistance: stats.vehicleLongest[vehicle]?.distance ?? 0,
        longestMap: stats.vehicleLongest[vehicle]?.map ?? "",
        stars: stats.vehicleStars[vehicle] ?? 0,
        avgPlacement: placementValues.length > 0
          ? placementValues.reduce((sum, v) => sum + v, 0) / placementValues.length
          : null,
        bestPlacement: placementValues.length > 0 ? Math.min(...placementValues) : null,
        worstPlacement: placementValues.length > 0 ? Math.max(...placementValues) : null
      };
    });
    if (vehicleSort === "longest-distance") return rows.sort((a, b) => b.longestDistance - a.longestDistance);
    if (vehicleSort === "adventure-stars") return rows.sort((a, b) => b.stars - a.stars);
    if (vehicleSort === "avg-placement") return rows.sort((a, b) => (a.avgPlacement ?? Infinity) - (b.avgPlacement ?? Infinity));
    if (vehicleSort === "highest-placement") return rows.sort((a, b) => (a.bestPlacement ?? Infinity) - (b.bestPlacement ?? Infinity));
    if (vehicleSort === "lowest-placement") return rows.sort((a, b) => (b.worstPlacement ?? 0) - (a.worstPlacement ?? 0));
    return rows.sort((a, b) => b.totalDistance - a.totalDistance);
  }, [stats.placements, stats.vehicleLongest, stats.vehicleStars, stats.vehicleTotals, vehicleSort]);

  const mapTableRows = useMemo(() => {
    const rows = Object.entries(stats.mapTotals).map(([map, item]) => ({
      map,
      count: item.count,
      distance: item.distance,
      avgDistance: item.distance / Math.max(item.count, 1),
      stars: stats.mapStars[map] ?? 0
    }));
    if (mapSort === "total-records") return rows.sort((a, b) => b.count - a.count);
    if (mapSort === "avg-distance") return rows.sort((a, b) => b.avgDistance - a.avgDistance);
    if (mapSort === "adventure-stars") return rows.sort((a, b) => b.stars - a.stars);
    return rows.sort((a, b) => b.distance - a.distance);
  }, [stats.mapTotals, stats.mapStars, mapSort]);

  const playerEntries = Object.entries(stats.playerCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([label, value]) => ({ label, value, accent: "var(--chart-3)" }));
  const mostUsedParts = Object.entries(stats.tuningParts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);
  const mostUsedSetups = Object.entries(stats.tuningSetups)
    .sort((a, b) => b[1].count - a[1].count)
    .slice(0, 10);
  const totalDistance = rows.reduce((sum, row) => sum + distance(row), 0);
  const summary = [
    { label: "Total Records", value: rows.length },
    { label: "Total Distance", value: formatDistance(totalDistance) },
    { label: "Average Distance", value: formatDistance(totalDistance / Math.max(rows.length, 1), 2) },
    { label: "Unique Players", value: new Set(rows.map((row) => asText(row.player_name))).size },
    { label: "Unique Vehicles", value: new Set(rows.map((row) => asText(row.vehicle_name))).size },
    { label: "Unique Maps", value: new Set(rows.map((row) => asText(row.map_name))).size }
  ];

  return (
    <main id="stats-container" className="stats-page">
      <section className="page-hero page-hero--compact" aria-labelledby="stats-title">
        <p className="eyebrow">Analytics</p>
        <h1 id="stats-title">Detailed Statistics</h1>
        <p>Records, vehicle performance, map distribution and tuning usage in one view.</p>
      </section>

      {records.isLoading && <p className="loading-state">Loading stats...</p>}
      {records.isError && <p className="frontend-error">Error fetching stats data from server.</p>}
      {records.data && (
        <>
          <section className="stats-summary" aria-label="Overall records summary">
            {summary.map((item) => (
              <div className="stat-box" key={item.label}>
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </div>
            ))}
          </section>

          <section className="stats-section">
            <div className="section-toolbar">
              <h2>Vehicle Statistics</h2>
              <select id="vehicle-sort-select" value={vehicleSort} onChange={(event) => setVehicleSort(event.target.value)}>
                <option value="total-distance">Total Distance</option>
                <option value="longest-distance">Longest Distance</option>
                <option value="adventure-stars">Adventure Stars</option>
                <option value="avg-placement">Average Placement</option>
                <option value="highest-placement">Highest Placement</option>
                <option value="lowest-placement">Lowest Placement</option>
              </select>
            </div>
            <TableFrame>
              <table id="vehicle-stats-table" style={{ width: "100%" }}>
                <tbody>
                  <tr>
                    <th>Rank</th>
                    <th>Vehicle</th>
                    <th>Total Distance</th>
                    <th>Longest Distance</th>
                    <th>Best Map</th>
                    <th>Adventure Stars</th>
                    <th>Avg Placement</th>
                    <th>Best Placement</th>
                    <th>Worst Placement</th>
                  </tr>
                  {vehicleTableRows.map((row, index) => (
                    <tr key={row.vehicle}>
                      <td>{index + 1}</td>
                      <td><VehicleWithIcon name={row.vehicle} /></td>
                      <td>{formatDistance(row.totalDistance)}</td>
                      <td>{formatDistance(row.longestDistance)}</td>
                      <td>{row.longestMap ? <MapWithIcon name={row.longestMap} /> : "-"}</td>
                      <td>{formatDistance(row.stars)}</td>
                      <td>{row.avgPlacement !== null ? row.avgPlacement.toFixed(2) : "-"}</td>
                      <td>{row.bestPlacement !== null ? row.bestPlacement : "-"}</td>
                      <td>{row.worstPlacement !== null ? row.worstPlacement : "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableFrame>
          </section>

          <section className="stats-section">
            <div className="section-toolbar">
              <h2>Records by Country</h2>
              <button
                type="button"
                className="filter-btn"
                onClick={() => setShowAllLabels((v) => !v)}
              >
                {showAllLabels ? "Fewer labels" : "See all labels"}
              </button>
            </div>
            <div className="country-records-layout">
              <div className={`country-pie-chart${showAllLabels ? " country-pie-chart--expanded" : ""}`}>
                <canvas
                  ref={countryCanvas}
                  id="country-pie"
                  width={pieCanvasWidth}
                  height={pieCanvasHeight}
                  aria-label="Pie chart showing records by country"
                  onMouseLeave={() => setHoveredCountry(null)}
                  onMouseMove={showAllLabels ? undefined : handleCountryPieMove}
                />

                {/* SVG overlay: connector lines for external labels */}
                {showAllLabels && (
                  <svg
                    className="country-pie-connectors"
                    viewBox={`0 0 ${pieCanvasWidth} ${pieCanvasHeight}`}
                    aria-hidden="true"
                  >
                    {countrySlices
                      .filter((s) => s.fraction < pieLabelThreshold)
                      .map((s) => {
                        const ex = pieCx + Math.cos(s.midAngle) * pieRadius;
                        const ey = pieCy + Math.sin(s.midAngle) * pieRadius;
                        const bx = pieCx + Math.cos(s.midAngle) * (pieRadius + 22);
                        const by = pieCy + Math.sin(s.midAngle) * (pieRadius + 22);
                        const onRight = Math.cos(s.midAngle) >= 0;
                        const lx = bx + (onRight ? 30 : -30);
                        return (
                          <g key={s.country}>
                            <polyline
                              points={`${ex},${ey} ${bx},${by} ${lx},${by}`}
                              fill="none"
                              stroke="var(--muted)"
                              strokeWidth="1"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            />
                            <circle cx={ex} cy={ey} r={2.5} fill={chartColor(s.index)} />
                          </g>
                        );
                      })}
                  </svg>
                )}

                {/* Internal labels — large slices only */}
                {countrySlices
                  .filter((s) => s.fraction >= pieLabelThreshold)
                  .map((s) => {
                    const labelX = 50 + Math.cos(s.midAngle) * 28;
                    const labelY = 50 + Math.sin(s.midAngle) * 38;
                    return (
                      <div
                        className="country-slice-label"
                        key={s.country}
                        style={{ left: `${labelX}%`, top: `${labelY}%` }}
                      >
                        <CountryFlag country={s.country} />
                        <span>{s.country}</span>
                      </div>
                    );
                  })}

                {/* External labels — small slices, "see all" mode */}
                {showAllLabels &&
                  countrySlices
                    .filter((s) => s.fraction < pieLabelThreshold)
                    .map((s) => {
                      const bx = pieCx + Math.cos(s.midAngle) * (pieRadius + 22);
                      const by = pieCy + Math.sin(s.midAngle) * (pieRadius + 22);
                      const onRight = Math.cos(s.midAngle) >= 0;
                      const lx = bx + (onRight ? 30 : -30);
                      const labelLeft = (lx / pieCanvasWidth) * 100;
                      const labelTop = (by / pieCanvasHeight) * 100;
                      return (
                        <div
                          key={s.country}
                          className={`country-slice-label country-slice-label--external${onRight ? "" : " country-slice-label--left"}`}
                          style={{ left: `${labelLeft}%`, top: `${labelTop}%` }}
                        >
                          <CountryFlag country={s.country} />
                          <span>{s.country}</span>
                        </div>
                      );
                    })}

                {/* Hover tooltip — normal mode only */}
                {!showAllLabels && hoveredCountry && (
                  <div className="country-pie-tooltip" style={{ left: hoveredCountry.x, top: hoveredCountry.y }}>
                    <CountryFlag country={hoveredCountry.country} />
                    <span>
                      {hoveredCountry.country} ({hoveredCountry.count})
                    </span>
                  </div>
                )}
              </div>
              <div className="country-player-ranking">
                <h3>Top 10 Players by Record Count</h3>
                <div className="chart-container">
                  <ChartBars entries={playerEntries} />
                </div>
              </div>
            </div>
          </section>

          <section className="stats-section">
            <div className="section-toolbar">
              <h2>Map Statistics</h2>
              <select value={mapSort} onChange={(event) => setMapSort(event.target.value)}>
                <option value="total-distance">Total Distance</option>
                <option value="total-records">Total Records</option>
                <option value="avg-distance">Average Distance</option>
                <option value="adventure-stars">Adventure Stars</option>
              </select>
            </div>
            <TableFrame>
              <table style={{ width: "100%" }}>
                <tbody>
                  <tr>
                    <th>Map Name</th>
                    <th>Total Records</th>
                    <th>Total Distance</th>
                    <th>Average Distance</th>
                    <th>Adventure Stars</th>
                  </tr>
                  {mapTableRows.map((row) => (
                    <tr key={row.map}>
                      <td>
                        <MapWithIcon name={row.map} />
                      </td>
                      <td>{row.count}</td>
                      <td>{formatDistance(row.distance)}</td>
                      <td>{formatDistance(row.avgDistance, 2)}</td>
                      <td>{formatDistance(row.stars)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableFrame>
          </section>

          <section className="stats-section">
            <h2>Tuning Part Statistics</h2>
            <div className="tuning-stats">
              <div className="stat-subsection">
                <h3>Most Used Individual Parts</h3>
                <TableFrame>
                  <table className="stats-usage-table">
                    <tbody>
                      <tr>
                        <th>Rank</th>
                        <th>Part</th>
                        <th>Usage Count</th>
                      </tr>
                      {tuningStatsSlots.map((slot) => {
                        const item = mostUsedParts[slot];
                        return (
                          <tr key={item?.[0] ?? `empty-part-${slot}`} className={!item ? "is-empty-row" : undefined}>
                            <td>{item ? slot + 1 : ""}</td>
                            <td>{item ? <TuningPartWithIcon name={item[0]} /> : ""}</td>
                            <td>{item ? item[1] : ""}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </TableFrame>
              </div>
              <div className="stat-subsection">
                <h3>Most Used Setups</h3>
                <TableFrame>
                  <table className="stats-usage-table">
                    <tbody>
                      <tr>
                        <th>Rank</th>
                        <th>Setup</th>
                        <th>Usage Count</th>
                      </tr>
                      {tuningStatsSlots.map((slot) => {
                        const item = mostUsedSetups[slot];
                        return (
                          <tr key={item?.[0] ?? `empty-setup-${slot}`} className={!item ? "is-empty-row" : undefined}>
                            <td>{item ? slot + 1 : ""}</td>
                            <td>
                              {item ? (
                                <span className="setup-icons-only" aria-label={item[1].parts}>
                                  <TuningPartsIcons parts={item[1].parts} />
                                </span>
                              ) : (
                                ""
                              )}
                            </td>
                            <td>{item ? item[1].count : ""}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </TableFrame>
              </div>
            </div>
          </section>
        </>
      )}
    </main>
  );
}
