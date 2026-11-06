import { fiscalYear, formatMillions } from "../utils/measures";

// The report's own or official figures for measures recorded as spending
// lines, kept apart from the modelled total. A line with no figure says so;
// it is never shown as £0.
export default function SpendingLines({ measures }) {
  const lines = measures.filter((m) => m.route === "ledger");
  if (!lines.length) return null;
  return (
    <section className="panel mb-6" data-testid="spending-lines">
      <h3 className="m-0 mb-1 text-lg font-semibold">Spending lines from the report</h3>
      <p className="m-0 mb-4 text-sm text-slate-500">
        Programmes and grants that change no tax or benefit. Their figures are the report&apos;s or official costings, not PolicyEngine estimates, and are not in the modelled total above.
      </p>
      <div className="overflow-x-auto">
        <table className="data-table compact">
          <thead>
            <tr>
              <th>Measure</th>
              <th>Applies in</th>
              <th>Figure</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {lines.map((m) => {
              const costs = m.official_cost ?? [];
              return (
                <tr key={m.id}>
                  <td>{m.name}</td>
                  <td>{m.coverage}</td>
                  <td>{costs.length ? costs.map((c) => `${formatMillions(c.value_m)} in ${fiscalYear(c.year)}`).join("; ") : "No figure published yet"}</td>
                  <td>
                    {costs.length
                      ? costs.map((c, i) => (
                          <a key={i} href={c.source_url} className="underline">
                            {c.paragraph || "Source"}
                          </a>
                        ))
                      : ""}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
