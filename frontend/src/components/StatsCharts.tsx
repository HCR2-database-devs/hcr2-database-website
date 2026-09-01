import { useMemo, useState } from "react";
import type { MouseEvent } from "react";

const WIDTH = 640;
const HEIGHT = 280;
const PAD_LEFT = 8;
const PAD_RIGHT = 24;
const PAD_TOP = 18;
const PAD_BOTTOM = 34;

const chartSegments = [
  "--accent",
  "--chart-2",
  "--chart-3",
  "--chart-4",
  "--chart-5",
  "--chart-6"
];

type LinePoint = { x: number; y: number };

export type LineChartPoint = {
  label: string;
  value: number;
  detail?: string;
};

type LineChartProps = {
  data: LineChartPoint[];
  height?: number;
  width?: number;
  color?: string;
};

function niceCeil(value: number) {
  if (value <= 0) return 1;
  const magnitude = Math.pow(10, Math.floor(Math.log10(value)));
  const normalized = value / magnitude;
  const nice = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  return nice * magnitude;
}

export function LineChart({ data, height = HEIGHT, width = WIDTH, color }: LineChartProps) {
  const [hover, setHover] = useState<{ index: number; x: number; y: number } | null>(null);
  const seriesColor = color ?? "var(--accent)";

  const geometry = useMemo(() => {
    const count = data.length;
    if (count === 0) return null;
    const innerWidth = width - PAD_LEFT - PAD_RIGHT;
    const innerHeight = height - PAD_TOP - PAD_BOTTOM;
    const maxVal = niceCeil(Math.max(...data.map((d) => d.value), 1));

    const points: LinePoint[] = data.map((d, index) => {
      const x = count === 1 ? PAD_LEFT + innerWidth / 2 : PAD_LEFT + (index / (count - 1)) * innerWidth;
      const y = PAD_TOP + innerHeight - (d.value / maxVal) * innerHeight;
      return { x, y };
    });

    const path = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(" ");
    const areaPath = `${path} L${points[points.length - 1].x.toFixed(2)},${(PAD_TOP + innerHeight).toFixed(
      2
    )} L${points[0].x.toFixed(2)},${(PAD_TOP + innerHeight).toFixed(2)} Z`;

    const grid = Array.from({ length: 5 }, (_, i) => {
      const fraction = i / 4;
      const value = maxVal - fraction * maxVal;
      const y = PAD_TOP + fraction * innerHeight;
      return { y, value };
    });

    return { points, path, areaPath, grid, maxVal, innerWidth, innerHeight };
  }, [data, width, height]);

  if (!geometry) {
    return <p className="empty-state">Not enough data to draw a chart.</p>;
  }

  const gridColor = "rgba(95, 232, 255, 0.18)";
  const labelColor = "var(--muted)";

  function handleMove(event: MouseEvent<SVGSVGElement>) {
    const svg = event.currentTarget;
    const bounds = svg.getBoundingClientRect();
    const scaleX = width / bounds.width;
    const scaleY = height / bounds.height;
    const rawX = (event.clientX - bounds.left) * scaleX;
    const rawY = (event.clientY - bounds.top) * scaleY;
    let nearest = 0;
    let nearestDist = Infinity;
    geometry.points.forEach((p, i) => {
      const dist = Math.hypot(p.x - rawX, p.y - rawY);
      if (dist < nearestDist) {
        nearestDist = dist;
        nearest = i;
      }
    });
    setHover({
      index: nearest,
      x: geometry.points[nearest].x * scaleX,
      y: geometry.points[nearest].y * scaleY
    });
  }

  return (
    <div className="line-chart-wrap">
      <div className="line-chart-hover" aria-hidden="true">
        {hover && (
          <div
            className="line-chart-tooltip"
            style={{
              left: hover.x,
              top: hover.y,
              transform: "translate(12px, -50%)"
            }}
          >
            <span className="line-chart-tooltip-label">{data[hover.index].label}</span>
            <strong>{data[hover.index].detail ?? data[hover.index].value.toLocaleString()}</strong>
          </div>
        )}
      </div>
      <svg
        className="line-chart"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="Line chart"
        width="100%"
        height="auto"
        onMouseMove={handleMove}
        onMouseLeave={() => setHover(null)}
      >
        {geometry.grid.map((line) => (
          <g key={line.value}>
            <line
              x1={PAD_LEFT}
              x2={width - PAD_RIGHT}
              y1={line.y}
              y2={line.y}
              stroke={gridColor}
              strokeWidth={1}
              strokeDasharray="4 5"
            />
            <text
              x={width - PAD_RIGHT + 4}
              y={line.y + 3.5}
              fill={labelColor}
              fontSize={10}
              textAnchor="start"
            >
              {line.value >= 1000 ? `${(line.value / 1000).toFixed(line.value % 1000 === 0 ? 0 : 1)}k` : line.value}
            </text>
          </g>
        ))}
        <path d={geometry.areaPath} fill={seriesColor} opacity={0.18} stroke="none" />
        <path d={geometry.path} fill="none" stroke={seriesColor} strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" />
        {geometry.points.map((p, i) => (
          <circle
            key={`${data[i].label}-${i}`}
            cx={p.x}
            cy={p.y}
            r={hover && hover.index === i ? 5 : 3.5}
            fill={seriesColor}
            stroke="var(--surface)"
            strokeWidth={1.5}
            style={{ cursor: "pointer", transition: "r 120ms ease" }}
          />
        ))}
        {hover && (
          <line
            x1={geometry.points[hover.index].x}
            x2={geometry.points[hover.index].x}
            y1={PAD_TOP}
            y2={height - PAD_BOTTOM}
            stroke={seriesColor}
            strokeWidth={1}
            strokeDasharray="3 3"
            opacity={0.6}
          />
        )}
        {geometry.points.map((p, i) => (
          <text
            key={`label-${i}`}
            x={p.x}
            y={height - 6}
            fill={labelColor}
            fontSize={10}
            textAnchor="middle"
          >
            {data[i].label}
          </text>
        ))}
      </svg>
    </div>
  );
}

