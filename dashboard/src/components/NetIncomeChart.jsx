import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLOURS } from "../utils/chartTheme";
import { formatPounds } from "../utils/measures";
import ChartPanel from "./ChartPanel";

// Net income against weekly hours for one preset: shows where work pays and
// where the taper and the health element create a cliff.
export default function NetIncomeChart({ curve, measures }) {
  return (
    <ChartPanel
      title={`Net income by hours worked: ${curve.label}`}
      subtitle={`£ a month, at £${curve.hourly_wage.toFixed(2)} an hour, 2027-28`}
      rows={curve.rows}
      filename={`net-income-${curve.preset}`}
      moreInfo="Earnings after income tax and employee National Insurance, plus Universal Credit. Placeholder arithmetic; the model adds every other benefit and tax on the day."
    >
      <div style={{ width: "100%", height: 320 }}>
        <ResponsiveContainer>
          <LineChart data={curve.rows}>
            <CartesianGrid stroke={CHART_COLOURS.grid} vertical={false} />
            <XAxis dataKey="hours" stroke={CHART_COLOURS.tick} label={{ value: "Hours a week", position: "insideBottom", offset: -4 }} />
            <YAxis tickFormatter={formatPounds} stroke={CHART_COLOURS.tick} width={70} />
            <Tooltip formatter={(v) => formatPounds(v)} />
            <Legend />
            <Line isAnimationActive={false} dataKey="baseline" name="Current law" stroke={CHART_COLOURS.before} strokeDasharray="6 4" dot={false} />
            {measures.map((m) => (
              <Line isAnimationActive={false} key={m.id} dataKey={m.id} name={m.name} stroke={m.colour} dot={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </ChartPanel>
  );
}
