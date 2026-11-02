import { expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { MetricBars, Histogram, TimeSeries } from "./index";
const noop = () => {};
it("represents a missing measurement as N/A rather than zero", () => {
  const html = renderToStaticMarkup(
    <MetricBars
      data={
        [
          { id: "missing", label: "Missing", value: null, sourceId: "source" },
        ] as any
      }
      onSelect={noop}
    />,
  );
  expect(html).toContain("Missing: N/A");
  expect(html).not.toContain('data-value="0"');
});
it("rejects an incomplete interval instead of silently omitting it", () => {
  expect(() =>
    renderToStaticMarkup(
      <MetricBars
        data={[
          { id: "a", label: "A", value: 0.5, low: 0.3, sourceId: "source" },
        ]}
        onSelect={noop}
      />,
    ),
  ).toThrow();
});
it("gives an explicit empty histogram state", () => {
  const html = renderToStaticMarkup(<Histogram values={[]} onSelect={noop} />);
  expect(html).toContain("No measurements");
  expect(html).not.toMatch(/NaN|undefined/);
});
it("preserves missing time-series samples as a visible gap", () => {
  const html = renderToStaticMarkup(
    <TimeSeries
      data={
        [
          { id: "a", x: 1, y: 2, label: "A", sourceId: "a" },
          { id: "b", x: 2, y: null, label: "Missing", sourceId: "b" },
          { id: "c", x: 3, y: 4, label: "C", sourceId: "c" },
        ] as any
      }
      onSelect={noop}
      label="Series"
    />,
  );
  expect(html).toContain("Missing: N/A");
  expect(html).not.toMatch(/NaN|undefined/);
});
