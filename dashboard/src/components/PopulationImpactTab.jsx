import { useState } from "react";
import { fiscalYear, formatMillions, packageFor, STATUS_NOTES } from "../utils/measures";
import AgeBandChart from "./AgeBandChart";
import BudgetaryImpactChart from "./BudgetaryImpactChart";
import DistributionalChart from "./DistributionalChart";
import PolicySelector from "./PolicySelector";
import PovertyView from "./PovertyView";
import RegionView from "./RegionView";
import SpendingLines from "./SpendingLines";
import StatTiles from "./StatTiles";
import UcGroupTable from "./UcGroupTable";
import ViewTabs from "./ViewTabs";
import WaterfallChart from "./WaterfallChart";
import WinnersLosersChart from "./WinnersLosersChart";

export const SUB_VIEWS = [
  { value: "cost", label: "Cost" },
  { value: "deciles", label: "By income decile" },
  { value: "age", label: "By age" },
  { value: "winners", label: "Who gains and loses" },
  { value: "poverty", label: "Poverty" },
  { value: "region", label: "By region" },
];

function peopleAffected(chosen, pkg) {
  if (pkg) return pkg.people_affected_k ?? null;
  if (chosen.length !== 1) return null;
  return chosen[0].people_affected_k ?? null;
}

export default function PopulationImpactTab({ data, measures, selected, onSelect, sub, onSub, onOpenPolicies }) {
  const computable = measures.filter((m) => m.computable);
  const chosen = computable.filter((m) => selected.includes(m.id));
  const pkg = packageFor(data, selected);
  const [year, setYear] = useState(data.years[data.years.length - 1]);
  const net = pkg
    ? pkg.budgetary_impact?.find((r) => r.year === year)?.value_m ?? null
    : chosen.length
      ? chosen.reduce((sum, m) => sum + (m.budgetary_impact?.find((r) => r.year === year)?.value_m ?? 0), 0)
      : null;
  const note = STATUS_NOTES[data.status] ?? "";
  const affected = peopleAffected(chosen, pkg);
  const notComputable = measures.filter((m) => !m.computable).length;
  return (
    <div className="tab-body">
      <PolicySelector measures={computable} selected={selected} onChange={onSelect} onOpenPolicies={onOpenPolicies} />
      <div className="mb-3 flex flex-wrap items-center gap-2 text-sm text-slate-700">
        <label htmlFor="tile-year">Year</label>
        <select id="tile-year" className="selector-select" value={year} onChange={(e) => setYear(Number(e.target.value))}>
          {data.years.map((y) => (
            <option key={y} value={y}>
              {fiscalYear(y)}
            </option>
          ))}
        </select>
      </div>
      <StatTiles
        tiles={[
          {
            label: `Net cost, ${fiscalYear(year)}`,
            value: formatMillions(net),
            note: [note, pkg ? "Selected measures run together" : chosen.length > 1 ? "Sum of single-measure figures" : ""].filter(Boolean).join(". "),
          },
          {
            label: "People in households affected",
            value: affected === null ? "Select one measure" : `${Math.round(affected).toLocaleString("en-GB")},000`,
            note: affected === null ? "Shown for one measure or the package" : note,
          },
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
          <BudgetaryImpactChart measures={chosen} years={data.years} basis={data.basis.cost} pkg={pkg} />
          <WaterfallChart
            measures={chosen}
            year={year}
            basis={data.basis.cost}
            netValue={pkg ? pkg.budgetary_impact?.find((r) => r.year === year)?.value_m ?? null : null}
          />
          <SpendingLines measures={measures} />
        </>
      )}
      {sub === "deciles" && <DistributionalChart measures={chosen} basis={data.basis.distribution} pkg={pkg} />}
      {sub === "age" && (
        <>
          <AgeBandChart measures={chosen} bands={data.age_bands} basis={data.basis.age_band} />
          <UcGroupTable measures={chosen} />
        </>
      )}
      {sub === "winners" && <WinnersLosersChart measures={chosen.length ? chosen : computable} pkg={pkg} />}
      {sub === "poverty" && <PovertyView measures={chosen} pkg={pkg} year={fiscalYear(data.years.at(-1))} />}
      {sub === "region" && <RegionView measures={chosen} />}
    </div>
  );
}
