import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { asText, formatDistance, MapWithIcon, TuningPartWithIcon, VehicleWithIcon } from "../lib/legacyDisplay";
import { getPublicData } from "../services/publicData";
import type { DataRow } from "../types/api";

type ChartEntry = {
  label: string;
  value: number;
  accent?: string;
};

const specialMaps = ["Forest Trials", "Intense City", "Raging Winter"];

function distance(row: DataRow) {
  return Number(row.distance ?? 0);
}

function adventureStars(row: DataRow) {
  const value = distance(row);
  return specialMaps.includes(asText(row.map_name)) ? (value >= 5000 ? 15000 : value * 3) : value >= 10000 ? 10000 : value;
}

function ChartBars({ entries }: { entries: ChartEntry[] }) {
  const max = Math.max(...entries.map((entry) => entry.value), 1);
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
                background: entry.accent
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
  const countryCanvas = useRef<HTMLCanvasElement | null>(null);
  const records = useQuery({
    queryKey: ["public-data", "records"],
    queryFn: () => getPublicData("records")
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

  useEffect(() => {
    const canvas = countryCanvas.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx || countryEntries.length === 0) {
      return;
    }
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    const total = countryEntries.reduce((sum, [, count]) => sum + count, 0) || 1;
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const radius = Math.min(canvas.width, canvas.height) / 2 - 10;
    let startAngle = -0.5 * Math.PI;
    countryEntries.forEach(([, count], index) => {
      const slice = (count / total) * Math.PI * 2;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, radius, startAngle, startAngle + slice);
      ctx.closePath();
      ctx.fillStyle = `hsl(${(index * 137.508) % 360},70%,50%)`;
      ctx.fill();
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 2;
      ctx.stroke();
      startAngle += slice;
    });
  }, [countryEntries]);

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
    .map(([label, value]) => ({ label, value, accent: "linear-gradient(to right, #85a728ff, #28a745)" }));
  const mapStarEntries = Object.entries(stats.mapStars)
    .sort((a, b) => b[1] - a[1])
    .map(([label, value]) => ({ label, value, accent: "linear-gradient(to right, #4287f5ff, #00d4ff)" }));
  const playerEntries = Object.entries(stats.playerCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([label, value]) => ({ label, value }));
  const mapEntries = Object.entries(stats.mapTotals).sort((a, b) => b[1].distance - a[1].distance);
  const totalDistance = rows.reduce((sum, row) => sum + distance(row), 0);

  return (
    <section id="stats-container">
      <h2>DETAILED STATISTICS</h2>
      {records.isLoading && <p>Loading stats...</p>}
      {records.isError && <p style={{ color: "red" }}>Error fetching stats data from server.</p>}
      {records.data && (
        <>
          <div className="stats-section">
            <div className="vehicle-header" style={{ position: "relative", display: "flex", alignItems: "center", justifyContent: "flex-end", marginBottom: 15 }}>
              <h3 className="vehicle-title" style={{ position: "absolute", left: "50%", transform: "translateX(-50%)", margin: 0 }}>
                Vehicle Statistics
              </h3>
              <div className="vehicle-select-wrap" style={{ marginLeft: "auto" }}>
                <select
                  id="vehicle-sort-select"
                  value={vehicleSort}
                  onChange={(event) => setVehicleSort(event.target.value)}
                  style={{ padding: "8px 12px", borderRadius: 4, border: "1px solid #ccc", fontSize: 14 }}
                >
                  <option value="total-distance">Total Distance</option>
                  <option value="longest-distance">Longest Distance</option>
                  <option value="avg-placement">Average Placement </option>
                  <option value="highest-placement">Highest Placement</option>
                  <option value="lowest-placement">Lowest Placement</option>
                </select>
              </div>
            </div>
            <div id="vehicle-stats-table">
              <table>
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
            </div>
          </div>

          <div className="stats-section">
            <h3>Vehicle Rankings by Adventure Stars</h3>
            <div className="chart-container stars-chart">
              <ChartBars entries={vehicleStarEntries} />
              <div className="total-stars">⭐ Total Adventure Stars : </div>
              <div className="total-stars-value">{formatDistance(vehicleStarEntries.reduce((sum, entry) => sum + entry.value, 0))}</div>
            </div>
          </div>

          <div className="stats-section">
            <h3>Top 10 Players by Record Count</h3>
            <div className="chart-container players-chart">
              <ChartBars entries={playerEntries} />
            </div>
          </div>

          <div className="stats-section">
            <h3>Records by Country</h3>
            <div className="pie-container">
              <canvas ref={countryCanvas} id="country-pie" width="500" height="375" aria-label="Pie chart showing records by country" />
              <div className="pie-legend">
                {countryEntries.map(([country, count], index) => (
                  <div className="legend-item" key={country}>
                    <span className="legend-color" style={{ background: `hsl(${(index * 137.508) % 360},70%,50%)` }} />
                    <span className="legend-label">
                      {country} ({count})
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="stats-section">
            <h3>Map Statistics</h3>
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
          </div>

          <div className="stats-section">
            <h3>Map Rankings by Adventure Stars</h3>
            <div className="chart-container stars-chart">
              <ChartBars entries={mapStarEntries} />
              <div className="total-stars">⭐ Total Adventure Stars : </div>
              <div className="total-stars-value">{formatDistance(mapStarEntries.reduce((sum, entry) => sum + entry.value, 0))}</div>
            </div>
          </div>

          <div className="stats-section">
            <h3>Tuning Part Statistics</h3>
            <div className="tuning-stats">
              <div className="stat-subsection">
                <h4>Most Used Individual Parts</h4>
                <table>
                  <tbody>
                    <tr>
                      <th>Rank</th>
                      <th>Part</th>
                      <th>Usage Count</th>
                    </tr>
                    {Object.entries(stats.tuningParts)
                      .sort((a, b) => b[1] - a[1])
                      .slice(0, 10)
                      .map(([part, count], index) => (
                        <tr key={part}>
                          <td>{index + 1}</td>
                          <td>
                            <TuningPartWithIcon name={part} />
                          </td>
                          <td>{count}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
              <div className="stat-subsection">
                <h4>Most Used Setups</h4>
                <table>
                  <tbody>
                    <tr>
                      <th>Rank</th>
                      <th>Setup</th>
                      <th>Usage Count</th>
                    </tr>
                    {Object.entries(stats.tuningSetups)
                      .sort((a, b) => b[1].count - a[1].count)
                      .slice(0, 10)
                      .map(([setup, item], index) => (
                        <tr key={setup}>
                          <td>{index + 1}</td>
                          <td>{setup}{item.parts ? `: ${item.parts}` : ""}</td>
                          <td>{item.count}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="stats-section">
            <h3>Overall Statistics</h3>
            <div className="overall-stats">
              <div className="stat-box"><strong>Total Records:</strong> {rows.length}</div>
              <div className="stat-box"><strong>Total Distance:</strong> {formatDistance(totalDistance)}</div>
              <div className="stat-box"><strong>Average Distance:</strong> {formatDistance(totalDistance / Math.max(rows.length, 1), 2)}</div>
              <div className="stat-box"><strong>Unique Players:</strong> {new Set(rows.map((row) => asText(row.player_name))).size}</div>
              <div className="stat-box"><strong>Unique Vehicles:</strong> {new Set(rows.map((row) => asText(row.vehicle_name))).size}</div>
              <div className="stat-box"><strong>Unique Maps:</strong> {new Set(rows.map((row) => asText(row.map_name))).size}</div>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
