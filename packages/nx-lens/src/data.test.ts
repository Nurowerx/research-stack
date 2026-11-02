import { describe, it, expect } from "vitest";
import { finiteMeasurements, csv } from "./data";
describe("Scientific data boundaries", () => {
  it("rejects invented or inverted uncertainty", () => {
    expect(() =>
      finiteMeasurements([
        { id: "a", label: "A", value: 0.4, low: 0.5, sourceId: "record" },
      ]),
    ).toThrow();
    expect(() =>
      finiteMeasurements([
        { id: "a", label: "A", value: NaN, sourceId: "record" },
      ]),
    ).toThrow();
  });
  it("preserves actual source IDs and allows absent intervals", () => {
    const data = [{ id: "a", label: "A", value: 0.4, sourceId: "record" }];
    expect(finiteMeasurements(data)).toEqual(data);
    expect(finiteMeasurements(data)[0].low).toBeUndefined();
  });
  it("exports quoted CSV and neutralizes spreadsheet formulas", () => {
    expect(csv([{ case: "a,b", answer: "=2+2", count: 2 }])).toContain(
      '"a,b","\'=2+2","2"',
    );
    expect(csv([])).toBe("");
  });
});
