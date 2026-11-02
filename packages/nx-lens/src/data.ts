export interface Measurement {
  id: string;
  label: string;
  value: number | null;
  sourceId: string;
  n?: number;
  low?: number;
  high?: number;
}
export interface Point {
  id: string;
  x: number;
  y: number;
  label: string;
  sourceId: string;
  group?: string;
  correct?: boolean;
}
export interface SeriesPoint extends Omit<Point, "y"> {
  y: number | null;
}
export function numericDomain(
  values: (number | null)[],
  includeZero = false,
): [number, number] {
  const valid = values.filter((v): v is number => v !== null);
  if (valid.some((v) => !Number.isFinite(v)))
    throw new Error("Non-finite chart coordinate");
  if (!valid.length) return [0, 1];
  let low = valid.reduce((a, b) => Math.min(a, b), Infinity),
    high = valid.reduce((a, b) => Math.max(a, b), -Infinity);
  if (includeZero) {
    low = Math.min(low, 0);
    high = Math.max(high, 0);
  }
  if (low === high) {
    const padding = Math.max(Math.abs(low) * 0.05, 0.5);
    low -= padding;
    high += padding;
  }
  return [low, high];
}
export function summarize(values: (number | null)[]) {
  const valid = values.filter((v): v is number => v !== null);
  if (valid.some((v) => !Number.isFinite(v)))
    throw new Error("Non-finite measurement");
  return {
    n: valid.length,
    missing: values.length - valid.length,
    mean: valid.length ? valid.reduce((a, b) => a + b, 0) / valid.length : null,
  };
}
export function finiteMeasurements(data: Measurement[]): Measurement[] {
  if (
    data.some(
      (d) =>
        (d.value !== null && !Number.isFinite(d.value)) ||
        (d.low !== undefined) !== (d.high !== undefined) ||
        (d.value === null && (d.low !== undefined || d.high !== undefined)) ||
        (d.low !== undefined &&
          (!Number.isFinite(d.low) || d.low > d.value!)) ||
        (d.high !== undefined &&
          (!Number.isFinite(d.high) || d.high < d.value!)),
    )
  )
    throw new Error("Invalid measurement or uncertainty bounds");
  return data;
}
export function csv(rows: Record<string, unknown>[]): string {
  if (!rows.length) return "";
  const keys = Object.keys(rows[0]);
  const escape = (v: unknown) => {
    let s = v == null ? "" : String(v);
    if (/^[=+\-@\t\r]/.test(s)) s = "'" + s;
    return '"' + s.replaceAll('"', '""') + '"';
  };
  return [
    keys.map(escape).join(","),
    ...rows.map((r) => keys.map((k) => escape(r[k])).join(",")),
  ].join("\r\n");
}
export function download(
  name: string,
  content: string,
  type = "application/json",
) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function exportSVG(svg: SVGSVGElement, name = "research-chart.svg") {
  const clone = svg.cloneNode(true) as SVGSVGElement;
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  const originals = [svg, ...svg.querySelectorAll("*")];
  const copies = [clone, ...clone.querySelectorAll("*")];
  originals.forEach((el, i) => {
    const s = getComputedStyle(el);
    for (const key of [
      "fill",
      "stroke",
      "font-family",
      "font-size",
      "font-weight",
      "opacity",
    ])
      copies[i].setAttribute(key, s.getPropertyValue(key));
  });
  clone.setAttribute("style", "background:#191d1f");
  download(name, new XMLSerializer().serializeToString(clone), "image/svg+xml");
}
