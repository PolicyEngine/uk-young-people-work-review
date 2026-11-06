import { fiscalYear, formatPence } from "../utils/measures";
import NetIncomeChart from "./NetIncomeChart";

// Example households, precomputed by the pipeline: from the full model in
// model mode, from a placeholder sketch of monthly UC in the template. Each
// row names only the measures that change it.
export default function HouseholdCalculator({ households, curves, measures, status }) {
  const computable = measures.filter((m) => m.computable);
  const byId = Object.fromEntries(computable.map((m) => [m.id, m]));
  const sketch = households.some((h) => h.source === "sketch");
  const year = households[0]?.year;
  return (
    <div className="tab-body">
      <section className="panel mb-6">
        <h3 className="m-0 mb-1 text-lg font-semibold">Example young people</h3>
        <p className="m-0 mb-4 text-sm text-slate-500">
          Monthly Universal Credit{sketch ? "" : " and net income"} under current law and each measure that changes it{year ? `, ${fiscalYear(year)}` : ""}.
          {sketch ? " Placeholder arithmetic covering UC only; the full model replaces it on the day." : ""}
          {status === "mock" ? " MOCK drill figures." : ""}
        </p>
        <div className="grid gap-4 md:grid-cols-2">
          {households.map((h) => (
            <article key={h.id} className="metric-card" data-testid={`household-${h.id}`}>
              <h4 className="m-0 text-base font-semibold text-slate-800">{h.label}</h4>
              {h.full_model_only && h.baseline_uc_monthly === null ? (
                <p className="m-0 mt-2 text-sm text-slate-600">Full model on the day</p>
              ) : (
                <dl className="m-0 mt-2 grid grid-cols-[1fr_auto] gap-x-4 gap-y-1 text-sm">
                  <dt className="text-slate-600">UC under current law</dt>
                  <dd className="m-0 text-right font-semibold">{formatPence(h.baseline_uc_monthly)} a month</dd>
                  {h.baseline_net_income_monthly !== undefined && (
                    <>
                      <dt className="text-slate-600">Net income under current law</dt>
                      <dd className="m-0 text-right font-semibold">{formatPence(h.baseline_net_income_monthly)} a month</dd>
                    </>
                  )}
                  {(h.changed_by ?? []).map((mid) => {
                    const change = h.reform_uc_monthly[mid] - h.baseline_uc_monthly;
                    const netChange =
                      h.reform_net_income_monthly && h.baseline_net_income_monthly !== undefined
                        ? h.reform_net_income_monthly[mid] - h.baseline_net_income_monthly
                        : null;
                    return (
                      <div key={mid} className="contents">
                        <dt className="text-slate-600">{byId[mid]?.name ?? mid}</dt>
                        <dd className="m-0 text-right">
                          UC {change >= 0 ? "+" : ""}
                          {formatPence(change)}
                          {netChange !== null && `; net income ${netChange >= 0 ? "+" : ""}${formatPence(netChange)}`} a month
                        </dd>
                      </div>
                    );
                  })}
                  {(h.changed_by ?? []).length === 0 && <dd className="col-span-2 m-0 text-slate-600">No change under any modelled measure.</dd>}
                </dl>
              )}
            </article>
          ))}
        </div>
      </section>
      {curves.map((curve) => (
        <NetIncomeChart key={curve.preset} curve={curve} measures={computable} sketch={sketch} />
      ))}
    </div>
  );
}
