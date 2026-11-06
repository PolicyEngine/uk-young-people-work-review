import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLOURS } from "../utils/chartTheme";
import { formatPounds, labelsFor } from "../utils/measures";
import ChartPanel from "./ChartPanel";
import MeasureLegend from "./MeasureLegend";

// The change for each age band, one bar per selected measure. The bands come
// from results.json; a missing or suppressed band is null, never 0.
export function ageBandRows(measures, bands) {
  return bands.map((band) => {
    const row = { age_band: band };
    for (const m of measures) row[m.id] = m.age_band?.find((r) => r.age_band === band)?.avg_change_gbp ?? null;
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
      labels={{ ...labelsFor(measures), age_band: "Age band" }}
      filename="age-band"
      moreInfo="Each person is given their household's change in net income and grouped by their own age, so a 17-year-old living with a parent counts in the 16-17 band. Cells with fewer than 10 survey households are suppressed before publication."
    >
      <MeasureLegend items={measures.map((m) => ({ key: m.id, label: m.name, colour: m.colour }))} />
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer minWidth={0} minHeight={200}>
          <BarChart data={rows} margin={{ top: 8, right: 8, bottom: 16, left: 8 }}>
            <CartesianGrid stroke={CHART_COLOURS.grid} vertical={false} />
            <XAxis dataKey="age_band" interval={0} stroke={CHART_COLOURS.tick} label={{ value: "Age", position: "insideBottom", offset: -10, fill: CHART_COLOURS.text }} />
            <YAxis tickFormatter={formatPounds} stroke={CHART_COLOURS.tick} width={70} />
            <Tooltip formatter={(v) => formatPounds(v)} />
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
