const formatThousands = (k) => `${k > 0 ? "+" : k < 0 ? "-" : ""}${Math.abs(Math.round(k)).toLocaleString("en-GB")},000`;

const GROUPS = { all: "Everyone", children: "Children", aged_16_24: "Aged 16 to 24" };
const BASIS = { bhc: "Before housing costs", ahc: "After housing costs" };

// Poverty rates under current law and each measure (or the package), by
// basis and group. Present only once model mode has run.
export default function PovertyView({ measures, pkg, year }) {
  const sources = [...(pkg?.poverty ? [{ id: "package", name: "Selected package", poverty: pkg.poverty }] : []), ...measures.filter((m) => m.poverty)];
  if (!sources.length) {
    return (
      <section className="panel mb-6" data-testid="poverty-pending">
        <h3 className="m-0 mb-1 text-lg font-semibold">Poverty</h3>
        <p className="m-0 text-sm text-slate-600">
          Poverty rates before and after housing costs, for everyone, children and 16-24-year-olds, come from the full model on the day.
        </p>
      </section>
    );
  }
  return (
    <section className="panel mb-6">
      <h3 className="m-0 mb-1 text-lg font-semibold">Poverty, {year}</h3>
      <p className="m-0 mb-4 text-sm text-slate-500">Share of people in relative poverty (below 60% of median income), and the change in the number of people in poverty.</p>
      <div className="overflow-x-auto">
        <table className="data-table compact">
          <thead>
            <tr>
              <th>Measure</th>
              <th>Basis</th>
              <th>Group</th>
              <th>Current law</th>
              <th>With the measure</th>
              <th>Change in people</th>
            </tr>
          </thead>
          <tbody>
            {sources.flatMap((s) =>
              s.poverty.map((row) => (
                <tr key={`${s.id}-${row.basis}-${row.group}`}>
                  <td>{s.name}</td>
                  <td>{BASIS[row.basis]}</td>
                  <td>{GROUPS[row.group] ?? row.group}</td>
                  <td>{row.baseline_rate_pct === null ? "Suppressed" : `${row.baseline_rate_pct.toFixed(1)}%`}</td>
                  <td>{row.reform_rate_pct === null ? "Suppressed" : `${row.reform_rate_pct.toFixed(1)}%`}</td>
                  <td>{row.change_k === null ? "Suppressed" : formatThousands(row.change_k)}</td>
                </tr>
              )),
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
