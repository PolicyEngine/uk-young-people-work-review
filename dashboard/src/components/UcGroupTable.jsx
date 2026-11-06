import { formatPounds } from "../utils/measures";

const GROUPS = {
  NO_REQUIREMENTS: "No work requirements (including the health element group)",
  INTERVIEW_ONLY: "Work-focused interview only",
  WORK_PREPARATION: "Work preparation",
  ALL_REQUIREMENTS: "All work requirements",
};

// Average change for adults on UC by work-related group. Present only once
// model mode has run.
export default function UcGroupTable({ measures }) {
  const withGroups = measures.filter((m) => m.uc_group?.length);
  if (!withGroups.length) return null;
  return (
    <section className="panel mb-6">
      <h3 className="m-0 mb-1 text-lg font-semibold">By UC work-related group</h3>
      <p className="m-0 mb-4 text-sm text-slate-500">Average change in household net income of adults on UC, by their work-related group, £ a year.</p>
      <div className="overflow-x-auto">
        <table className="data-table compact">
          <thead>
            <tr>
              <th>Group</th>
              {withGroups.map((m) => (
                <th key={m.id}>{m.name}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Object.entries(GROUPS).map(([code, label]) => (
              <tr key={code}>
                <td>{label}</td>
                {withGroups.map((m) => (
                  <td key={m.id}>{formatPounds(m.uc_group.find((r) => r.uc_group === code)?.avg_change_gbp)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
