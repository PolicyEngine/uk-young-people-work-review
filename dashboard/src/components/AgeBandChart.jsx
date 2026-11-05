import { Bar, BarChart, CartesianGrid, Legend, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLOURS } from "../utils/chartTheme";
import { formatPounds } from "../utils/measures";
import ChartPanel from "./ChartPanel";

// Who benefits among young people: the change for each age band, one bar per
// selected measure. The bands come from results.json, not a fixed list.
export function ageBandRows(measures, bands) {
  return bands.map((band) => {
    const row = { age_band: band };
    for (const m of measures) row[m.id] = m.age_band?.find((r) => r.age_band === band)?.avg_change_gbp ?? 0;
    return row;
  });
}

export default function AgeBandChart({ measures, bands, basis }) {
  const rows = ageBandRows(measures, bands);
  return (
    <ChartPanel
      title="Average change by age band"
      subtitle={`${basis}, £ a year`}
      rows={rows}
      filename="age-band"
      moreInfo="Cells with fewer than 10 survey households are suppressed before publication. In the template the values are placeholders."
    >
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer>
          <BarChart data={rows}>
            <CartesianGrid stroke={CHART_COLOURS.grid} vertical={false} />
            <XAxis dataKey="age_band" stroke={CHART_COLOURS.tick} />
            <YAxis tickFormatter={formatPounds} stroke={CHART_COLOURS.tick} width={70} />
            <Tooltip formatter={(v) => formatPounds(v)} />
            <Legend />
            <ReferenceLine y={0} stroke={CHART_COLOURS.zeroLine} />
            {measures.map((m) => (
              <Bar isAnimationActive={false} key={m.id} dataKey={m.id} name={m.name} fill={m.colour} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartPanel>
  );
}
