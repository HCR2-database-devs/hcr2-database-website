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
  const [hoveredCountry, setHoveredCountry] = useState<HoveredCountry | null>(null);
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
    if (vehicleSort === "longest-distance") {
      return Object.entries(stats.vehicleLongest)
        .sort((a, b) => b[1].distance - a[1].distance)
        .map(([vehicle, item]) => ({ vehicle, value: item.distance, map: item.map }));
    }
    if (vehicleSort === "avg-placement") {
      return Object.entries(stats.placements)
        .map(([vehicle, values]) => ({
          vehicle,
          value: values.reduce((sum, item) => sum + item, 0) / Math.max(values.length, 1)
        }))
        .sort((a, b) => a.value - b.value);
    }
    if (vehicleSort === "highest-placement") {
      return Object.entries(stats.placements)
        .map(([vehicle, values]) => ({ vehicle, value: Math.min(...values) }))
        .sort((a, b) => a.value - b.value);
    }
    if (vehicleSort === "lowest-placement") {
      return Object.entries(stats.placements)
        .map(([vehicle, values]) => ({ vehicle, value: Math.max(...values) }))
        .sort((a, b) => b.value - a.value);
    }
    return Object.entries(stats.vehicleTotals)
      .sort((a, b) => b[1] - a[1])
      .map(([vehicle, value]) => ({ vehicle, value }));
  }, [stats.placements, stats.vehicleLongest, stats.vehicleTotals, vehicleSort]);

  const vehicleStarEntries = Object.entries(stats.vehicleStars)
    .sort((a, b) => b[1] - a[1])
    .map(([label, value]) => ({ label, value, accent: "var(--accent)" }));
  const mapStarEntries = Object.entries(stats.mapStars)
    .sort((a, b) => b[1] - a[1])
    .map(([label, value]) => ({ label, value, accent: "var(--chart-2)" }));
  const playerEntries = Object.entries(stats.playerCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([label, value]) => ({ label, value, accent: "var(--chart-3)" }));
  const mapEntries = Object.entries(stats.mapTotals).sort((a, b) => b[1].distance - a[1].distance);
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
                <option value="avg-placement">Average Placement</option>
                <option value="highest-placement">Highest Placement</option>
                <option value="lowest-placement">Lowest Placement</option>
              </select>
            </div>
            <TableFrame>
              <table id="vehicle-stats-table">
                <tbody>
                  <tr>
                    <th>Rank</th>
                    <th>Vehicle Name</th>
                    <th>{vehicleSort === "longest-distance" ? "Longest Distance" : vehicleSort.includes("placement") ? "Placement" : "Total Distance"}</th>
                    {vehicleSort === "longest-distance" && <th>Map</th>}
                  </tr>
                  {vehicleTableRows.map((row, index) => (
                    <tr key={row.vehicle}>
                      <td>{index + 1}</td>
                      <td>
                        <VehicleWithIcon name={row.vehicle} />
                      </td>
                      <td>{vehicleSort.includes("placement") ? row.value.toFixed(2) : formatDistance(row.value)}</td>
                      {"map" in row && (
                        <td>
                          <MapWithIcon name={row.map} />
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableFrame>
          </section>

          <section className="stats-section">
            <h2>Vehicle Adventure Stars</h2>
            <div className="chart-container">
              <ChartBars entries={vehicleStarEntries} />
              <div className="total-stars">
                <span>Total Adventure Stars</span>
                <strong>{formatDistance(vehicleStarEntries.reduce((sum, entry) => sum + entry.value, 0))}</strong>
              </div>
            </div>
          </section>

          <section className="stats-section">
            <h2>Records by Country</h2>
            <div className="country-records-layout">
              <div className="country-pie-chart">
                <canvas
                  ref={countryCanvas}
                  id="country-pie"
                  width={pieCanvasWidth}
                  height={pieCanvasHeight}
                  aria-label="Pie chart showing records by country"
                  onMouseLeave={() => setHoveredCountry(null)}
                  onMouseMove={handleCountryPieMove}
                />
                {countrySlices
                  .filter((slice) => slice.fraction >= pieLabelThreshold)
                  .map((slice) => {
                    const labelX = 50 + Math.cos(slice.midAngle) * 28;
                    const labelY = 50 + Math.sin(slice.midAngle) * 38;
                    return (
                      <div
                        className="country-slice-label"
                        key={slice.country}
                        style={{ left: `${labelX}%`, top: `${labelY}%` }}
                      >
                        <CountryFlag country={slice.country} />
                        <span>{slice.country}</span>
                      </div>
                    );
                  })}
                {hoveredCountry && (
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
            <h2>Map Statistics</h2>
            <TableFrame>
              <table>
                <tbody>
                  <tr>
                    <th>Map Name</th>
                    <th>Total Records</th>
                    <th>Total Distance</th>
                    <th>Average Distance</th>
                  </tr>
                  {mapEntries.map(([map, item]) => (
                    <tr key={map}>
                      <td>
                        <MapWithIcon name={map} />
                      </td>
                      <td>{item.count}</td>
                      <td>{formatDistance(item.distance)}</td>
                      <td>{formatDistance(item.distance / item.count, 2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableFrame>
          </section>

          <section className="stats-section">
            <h2>Map Adventure Stars</h2>
            <div className="chart-container">
              <ChartBars entries={mapStarEntries} />
              <div className="total-stars">
                <span>Total Adventure Stars</span>
                <strong>{formatDistance(mapStarEntries.reduce((sum, entry) => sum + entry.value, 0))}</strong>
              </div>
            </div>
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
