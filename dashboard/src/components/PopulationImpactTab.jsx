import { formatMillions } from "../utils/measures";
import AgeBandChart from "./AgeBandChart";
import BudgetaryImpactChart from "./BudgetaryImpactChart";
import DistributionalChart from "./DistributionalChart";
import PolicySelector from "./PolicySelector";
import StatTiles from "./StatTiles";
import ViewTabs from "./ViewTabs";
import WaterfallChart from "./WaterfallChart";
import WinnersLosersChart from "./WinnersLosersChart";

export const SUB_VIEWS = [
  { value: "cost", label: "Cost" },
  { value: "deciles", label: "By income decile" },
  { value: "age", label: "By age band" },
  { value: "winners", label: "Who gains and loses" },
];

export default function PopulationImpactTab({ data, measures, selected, onSelect, sub, onSub, onOpenPolicies }) {
  const computable = measures.filter((m) => m.computable);
  const chosen = computable.filter((m) => selected.includes(m.id));
  const lastYear = data.years[data.years.length - 1];
  const net = chosen.reduce(
    (sum, m) => sum + (m.budgetary_impact.find((r) => r.year === lastYear)?.value_m ?? 0),
    0,
  );
  const notComputable = measures.filter((m) => !m.computable).length;
  return (
    <div className="tab-body">
      <PolicySelector measures={computable} selected={selected} onChange={onSelect} />
      <StatTiles
        tiles={[
          { label: `Net cost, ${lastYear}-${String((lastYear + 1) % 100).padStart(2, "0")}`, value: formatMillions(net), note: "Placeholder" },
          { label: "Measures modelled", value: String(computable.length), note: "Placeholder parameter changes" },
          {
            label: "Measures not modelled",
            value: String(notComputable),
            note: (
              <button type="button" className="underline" onClick={onOpenPolicies}>
                See the reason for each
              </button>
            ),
          },
        ]}
      />
      <ViewTabs views={SUB_VIEWS} active={sub} onChange={onSub} label="Population impact" sub />
      {sub === "cost" && (
        <>
          <BudgetaryImpactChart measures={chosen} years={data.years} basis={data.basis.cost} />
          <WaterfallChart measures={chosen} year={lastYear} />
        </>
      )}
      {sub === "deciles" && <DistributionalChart measures={chosen} basis={data.basis.distribution} />}
      {sub === "age" && <AgeBandChart measures={chosen} bands={data.age_bands} basis={data.basis.age_band} />}
      {sub === "winners" && <WinnersLosersChart measure={chosen[0] ?? computable[0]} />}
    </div>
  );
}
