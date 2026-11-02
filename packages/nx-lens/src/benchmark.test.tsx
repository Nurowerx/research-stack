import { expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import fixture from "../../../datasets/synthetic/v1/visualization.json";
import {
  Histogram,
  MetricBars,
  TimeSeries,
  summarize,
  numericDomain,
} from "./index";
const noop = () => {};
it("matches the independently specified mean and missing-value denominator", () => {
  expect(summarize(fixture.values)).toEqual(fixture.expected);
  expect(summarize([null])).toEqual({ n: 0, missing: 1, mean: null });
});
it("maps the estimate and uncertainty bounds to independently computed SVG coordinates", () => {
  const html = renderToStaticMarkup(
    <MetricBars data={[fixture.interval]} onSelect={noop} />,
  );
  const mark = html.match(/<rect[^>]*data-measurement-id="estimate"[^>]*>/)![0];
  expect(Number(mark.match(/width="([^"]+)"/)![1])).toBeCloseTo(
    482 * fixture.interval.value,
    10,
  );
  const interval = html.match(
    /data-interval-low[^>]*d="M([^,]+),[^H]+H([^"]+)"/,
  )!;
  expect(Number(interval[1])).toBeCloseTo(104 + 482 * fixture.interval.low, 10);
  expect(Number(interval[2])).toBeCloseTo(
    104 + 482 * fixture.interval.high,
    10,
  );
  expect(mark).toContain('data-source-id="normal-fixture"');
});
it("retains every outlier and all 10000 observations in histogram bin counts", () => {
  for (const values of [fixture.histogram, fixture.stress_values]) {
    const html = renderToStaticMarkup(
      <Histogram values={values} onSelect={noop} />,
    );
    const count = [...html.matchAll(/aria-label="(\d+) calls/g)].reduce(
      (sum, m) => sum + Number(m[1]),
      0,
    );
    expect(count).toBe(values.length);
    expect(html).not.toMatch(/NaN|Infinity/);
  }
});
it("preserves negative values, an outlier and a disconnected missing-time interval", () => {
  const html = renderToStaticMarkup(
    <TimeSeries
      data={fixture.time_series}
      onSelect={noop}
      label="Known series"
    />,
  );
  const path = html.match(/<path d="([^"]+)"/)![1];
  expect(path.match(/M/g)).toHaveLength(2);
  expect(html.match(/<circle/g)).toHaveLength(4);
  expect(html).toContain("2: N/A");
  expect(
    numericDomain(
      fixture.time_series.map((d) => d.y),
      true,
    ),
  ).toEqual([-2, 100]);
});
it("rejects nonfinite coordinates and accuracy outside the declared scale", () => {
  expect(() => numericDomain([NaN])).toThrow();
  expect(() =>
    renderToStaticMarkup(
      <MetricBars data={[{ ...fixture.interval, value: 2 }]} onSelect={noop} />,
    ),
  ).toThrow();
});
