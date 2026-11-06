import { describe, expect, it } from "vitest";
import results from "../../public/data/results.json";
import { ageBandRows } from "../components/AgeBandChart";
import { waterfallRows, wrapLabel } from "../components/WaterfallChart";
import { costRows } from "../components/BudgetaryImpactChart";
import { decileRows } from "../components/DistributionalChart";
import { catalogue, fiscalShort, formatMillions, formatPounds, headlineIds, packageFor, toCsv, totalByYear } from "./measures";

describe("measure utils", () => {
  it("gives a colour to computable measures only", () => {
    for (const m of catalogue(results)) expect(Boolean(m.colour)).toBe(m.computable);
  });

  it("formats a missing figure as not computable, not £0", () => {
    expect(formatMillions(null)).toBe("Not computable");
    expect(formatMillions(1500)).toBe("£1.5bn");
    expect(formatMillions(-250)).toBe("-£250m");
  });

  it("totals by year", () => {
    const computable = results.measures.filter((m) => m.computable);
    const rows = totalByYear(computable, results.years);
    expect(rows).toHaveLength(results.years.length);
    expect(rows[0].total).toBeCloseTo(computable.reduce((s, m) => s + m.budgetary_impact[0].value_m, 0));
  });

  it("keeps a missing year as null, never 0", () => {
    const m = { id: "a", budgetary_impact: [{ year: 2027, value_m: 5 }] };
    const rows = totalByYear([m], [2027, 2028]);
    expect(rows[1].a).toBeNull();
    expect(rows[1].incomplete).toBe(true);
    expect(decileRows([{ id: "a", decile: [] }])[0].a).toBeNull();
  });

  it("uses the package run for the net when the selection is the package", () => {
    const a = { id: "a", budgetary_impact: [{ year: 2027, value_m: 100 }] };
    const b = { id: "b", budgetary_impact: [{ year: 2027, value_m: -40 }] };
    const pkg = { members: ["a", "b"], budgetary_impact: [{ year: 2027, value_m: 55 }] };
    expect(packageFor({ package: pkg }, ["b", "a"])).toBe(pkg);
    expect(packageFor({ package: pkg }, ["a"])).toBeNull();
    expect(costRows([a, b], [2027], pkg)[0].total).toBe(55);
    expect(costRows([a, b], [2027], null)[0].total).toBe(60);
  });

  it("colours costs and savings from different ramps", () => {
    const data = {
      measures: [
        { id: "c", computable: true, budgetary_impact: [{ year: 2027, value_m: 100 }] },
        { id: "s", computable: true, budgetary_impact: [{ year: 2027, value_m: -100 }] },
      ],
    };
    const [c, s] = catalogue(data);
    expect(c.colour).not.toBe(s.colour);
  });

  it("defaults to the headline measures only", () => {
    const ids = headlineIds(results.measures);
    expect(ids).not.toContain("work_allowance_all_ages");
    expect(ids).toContain("youth_standard_allowance");
  });

  it("names measures in CSV headers and shortens year ticks", () => {
    expect(toCsv([{ a: 1 }], { a: "Measure A" }).split("\n")[0]).toBe("Measure A");
    expect(fiscalShort(2027)).toBe("27-28");
  });

  it("ends the waterfall at the net total", () => {
    const computable = results.measures.filter((m) => m.computable);
    const rows = waterfallRows(computable, 2030);
    const net = rows.at(-1);
    expect(net.net).toBe(true);
    expect(net.value).toBeCloseTo(rows.slice(0, -1).reduce((s, r) => s + r.value, 0));
  });

  it("builds one age band row per band in results.json", () => {
    const computable = results.measures.filter((m) => m.computable);
    const rows = ageBandRows(computable, results.age_bands);
    expect(rows.map((r) => r.age_band)).toEqual(results.age_bands);
    expect(rows[1][computable[0].id]).toBe(computable[0].age_band[1].avg_change_gbp);
  });

  it("formats negative pounds with the sign first", () => {
    expect(formatPounds(-35.3)).toBe("-£35");
  });

  it("wraps long measure names for the waterfall axis", () => {
    expect(wrapLabel("Higher work allowances (illustrative)")).toEqual(["Higher work", "allowances", "(illustrative)"]);
  });

  it("writes CSV with escaping", () => {
    expect(toCsv([{ a: "x,y", b: 1 }])).toBe('a,b\n"x,y",1');
  });
});
