import { REPO_ISSUES } from "../utils/measures";

function IssueLink({ issue }) {
  if (!issue) return null;
  return (
    <>
      {" "}
      <a className="text-slate-500 underline" href={`${REPO_ISSUES}/${issue}`}>
        (issue {issue})
      </a>
    </>
  );
}

export default function MethodologyTab({ data }) {
  const engine = data.engine;
  return (
    <div className="tab-body">
      <section className="panel mb-6">
        <h3 className="m-0 mb-2 text-lg font-semibold">Basis</h3>
        <ul className="m-0 list-disc pl-5 text-sm text-slate-700">
          {Object.entries(data.basis).map(([key, text]) => (
            <li key={key}>{text}</li>
          ))}
        </ul>
      </section>
      <section className="panel mb-6">
        <h3 className="m-0 mb-2 text-lg font-semibold">What the data do not hold</h3>
        <ul className="m-0 list-disc pl-5 text-sm text-slate-700">
          {data.data_limits.map((limit) => (
            <li key={limit.key}>
              {limit.reason}
              <IssueLink issue={limit.issue} />
            </li>
          ))}
        </ul>
      </section>
      <section className="panel mb-6">
        <h3 className="m-0 mb-2 text-lg font-semibold">Where the model needs care</h3>
        <ul className="m-0 list-disc pl-5 text-sm text-slate-700">
          {data.model_limits.map((limit) => (
            <li key={limit.key}>
              {limit.reason}
              <IssueLink issue={limit.issue} />
            </li>
          ))}
        </ul>
      </section>
      <p className="text-sm text-slate-500" data-testid="replication-line">
        {engine.validated_pair && engine.label
          ? `Engine and data: ${engine.label}`
          : `policyengine-uk ${engine.policyengine_uk}, dataset ${engine.dataset} (not the pinned engine and data pair)`}
        .
      </p>
    </div>
  );
}
