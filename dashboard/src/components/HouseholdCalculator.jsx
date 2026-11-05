import { formatPounds } from "../utils/measures";
import NetIncomeChart from "./NetIncomeChart";

// Preset households, precomputed by the pipeline. In the template the values
// are an arithmetic sketch of monthly UC; the real calculator runs the full
// model, and presets marked full model only show no figure until then.
export default function HouseholdCalculator({ households, curves, measures }) {
  const computable = measures.filter((m) => m.computable);
  return (
    <div className="tab-body">
      <section className="panel mb-6">
        <h3 className="m-0 mb-1 text-lg font-semibold">Example young people</h3>
        <p className="m-0 mb-4 text-sm text-slate-500">
          Monthly Universal Credit under current law and each modelled measure, 2027-28. Placeholder arithmetic.
        </p>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Household</th>
                <th>Current law</th>
                {computable.map((m) => (
                  <th key={m.id}>{m.name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {households.map((h) => (
                <tr key={h.id} data-testid={`household-${h.id}`}>
                  <td>{h.label}</td>
                  <td>{h.full_model_only ? "Full model on the day" : formatPounds(h.baseline_uc_monthly)}</td>
                  {computable.map((m) => (
                    <td key={m.id}>{h.full_model_only ? "" : formatPounds(h.reform_uc_monthly[m.id])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {curves.map((curve) => (
        <NetIncomeChart key={curve.preset} curve={curve} measures={computable} />
      ))}
    </div>
  );
}
