"use client";

import { useEffect, useMemo, useState } from "react";
import { catalogue, headlineIds } from "../utils/measures";
import Banner, { bannerFor } from "./Banner";
import BaselineTab from "./BaselineTab";
import HouseholdCalculator from "./HouseholdCalculator";
import MethodologyTab from "./MethodologyTab";
import PoliciesTab from "./PoliciesTab";
import PopulationImpactTab, { SUB_VIEWS } from "./PopulationImpactTab";
import ViewTabs from "./ViewTabs";

// Tab pattern from the AB2026 dashboard: VIEWS, with the state in ?tab=,
// ?sub= and ?policies=. Each fact appears once; other tabs link to it.
export const VIEWS = [
  { value: "impact", label: "Population impact" },
  { value: "household", label: "Example households" },
  { value: "baseline", label: "Baseline" },
  { value: "policies", label: "Policies" },
  { value: "method", label: "Methodology" },
];

function readState(measures) {
  const computable = measures.filter((m) => m.computable).map((m) => m.id);
  const headline = headlineIds(measures);
  if (typeof window === "undefined") return { tab: "impact", sub: "cost", policies: headline };
  const params = new URLSearchParams(window.location.search);
  const tab = VIEWS.some((v) => v.value === params.get("tab")) ? params.get("tab") : "impact";
  const sub = SUB_VIEWS.some((v) => v.value === params.get("sub")) ? params.get("sub") : "cost";
  const asked = params.get("policies")?.split(",").filter((id) => computable.includes(id));
  return { tab, sub, policies: asked?.length ? asked : headline };
}

export default function Dashboard({ data }) {
  const measures = useMemo(() => catalogue(data), [data]);
  const [state, setState] = useState(() => readState(measures));

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    params.set("tab", state.tab);
    if (state.tab === "impact") params.set("sub", state.sub);
    else params.delete("sub");
    params.set("policies", state.policies.join(","));
    window.history.replaceState(null, "", `${window.location.pathname}?${params}`);
  }, [state]);

  const update = (patch) => setState((s) => ({ ...s, ...patch }));

  return (
    <main className="app-shell min-h-screen">
      <Banner banner={bannerFor(data)} />
      <div className="title-row">
        <div className="mx-auto max-w-[1200px] px-4 py-4 sm:px-6">
          <h1>Young people and work review: costs and who would benefit</h1>
        </div>
      </div>
      <div className="relative z-[1] mx-auto max-w-[1200px] px-4 py-8 sm:px-6">
        <ViewTabs views={VIEWS} active={state.tab} onChange={(tab) => update({ tab })} />
        {state.tab === "impact" && (
          <PopulationImpactTab
            data={data}
            measures={measures}
            selected={state.policies}
            onSelect={(policies) => update({ policies })}
            sub={state.sub}
            onSub={(sub) => update({ sub })}
            onOpenPolicies={() => update({ tab: "policies" })}
          />
        )}
        {state.tab === "household" && (
          <HouseholdCalculator households={data.households} curves={data.net_income_curves} measures={measures} status={data.status} />
        )}
        {state.tab === "baseline" && <BaselineTab data={data} />}
        {state.tab === "policies" && <PoliciesTab measures={measures} />}
        {state.tab === "method" && <MethodologyTab data={data} />}
      </div>
    </main>
  );
}
