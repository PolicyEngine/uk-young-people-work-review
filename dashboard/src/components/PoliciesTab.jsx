import { detailsFor } from "../utils/policyDetails";
import { REPO_ISSUES, ROUTE_LABELS } from "../utils/measures";

// One card per candidate recommendation: the single home of each measure's
// description, who it affects and how it works. A measure that is not
// computable shows its reason, never a figure.
export default function PoliciesTab({ measures }) {
  return (
    <div className="tab-body">
      <p className="m-0 mb-4 text-sm text-slate-600">
        The candidate measures below were written before the final report from its terms of reference and the interim report. On the day they are replaced by the report&apos;s own recommendations. Measures aimed at 14- and 15-year-olds, such as school work experience, are outside the dashboard&apos;s age range and are listed only as spending lines.
      </p>
      <div className="grid gap-4 md:grid-cols-2">
        {measures.map((m) => {
          const details = detailsFor(m);
          return (
            <article key={m.id} id={`policy-${m.id}`} className="panel" data-testid={`policy-${m.id}`}>
              <p className="eyebrow m-0 text-slate-500">{ROUTE_LABELS[m.route]}</p>
              <h3 className="m-0 mt-1 text-lg font-semibold">{m.name}</h3>
              <p className="m-0 mt-2 text-sm text-slate-700">{m.description}</p>
              {details && (
                <>
                  <p className="m-0 mt-2 text-sm text-slate-600">
                    <strong>Who it affects:</strong> {details.whoIsAffected}
                  </p>
                  <p className="m-0 mt-2 text-sm text-slate-600">
                    <strong>How it works:</strong> {details.howItWorks}
                  </p>
                </>
              )}
              <p className="m-0 mt-2 text-sm text-slate-500">
                Recommendation: {m.recommendation}. Applies in: {m.coverage}.
              </p>
              {!m.computable && (
                <p className="caveat-card m-0 mt-3 pl-3 text-sm" data-testid="route-reason">
                  {m.route_reason}
                </p>
              )}
              {m.issues.length > 0 && (
                <p className="m-0 mt-2 text-xs text-slate-500">
                  Open questions:{" "}
                  {m.issues.map((n, i) => (
                    <span key={n}>
                      {i > 0 && ", "}
                      <a className="underline" href={`${REPO_ISSUES}/${n}`}>
                        issue {n}
                      </a>
                    </span>
                  ))}
                </p>
              )}
            </article>
          );
        })}
      </div>
    </div>
  );
}