export type BarChartPoint = {
  label: string;
  value: number;
  color?: string;
};

type BarChartProps = {
  data: BarChartPoint[];
  height?: number;
};

export function BarChart({ data, height = 260 }: BarChartProps) {
  const geometry = useMemo(() => {
    const innerWidth = WIDTH - PAD_LEFT - PAD_RIGHT;
    const innerHeight = height - PAD_TOP - PAD_BOTTOM;
    const maxVal = niceCeil(Math.max(...data.map((d) => d.value), 1));
    const step = data.length > 0 ? innerWidth / data.length : innerWidth;
    const bars = data.map((d, i) => {
      const barWidth = Math.max(step * 0.62, 4);
      const x = PAD_LEFT + i * step + (step - barWidth) / 2;
      const barHeight = (d.value / maxVal) * innerHeight;
      return { x, y: PAD_TOP + innerHeight - barHeight, barWidth, barHeight };
    });
    const grid = Array.from({ length: 5 }, (_, i) => {
      const fraction = i / 4;
      const value = maxVal - fraction * maxVal;
      const y = PAD_TOP + fraction * innerHeight;
      return { y, value };
    });
    return { bars, grid, maxVal };
  }, [data, height]);

  return (
    <div className="bar-chart-wrap">
      <svg
        className="bar-chart"
        viewBox={`0 0 ${WIDTH} ${height}`}
        role="img"
        aria-label="Bar chart"
        width="100%"
        height="auto"
      >
        {geometry.grid.map((line) => (
          <g key={line.value}>
            <line
              x1={PAD_LEFT}
              x2={WIDTH - PAD_RIGHT}
              y1={line.y}
              y2={line.y}
              stroke="rgba(95, 232, 255, 0.18)"
              strokeWidth={1}
              strokeDasharray="4 5"
            />
            <text x={WIDTH - PAD_RIGHT + 4} y={line.y + 3.5} fill="var(--muted)" fontSize={10} textAnchor="start">
              {line.value >= 1000 ? `${(line.value / 1000).toFixed(1)}k` : line.value}
            </text>
          </g>
        ))}
        {geometry.bars.map((bar, i) => (
          <g key={i}>
            <rect
              x={bar.x}
              y={bar.y}
              width={bar.barWidth}
              height={bar.barHeight}
              rx={3}
              fill={data[i].color ?? `var(${chartSegments[i % chartSegments.length]})`}
              style={{ transition: "height 150ms ease, y 150ms ease" }}
            />
          </g>
        ))}
      </svg>
    </div>
  );
}