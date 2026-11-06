import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { WINNERS_LOSERS_SERIES } from "../utils/chartTheme";
import { CHART_COLOURS } from "../utils/chartTheme";
import ChartPanel from "./ChartPanel";
import MeasureLegend from "./MeasureLegend";

const PACKAGE = "__package";

// Share of people by decile whose household gains or loses, for one measure
// or the package. Segments and key run gain more, gain less, no change,
// lose less, lose more, as on the AB2026 dashboard.
export default function WinnersLosersChart({ measures, pkg }) {
  const options = [...(pkg?.winners_losers ? [{ id: PACKAGE, name: "Selected package" }] : []), ...measures];
  const [chosen, setChosen] = useState(options[0]?.id);
  const current = options.find((o) => o.id === chosen) ?? options[0];
  const rows = (current?.id === PACKAGE ? pkg.winners_losers : current?.winners_losers) ?? [];
  const labels = Object.fromEntries(WINNERS_LOSERS_SERIES.map((s) => [s.key, s.label]));
  return (
    <ChartPanel
      title="Who gains and who loses"
      subtitle={`${current?.name ?? ""}: share of people by household income decile, %`}
      rows={rows}
      labels={{ ...labels, decile: "Income decile" }}
      filename="winners-losers"
      controls={
        options.length > 1 && (
          <label className="text-sm text-slate-700">
            <span className="sr-only">Measure</span>
            <select className="selector-select" value={current?.id} onChange={(e) => setChosen(e.target.value)}>
              {options.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name}
                </option>
              ))}
            </select>
          </label>
        )
      }
      moreInfo="A change of less than £1 a year counts as no change. The 5% threshold is the change as a share of the household's net income."
    >
      <MeasureLegend items={WINNERS_LOSERS_SERIES.map((s) => ({ key: s.key, label: s.label, colour: s.colour }))} />
      <div style={{ width: "100%", height: 360 }}>
        <ResponsiveContainer minWidth={0} minHeight={200}>
          <BarChart data={rows} layout="vertical" margin={{ top: 8, right: 8, bottom: 16, left: 8 }}>
            <CartesianGrid stroke={CHART_COLOURS.grid} horizontal={false} />
            <XAxis type="number" domain={[0, 100]} stroke={CHART_COLOURS.tick} tickFormatter={(v) => `${v}%`} />
            <YAxis type="category" dataKey="decile" stroke={CHART_COLOURS.tick} width={40} interval={0} label={{ value: "Decile", angle: -90, position: "insideLeft", fill: CHART_COLOURS.text }} />
            <Tooltip formatter={(v) => (v === null ? "n/a" : `${v}%`)} />
            {WINNERS_LOSERS_SERIES.map((s) => (
              <Bar isAnimationActive={false} key={s.key} dataKey={s.key} name={s.label} stackId="wl" fill={s.colour} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartPanel>
  );
}
