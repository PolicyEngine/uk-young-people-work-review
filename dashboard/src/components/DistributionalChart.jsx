import { useState } from "react";
import { Bar, CartesianGrid, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLOURS } from "../utils/chartTheme";
import { formatPounds, labelsFor } from "../utils/measures";
import ChartPanel from "./ChartPanel";
import MeasureLegend from "./MeasureLegend";

const FIELDS = { gbp: "avg_change_gbp", pct: "pct_change" };

// A missing or suppressed decile is null, never 0.
export function decileRows(measures, field = "avg_change_gbp", pkg = null) {
  return Array.from({ length: 10 }, (_, i) => {
    const row = { decile: i + 1 };
    let total = 0;
    let any = false;
    for (const m of measures) {
      const value = m.decile?.[i]?.[field] ?? null;
      row[m.id] = value;
      if (value !== null) {
        total += value;
        any = true;
      }
    }
    row.total = pkg ? pkg.decile?.[i]?.[field] ?? null : any ? total : null;
    return row;
  });
}

const formatPct = (v) => (v === null || v === undefined ? "n/a" : `${v.toFixed(2)}%`);

export default function DistributionalChart({ measures, basis, pkg }) {
  const [unit, setUnit] = useState("gbp");
  const rows = decileRows(measures, FIELDS[unit], pkg);
  const format = unit === "gbp" ? formatPounds : formatPct;
  return (
    <ChartPanel
      title="Change in household income by decile"
      subtitle={`${basis}; ${unit === "gbp" ? "£ a year" : "% of net income"}. ${pkg ? "Net: the selected measures run together" : "Net: sum of the single-measure figures"}.`}
      rows={rows}
      labels={{ ...labelsFor(measures), total: "Net", decile: "Income decile" }}
      filename="deciles"
      controls={
        <div className="flex gap-1" role="group" aria-label="Unit">
          <button type="button" className={`toggle-button ${unit === "gbp" ? "active" : ""}`} aria-pressed={unit === "gbp"} onClick={() => setUnit("gbp")}>
            £ a year
          </button>
          <button type="button" className={`toggle-button ${unit === "pct" ? "active" : ""}`} aria-pressed={unit === "pct"} onClick={() => setUnit("pct")}>
            % change
          </button>
        </div>
      }
    >
      <MeasureLegend
        items={[
          ...measures.map((m) => ({ key: m.id, label: m.name, colour: m.colour })),
          { key: "net", label: "Net", colour: CHART_COLOURS.net, line: true },
        ]}
      />
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer minWidth={0} minHeight={200}>
          <ComposedChart data={rows} stackOffset="sign" margin={{ top: 8, right: 8, bottom: 16, left: 8 }}>
            <CartesianGrid stroke={CHART_COLOURS.grid} vertical={false} />
            <XAxis dataKey="decile" interval={0} stroke={CHART_COLOURS.tick} label={{ value: "Income decile (1 = lowest)", position: "insideBottom", offset: -10, fill: CHART_COLOURS.text }} />
            <YAxis tickFormatter={format} stroke={CHART_COLOURS.tick} width={64} />
            <Tooltip formatter={(v) => format(v)} labelFormatter={(d) => `Decile ${d}`} />
            <ReferenceLine y={0} stroke={CHART_COLOURS.zeroLine} />
            {measures.map((m) => (
              <Bar isAnimationActive={false} key={m.id} dataKey={m.id} name={m.name} stackId="d" fill={m.colour} />
            ))}
            <Line isAnimationActive={false} dataKey="total" name="Net" stroke="none" dot={{ r: 4, fill: CHART_COLOURS.net, stroke: CHART_COLOURS.surface, strokeWidth: 2 }} legendType="none" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </ChartPanel>
  );
}
