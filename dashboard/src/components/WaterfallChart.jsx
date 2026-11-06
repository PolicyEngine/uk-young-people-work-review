import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLOURS } from "../utils/chartTheme";
import { fiscalYear, formatMillions } from "../utils/measures";
import ChartPanel from "./ChartPanel";

// Expansions against offsets in one year, ending at the net total. Drawn
// with horizontal bars, so long measure names stay readable on a phone. A
// cost to the Exchequer (households gain) is teal; a saving is amber.
export function waterfallRows(measures, year, netValue = null) {
  let running = 0;
  const rows = measures.map((m) => {
    const value = m.budgetary_impact?.find((r) => r.year === year)?.value_m ?? null;
    const start = running;
    running += value ?? 0;
    return { name: m.name, base: Math.min(start, running), size: Math.abs(value ?? 0), value };
  });
  const net = netValue ?? running;
  rows.push({ name: "Net", base: Math.min(0, net), size: Math.abs(net), value: net, net: true });
  return rows;
}

// Kept for other views: wrap a long label onto lines of about 18 characters.
export function wrapLabel(text, width = 18) {
  const lines = [];
  for (const word of String(text).split(" ")) {
    const last = lines.at(-1);
    if (last && `${last} ${word}`.length <= width) lines[lines.length - 1] = `${last} ${word}`;
    else lines.push(word);
  }
  return lines;
}

function WrappedTick({ x, y, payload }) {
  const lines = wrapLabel(payload?.value ?? "", 22);
  return (
    <text x={x} y={y - ((lines.length - 1) * 13) / 2} textAnchor="end" fontSize={11} fill={CHART_COLOURS.text}>
      {lines.map((line, i) => (
        <tspan key={i} x={x - 4} dy={i === 0 ? 4 : 13}>
          {line}
        </tspan>
      ))}
    </text>
  );
}

export default function WaterfallChart({ measures, year, basis, netValue }) {
  const rows = waterfallRows(measures, year, netValue);
  return (
    <ChartPanel
      title={`Cost by measure, ${fiscalYear(year)}`}
      subtitle={`${basis}. ${netValue === null || netValue === undefined ? "Net: sum of the single-measure figures" : "Net: the selected measures run together"}.`}
      rows={rows.map(({ name, value }) => ({ measure: name, value_m: value }))}
      labels={{ measure: "Measure", value_m: "£ million" }}
      filename="waterfall"
    >
      <div style={{ width: "100%", height: 64 + rows.length * 52 }}>
        <ResponsiveContainer minWidth={0} minHeight={160}>
          <BarChart data={rows} layout="vertical" margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid stroke={CHART_COLOURS.grid} horizontal={false} />
            <XAxis type="number" tickFormatter={formatMillions} stroke={CHART_COLOURS.tick} />
            <YAxis type="category" dataKey="name" interval={0} width={150} tick={<WrappedTick />} stroke={CHART_COLOURS.tick} />
            <Tooltip formatter={(v, n, item) => (n === "size" ? formatMillions(item.payload.value) : null)} />
            <ReferenceLine x={0} stroke={CHART_COLOURS.zeroLine} />
            <Bar isAnimationActive={false} dataKey="base" stackId="w" fill="transparent" />
            <Bar isAnimationActive={false} dataKey="size" stackId="w">
              {rows.map((row) => (
                <Cell key={row.name} fill={row.net ? CHART_COLOURS.highlight : (row.value ?? 0) >= 0 ? CHART_COLOURS.gain : CHART_COLOURS.loss} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartPanel>
  );
}
