// Chips for the computable measures; selection is kept in ?policies=. Each
// chip shows the name only; the description lives on the Policies card.
// Selected chips change fill and border only. On a phone the chips sit in
// one scrolling row so the figures are on the first screen.
export default function PolicySelector({ measures, selected, onChange, onOpenPolicies }) {
  const toggle = (id) =>
    onChange(selected.includes(id) ? selected.filter((s) => s !== id) : [...selected, id]);
  const headline = measures.filter((m) => m.in_headline !== false);
  const scenarios = measures.filter((m) => m.in_headline === false);
  const chip = (m) => (
    <button
      key={m.id}
      type="button"
      aria-pressed={selected.includes(m.id)}
      className={`selector-chip ${selected.includes(m.id) ? "active" : ""}`}
      onClick={() => toggle(m.id)}
    >
      <span className="inline-block h-3 w-3 shrink-0 rounded-full align-middle" style={{ background: m.colour }} />
      <span className="ml-2 font-semibold text-slate-800">{m.name}</span>
    </button>
  );
  return (
    <div className="mb-4">
      <div className="chip-row" role="group" aria-label="Measures">
        {headline.map(chip)}
      </div>
      {scenarios.length > 0 && (
        <>
          <p className="m-0 mt-3 mb-2 text-xs text-slate-500">Separate scenarios, not in the headline: they reach people outside the review&apos;s age group.</p>
          <div className="chip-row" role="group" aria-label="Separate scenarios">
            {scenarios.map(chip)}
          </div>
        </>
      )}
      {onOpenPolicies && (
        <button type="button" className="mt-2 text-sm underline text-slate-600" onClick={onOpenPolicies}>
          What each measure does
        </button>
      )}
    </div>
  );
}
