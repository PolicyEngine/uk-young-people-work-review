import { Bar, CartesianGrid, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLOURS } from "../utils/chartTheme";
import { fiscalShort, formatMillions, labelsFor, totalByYear } from "../utils/measures";
import ChartPanel from "./ChartPanel";
import MeasureLegend from "./MeasureLegend";

// Costs above zero and savings below (stackOffset="sign", as on the AB2026
// dashboard), with the net total marked in each year. The net is the
// package run when the selection is the package, else the sum of the
// single-measure figures, and the subtitle says which.
export function costRows(measures, years, pkg) {
  const rows = totalByYear(measures, years);
  if (!pkg) return rows;
  return rows.map((row) => ({ ...row, total: pkg.budgetary_impact?.find((c) => c.year === row.year)?.value_m ?? null }));
}

// The chart itself; ResponsiveContainer passes width and height.
export function CostBars({ rows, measures, width, height }) {
  return (
          <ComposedChart width={width} height={height} data={rows} stackOffset="sign" margin={{ top: 8, right: 8, bottom: 16, left: 8 }}>
      <CartesianGrid stroke={CHART_COLOURS.grid} vertical={false} />
      <XAxis dataKey="year" interval={0} tickFormatter={fiscalShort} stroke={CHART_COLOURS.tick} label={{ value: "Fiscal year", position: "insideBottom", offset: -10, fill: CHART_COLOURS.text }} />
      <YAxis tickFormatter={formatMillions} stroke={CHART_COLOURS.tick} width={70} />
      <Tooltip formatter={(v) => formatMillions(v)} labelFormatter={fiscalShort} />
      <ReferenceLine y={0} stroke={CHART_COLOURS.zeroLine} />
      {measures.map((m) => (
        <Bar isAnimationActive={false} key={m.id} dataKey={m.id} name={m.name} stackId="cost" fill={m.colour} />
      ))}
      <Line isAnimationActive={false} dataKey="total" name="Net" stroke="none" dot={{ r: 5, fill: CHART_COLOURS.net, stroke: CHART_COLOURS.surface, strokeWidth: 2 }} legendType="none" />
    </ComposedChart>
  );
}

export default function BudgetaryImpactChart({ measures, years, basis, pkg }) {
  const rows = costRows(measures, years, pkg);
  const net = pkg ? "Net: the selected measures run together" : "Net: sum of the single-measure figures";
  return (
    <ChartPanel
      title="Cost by year"
      subtitle={`${basis}. ${net}.`}
      rows={rows}
      labels={{ ...labelsFor(measures), total: "Net", year: "Fiscal year starting" }}
      filename="cost-by-year"
      moreInfo="Costs to the Exchequer stack above zero and savings below; the dot is the net total. Measures that are not computable are listed on the Policies tab and are not shown as zero."
    >
      <MeasureLegend
        items={[
          ...measures.map((m) => ({ key: m.id, label: m.name, colour: m.colour })),
          { key: "net", label: "Net", colour: CHART_COLOURS.net, line: true },
        ]}
      />
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer minWidth={0} minHeight={200}>
          <CostBars rows={rows} measures={measures} />
        </ResponsiveContainer>
      </div>
    </ChartPanel>
  );
}
