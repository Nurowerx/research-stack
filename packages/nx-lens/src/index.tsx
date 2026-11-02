import { useId, useMemo, useState, useRef, type KeyboardEvent } from "react";
import {
  scaleLinear,
  scaleBand,
  bin,
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCenter,
  randomLcg,
  line,
  type SimulationNodeDatum,
  type SimulationLinkDatum,
} from "d3";
import {
  finiteMeasurements,
  type Measurement,
  type Point,
  type SeriesPoint,
  numericDomain,
  exportSVG,
} from "./data";
export * from "./data";
const colors = {
  ink: "#e6e3dc",
  muted: "#a4acb0",
  line: "#343d41",
  accent: "#c9987c",
  good: "#9fbdb0",
  bad: "#dca896",
};
const activate = (e: KeyboardEvent, callback: () => void) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    callback();
  }
};

export function ChartFrame({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  const ref = useRef<HTMLDivElement>(null);
  return (
    <section className="chart-frame" ref={ref}>
      <header className="panel-heading">
        <h3>{title}</h3>
        <button
          className="text-button"
          onClick={() => {
            const svg = ref.current?.querySelector("svg");
            if (svg)
              exportSVG(svg, `${title.toLowerCase().replaceAll(" ", "-")}.svg`);
          }}
        >
          Export SVG
        </button>
      </header>
      <p className="chart-description">{description}</p>
      {children}
    </section>
  );
}

export function MetricBars({
  data,
  selected,
  onSelect,
  title = "Accuracy by case family",
}: {
  data: Measurement[];
  selected?: string;
  onSelect: (id: string) => void;
  title?: string;
}) {
  const id = useId();
  finiteMeasurements(data);
  if (
    data.some((d) =>
      [d.value, d.low, d.high].some((v) => v != null && (v < 0 || v > 1)),
    )
  )
    throw new Error("Accuracy measurements and bounds must be within [0, 1]");
  const width = 650,
    height = 238;
  const y = scaleBand<string>()
    .domain(data.map((d) => d.id))
    .range([14, height - 32])
    .padding(0.42);
  const x = scaleLinear()
    .domain([0, 1])
    .range([104, width - 64]);
  return (
    <>
      <svg viewBox={`0 0 ${width} ${height}`} role="group" aria-labelledby={id}>
        <title id={id}>
          {title}. Select a family to filter the linked results.
        </title>
        {[0, 0.25, 0.5, 0.75, 1].map((t) => (
          <g key={t}>
            <line
              x1={x(t)}
              x2={x(t)}
              y1={6}
              y2={height - 27}
              stroke={colors.line}
              strokeDasharray={t ? "2 5" : undefined}
            />
            <text
              x={x(t)}
              y={height - 6}
              textAnchor="middle"
              fill={colors.muted}
              fontSize={11}
            >
              {Math.round(t * 100)}%
            </text>
          </g>
        ))}
        {data.map((d) => (
          <g
            key={d.id}
            role="button"
            tabIndex={0}
            aria-label={`${d.label}: ${d.value === null ? "N/A" : (d.value * 100).toFixed(1) + " percent"}, ${d.n ?? "unknown"} cases. Filter ${d.label}`}
            onClick={() => onSelect(d.id)}
            onKeyDown={(e) => activate(e, () => onSelect(d.id))}
            className="chart-mark"
          >
            <rect
              x={0}
              y={y(d.id)! - 6}
              width={width}
              height={y.bandwidth() + 12}
              fill={selected === d.id ? "#30302c" : "transparent"}
            />
            <text
              x={0}
              y={y(d.id)! + y.bandwidth() / 2 + 4}
              fill={colors.ink}
              fontSize={12}
            >
              {d.label}
            </text>
            <rect
              x={x(0)}
              y={y(d.id)}
              width={x(1) - x(0)}
              height={y.bandwidth()}
              fill="#292f31"
            />
            {d.value !== null && (
              <rect
                data-source-id={d.sourceId}
                data-measurement-id={d.id}
                data-value={d.value}
                x={x(0)}
                y={y(d.id)}
                width={Math.max(0, x(d.value) - x(0))}
                height={y.bandwidth()}
                fill={selected === d.id ? colors.ink : colors.accent}
              />
            )}
            {d.low !== undefined && d.high !== undefined && (
              <path
                data-interval-low={d.low}
                data-interval-high={d.high}
                d={`M${x(d.low)},${y(d.id)! + y.bandwidth() / 2}H${x(d.high)}`}
                stroke={colors.ink}
                strokeWidth={2}
              />
            )}
            <text
              x={width - 4}
              y={y(d.id)! + y.bandwidth() / 2 + 4}
              textAnchor="end"
              fill={colors.ink}
              fontSize={12}
            >
              {d.value === null ? "N/A" : Math.round(d.value * 100) + "%"}
            </text>
            <title>
              {d.label}; n={d.n}; source {d.sourceId}
            </title>
          </g>
        ))}
      </svg>
      <details className="data-alternative">
        <summary>View chart data</summary>
        <table>
          <thead>
            <tr>
              <th>Family</th>
              <th>Accuracy</th>
              <th>Cases</th>
            </tr>
          </thead>
          <tbody>
            {data.map((d) => (
              <tr key={d.id}>
                <td>
                  <button onClick={() => onSelect(d.id)}>{d.label}</button>
                </td>
                <td>
                  {d.value === null ? "N/A" : (d.value * 100).toFixed(2) + "%"}
                </td>
                <td>{d.n}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </>
  );
}

export function ScatterPlot({
  data,
  onSelect,
  title = "Measured prediction latency",
}: {
  data: Point[];
  onSelect: (id: string) => void;
  title?: string;
}) {
  const id = useId();
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState(0);
  if (
    data.some(
      (d) =>
        !Number.isFinite(d.x) || !Number.isFinite(d.y) || d.x < 0 || d.y < 0,
    )
  )
    throw new Error(
      "Latency and observation index must be finite and nonnegative",
    );
  const max = Math.max(...data.map((d) => d.x), 0.001);
  const x = scaleLinear()
    .domain([max * offset, max * (offset + 1 / zoom)])
    .range([54, 600]);
  const y = scaleLinear()
    .domain([0, Math.max(...data.map((d) => d.y), 1)])
    .range([194, 20]);
  return (
    <>
      <div className="chart-tools">
        <label>
          Zoom{" "}
          <input
            aria-label="Latency chart zoom"
            type="range"
            min={1}
            max={5}
            step={0.5}
            value={zoom}
            onChange={(e) => {
              setZoom(+e.target.value);
              setOffset(0);
            }}
          />
        </label>
        <label>
          Pan{" "}
          <input
            aria-label="Latency chart pan"
            type="range"
            min={0}
            max={Math.max(0, 1 - 1 / zoom)}
            step={0.01}
            value={offset}
            onChange={(e) => setOffset(+e.target.value)}
          />
        </label>
      </div>
      <svg viewBox="0 0 650 238" role="group" aria-labelledby={id}>
        <title id={id}>
          {title}. Each point is one actual predict call. Select to inspect
          source evidence.
        </title>
        {x.ticks(5).map((t) => (
          <g key={t}>
            <line
              x1={x(t)}
              x2={x(t)}
              y1={14}
              y2={198}
              stroke={colors.line}
              strokeDasharray="2 5"
            />
            <text
              x={x(t)}
              y={218}
              textAnchor="middle"
              fill={colors.muted}
              fontSize={10}
            >
              {t.toPrecision(2)}
            </text>
          </g>
        ))}
        <text
          x={330}
          y={235}
          textAnchor="middle"
          fill={colors.muted}
          fontSize={10}
        >
          PREDICT CALL · MILLISECONDS
        </text>
        <text
          transform="translate(13 130) rotate(-90)"
          textAnchor="middle"
          fill={colors.muted}
          fontSize={10}
        >
          OBSERVATION INDEX
        </text>
        {data
          .filter((d) => x(d.x) >= 54 && x(d.x) <= 600)
          .map((d) => (
            <circle
              key={d.id}
              cx={x(d.x)}
              cy={y(d.y)}
              r={3.8}
              fill={d.correct ? colors.good : colors.accent}
              fillOpacity={0.85}
              className="chart-mark"
              tabIndex={0}
              role="button"
              aria-label={`${d.label}, ${d.x.toFixed(4)} milliseconds. Inspect result`}
              onClick={() => onSelect(d.id)}
              onKeyDown={(e) => activate(e, () => onSelect(d.id))}
            >
              <title>
                {d.label}: {d.x.toFixed(5)} ms
              </title>
            </circle>
          ))}
      </svg>
      <p className="chart-footnote">
        Copper: incorrect answer · Sage: correct answer. Timing excludes scoring
        and storage.
      </p>
    </>
  );
}

export function Histogram({
  values,
  onSelect,
}: {
  values: number[];
  onSelect: (range: [number, number] | null) => void;
}) {
  const id = useId();
  const domain = numericDomain(values);
  if (!values.length) return <p role="status">No measurements</p>;
  const bins = bin().domain(domain).thresholds(10)(values);
  const x = scaleLinear().domain(domain).nice().range([45, 610]);
  const y = scaleLinear()
    .domain([0, Math.max(...bins.map((b) => b.length), 1)])
    .range([124, 12]);
  return (
    <>
      <svg viewBox="0 0 650 155" role="group" aria-labelledby={id}>
        <title id={id}>
          Latency distribution. Select a bin to filter the result table.
        </title>
        {bins.map((b, i) => (
          <g
            key={i}
            role="button"
            tabIndex={0}
            className="chart-mark"
            aria-label={`${b.length} calls from ${b.x0?.toPrecision(3)} to ${b.x1?.toPrecision(3)} milliseconds`}
            onClick={() => onSelect([b.x0!, b.x1!])}
            onKeyDown={(e) => activate(e, () => onSelect([b.x0!, b.x1!]))}
          >
            <rect
              x={x(b.x0!)}
              y={y(b.length)}
              width={Math.max(1, x(b.x1!) - x(b.x0!) - 2)}
              height={124 - y(b.length)}
              fill={colors.accent}
            />
            <text
              x={x(b.x0!) + 5}
              y={y(b.length) - 4}
              fill={colors.muted}
              fontSize={10}
            >
              {b.length}
            </text>
          </g>
        ))}
        {x.ticks(5).map((t) => (
          <text
            key={t}
            x={x(t)}
            y={146}
            textAnchor="middle"
            fill={colors.muted}
            fontSize={10}
          >
            {t.toPrecision(2)} ms
          </text>
        ))}
      </svg>
      <button className="text-button" onClick={() => onSelect(null)}>
        Clear latency filter
      </button>
    </>
  );
}

export function TimeSeries({
  data,
  onSelect,
  label,
}: {
  data: SeriesPoint[];
  onSelect: (id: string) => void;
  label: string;
}) {
  const id = useId();
  const domain = numericDomain(data.map((d) => d.x));
  const yDomain = numericDomain(
    data.map((d) => d.y),
    true,
  );
  const ordered = [...data].sort((a, b) => a.x - b.x);
  const x = scaleLinear().domain(domain).range([40, 610]);
  const y = scaleLinear().domain(yDomain).range([125, 15]);
  const path = line<SeriesPoint>()
    .defined((d) => d.y !== null)
    .x((d) => x(d.x))
    .y((d) => y(d.y!))(ordered);
  return (
    <svg viewBox="0 0 650 160" role="group" aria-labelledby={id}>
      <title id={id}>{label}. Each point links to an evaluation run.</title>
      {data
        .filter((d) => d.y === null)
        .map((d) => (
          <text
            key={d.id}
            x={x(d.x)}
            y={136}
            fill={colors.muted}
            fontSize={9}
            textAnchor="middle"
          >
            {d.label}: N/A
          </text>
        ))}
      <path
        d={path ?? ""}
        fill="none"
        stroke={colors.accent}
        strokeWidth={1.5}
      />
      {ordered
        .filter((d): d is Point => d.y !== null)
        .map((d) => (
          <g
            key={d.id}
            role="button"
            tabIndex={0}
            aria-label={`${d.label}: ${d.y.toFixed(3)}. Open run`}
            onClick={() => onSelect(d.id)}
            onKeyDown={(e) => activate(e, () => onSelect(d.id))}
            className="chart-mark"
          >
            <circle cx={x(d.x)} cy={y(d.y)} r={5} fill={colors.ink} />
            <text
              x={x(d.x)}
              y={y(d.y) - 10}
              fill={colors.muted}
              fontSize={10}
              textAnchor="middle"
            >
              {d.y.toFixed(2)}
            </text>
            <title>
              {d.label} · {new Date(d.x).toLocaleString()}
            </title>
          </g>
        ))}
      {x.ticks(3).map((t) => (
        <text
          key={t}
          x={x(t)}
          y={151}
          fill={colors.muted}
          fontSize={10}
          textAnchor="middle"
        >
          {new Date(t).toLocaleTimeString()}
        </text>
      ))}
    </svg>
  );
}

export interface GraphNode {
  id: string;
  label: string;
  kind: string;
}
export interface GraphEdge {
  id: string;
  source_id: string;
  target_id: string;
  relation: string;
  assessment: string;
}
interface LayoutNode extends GraphNode, SimulationNodeDatum {}
interface LayoutEdge extends SimulationLinkDatum<LayoutNode>, GraphEdge {}
export function ProvenanceGraph({
  nodes,
  edges,
  selected,
  onSelect,
}: {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selected?: string;
  onSelect: (id: string) => void;
}) {
  const id = useId();
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const drag = useRef<{ x: number; y: number } | null>(null);
  const layout = useMemo(() => {
    const ns: LayoutNode[] = nodes.map((n) => ({ ...n }));
    const links: LayoutEdge[] = edges.map((e) => ({
      ...e,
      source: e.source_id,
      target: e.target_id,
    }));
    const simulation = forceSimulation(ns)
      .randomSource(randomLcg(0.42))
      .force(
        "link",
        forceLink<LayoutNode, LayoutEdge>(links)
          .id((n) => n.id)
          .distance(85),
      )
      .force("charge", forceManyBody().strength(-230))
      .force("center", forceCenter(340, 180))
      .stop();
    for (let i = 0; i < 100; i++) simulation.tick();
    return { ns, links };
  }, [nodes, edges]);
  return (
    <>
      <div className="chart-tools">
        <button
          onClick={() => setZoom((z) => Math.min(z + 0.2, 3))}
          aria-label="Zoom graph in"
        >
          +
        </button>
        <button
          onClick={() => setZoom((z) => Math.max(z - 0.2, 0.4))}
          aria-label="Zoom graph out"
        >
          −
        </button>
        <button
          onClick={() => {
            setZoom(1);
            setPan({ x: 0, y: 0 });
          }}
        >
          Reset graph
        </button>
        <span>Drag to pan · Tab to inspect</span>
      </div>
      <svg
        viewBox="0 0 680 360"
        role="group"
        aria-labelledby={id}
        onPointerDown={(e) => {
          if (e.target === e.currentTarget) {
            drag.current = { x: e.clientX, y: e.clientY };
            e.currentTarget.setPointerCapture(e.pointerId);
          }
        }}
        onPointerMove={(e) => {
          if (drag.current) {
            const rect = e.currentTarget.getBoundingClientRect();
            setPan((p) => ({
              x: p.x + ((e.clientX - drag.current!.x) * 680) / rect.width,
              y: p.y + ((e.clientY - drag.current!.y) * 360) / rect.height,
            }));
            drag.current = { x: e.clientX, y: e.clientY };
          }
        }}
        onPointerUp={() => {
          drag.current = null;
        }}
      >
        <title id={id}>
          Version-specific provenance graph. Arrows point from a record to its
          source or dependency. Linkage is not proof of truth.
        </title>
        <defs>
          <marker
            id={`${id}-arrow`}
            viewBox="0 0 10 10"
            refX={19}
            refY={5}
            markerWidth={5}
            markerHeight={5}
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill={colors.muted} />
          </marker>
        </defs>
        <g
          transform={`translate(${pan.x} ${pan.y}) translate(340 180) scale(${zoom}) translate(-340 -180)`}
        >
          {layout.links.map((e) => {
            const a = e.source as LayoutNode,
              b = e.target as LayoutNode;
            return (
              <line
                key={e.id}
                x1={a.x}
                y1={a.y}
                x2={b.x}
                y2={b.y}
                stroke={
                  e.relation === "contradicted_by" ? colors.bad : colors.line
                }
                strokeDasharray={
                  e.assessment === "citation_only" ? "3 4" : undefined
                }
                markerEnd={`url(#${id}-arrow)`}
              >
                <title>
                  {e.relation} · {e.assessment}
                </title>
              </line>
            );
          })}
          {layout.ns.map((n) => (
            <g
              key={n.id}
              transform={`translate(${n.x} ${n.y})`}
              className="chart-mark"
              role="button"
              tabIndex={0}
              aria-label={`${n.kind}: ${n.label}. Inspect record`}
              onClick={() => onSelect(n.id)}
              onKeyDown={(e) => activate(e, () => onSelect(n.id))}
            >
              <circle
                r={n.id === selected ? 10 : 6}
                fill={
                  n.kind === "claim"
                    ? colors.accent
                    : n.kind === "evidence"
                      ? colors.good
                      : "#b8bfc1"
                }
                stroke={n.id === selected ? colors.ink : "#191d1f"}
                strokeWidth={2}
              />
              <text y={20} textAnchor="middle" fill={colors.ink} fontSize={9}>
                {n.label.length > 30 ? n.label.slice(0, 28) + "…" : n.label}
              </text>
              <title>
                {n.kind} / {n.label}
              </title>
            </g>
          ))}
        </g>
      </svg>
      <p className="chart-footnote">
        Dashed links: citation only · Copper links: contradictory assessment.
        Use the record table for an accessible alternative.
      </p>
    </>
  );
}
