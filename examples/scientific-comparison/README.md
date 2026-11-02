# Standalone LENS and FRAME composition

LENS renders measurements supplied by the caller. It does not fetch an API or invent uncertainty. Every mark carries a source record reference and emits a selection callback.

```tsx
import {MetricBars, ChartFrame} from '@nurowerx/lens';
import {Workspace} from '@nurowerx/frame';

const measurements = Object.entries(run.summary.groups).map(([id, group]) => ({
  id, label: id, value: group.accuracy, n: group.cases,
  sourceId: run.execution_id,
}));

<ChartFrame title="Case-family accuracy" description="Measured synthetic fixture results">
  <MetricBars data={measurements} selected={family} onSelect={setFamily}/>
</ChartFrame>
```

`ScatterPlot` accepts x/y measurements with source IDs; `Histogram` emits selected numeric bounds; `TimeSeries` emits a selected run; `ProvenanceGraph` emits a record ID and supports zoom/pan. The integrated console translates these events into shared filters and TRACE inspection. Tables offer alternative access to the same measured results.

Optional `low`/`high` fields on a bar measurement display supplied interval bounds. The caller must justify and label their estimand and calculation; the supplied deterministic fixture has no such interval. Non-finite values and inverted bounds are rejected.

`Workspace` receives navigation, header, main content and inspector slots plus width/onResize controls. It has no dependency on LENS or the API. The console persists its `WorkspaceLayout` through the layout service.
