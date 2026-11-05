import { formatMillions } from "../utils/measures";

// Official context, shown once. Other tabs link here rather than repeat it.
export default function BaselineTab({ data }) {
  const { context } = data;
  return (
    <div className="tab-body">
      <section className="panel mb-6">
        <h3 className="m-0 mb-1 text-lg font-semibold">Young people not in education, employment or training</h3>
        <p className="m-0 mb-4 text-sm text-slate-500">{context.neet_source}.</p>
        <table className="data-table compact">
          <thead>
            <tr>
              <th>Period</th>
              <th>NEET</th>
              <th>Share of age group</th>
            </tr>
          </thead>
          <tbody>
            {context.neet.map((row) => (
              <tr key={row.period}>
                <td>{row.period}</td>
                <td>{row.neet_k === null ? "n/a" : `${row.neet_k.toLocaleString("en-GB")}k`}</td>
                <td>{row.neet_rate_pct === null ? "n/a" : `${row.neet_rate_pct}%`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="panel">
        <h3 className="m-0 mb-1 text-lg font-semibold">Young people on the UC health element and PIP</h3>
        <p className="m-0 mb-4 text-sm text-slate-500">{context.young_claimants_source}. The modelled baseline is added on the day.</p>
        <table className="data-table compact">
          <thead>
            <tr>
              <th>Year</th>
              <th>UC health element: people</th>
              <th>UC health element: spending</th>
              <th>PIP: people</th>
              <th>PIP: spending</th>
            </tr>
          </thead>
          <tbody>
            {context.young_claimants.map((row) => (
              <tr key={row.year}>
                <td>{row.fiscal_year}</td>
                <td>{row.uc_health_caseload_k}k</td>
                <td>{formatMillions(row.uc_health_spend_m)}</td>
                <td>{row.pip_caseload_k}k</td>
                <td>{formatMillions(row.pip_spend_m)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
