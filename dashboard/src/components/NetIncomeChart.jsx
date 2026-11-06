import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLOURS } from "../utils/chartTheme";
import { formatPounds, labelsFor } from "../utils/measures";
import ChartPanel from "./ChartPanel";
import MeasureLegend from "./MeasureLegend";

// Net income against weekly hours for one preset, with only the measures
// that change it: shows where work pays and where the taper and the health
// element create a cliff.
export default function NetIncomeChart({ curve, measures, sketch }) {
  const changing = measures.filter((m) => curve.rows.some((r) => r[m.id] !== undefined && r[m.id] !== r.baseline));
  const unchanged = measures.filter((m) => !changing.includes(m));
  return (
    <ChartPanel
      title={`Net income by hours worked: ${curve.label}`}
      subtitle={`£ a month, at £${curve.hourly_wage.toFixed(2)} an hour, 2027-28`}
      rows={curve.rows}
      labels={{ ...labelsFor(measures), baseline: "Current law", hours: "Hours a week" }}
      filename={`net-income-${curve.preset}`}
      moreInfo={`Earnings after income tax and employee National Insurance, plus Universal Credit.${sketch ? " Placeholder arithmetic; the full model adds every other benefit and tax on the day." : ""}${unchanged.length ? ` No change under: ${unchanged.map((m) => m.name).join("; ")}.` : ""}`}
    >
      <MeasureLegend
        items={[
          { key: "baseline", label: "Current law", colour: CHART_COLOURS.before, line: true, dashed: true },
          ...changing.map((m) => ({ key: m.id, label: m.name, colour: m.colour, line: true })),
        ]}
      />
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer minWidth={0} minHeight={200}>
          <LineChart data={curve.rows} margin={{ top: 8, right: 8, bottom: 24, left: 8 }}>
            <CartesianGrid stroke={CHART_COLOURS.grid} vertical={false} />
            <XAxis dataKey="hours" stroke={CHART_COLOURS.tick} label={{ value: "Hours a week", position: "insideBottom", offset: -16, fill: CHART_COLOURS.text }} />
            <YAxis tickFormatter={formatPounds} stroke={CHART_COLOURS.tick} width={70} />
            <Tooltip formatter={(v) => formatPounds(v)} />
            <Line isAnimationActive={false} dataKey="baseline" name="Current law" stroke={CHART_COLOURS.before} strokeDasharray="6 4" dot={false} />
            {changing.map((m) => (
              <Line isAnimationActive={false} key={m.id} dataKey={m.id} name={m.name} stroke={m.colour} dot={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </ChartPanel>
  );
}
