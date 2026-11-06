// A legend for the measure charts: the swatch carries the colour, the text
// stays in the text colour so every name is readable (adapted from the
// AB2026 dashboard's MeasureKey).
export default function MeasureLegend({ items }) {
  if (!items?.length) return null;
  return (
    <ul className="measure-legend" aria-label="Key">
      {items.map((item) => (
        <li key={item.key}>
          <span
            className={`measure-legend-swatch ${item.line ? "line" : ""} ${item.dashed ? "dashed" : ""}`}
            style={{ background: item.line ? "transparent" : item.colour, borderColor: item.colour }}
            aria-hidden="true"
          />
          {item.label}
        </li>
      ))}
    </ul>
  );
}
