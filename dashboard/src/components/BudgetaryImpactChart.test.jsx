import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { CostBars, costRows } from "./BudgetaryImpactChart";

afterEach(cleanup);

// A saving and a cost in one year: with stackOffset="sign" the saving sits
// wholly below zero and the cost wholly above, and the stack's top is the
// sum of the costs, not the net (the template's earlier artefact).
describe("cost chart with a cost and a saving", () => {
  it("draws the saving below zero and the cost above it", () => {
    const measures = [
      { id: "save", name: "Saving", colour: "teal", budgetary_impact: [{ year: 2027, value_m: -500 }] },
      { id: "cost", name: "Cost", colour: "amber", budgetary_impact: [{ year: 2027, value_m: 800 }] },
    ];
    const rows = costRows(measures, [2027], null);
    const { container } = render(<CostBars rows={rows} measures={measures} width={600} height={300} />);
    const rects = [...container.querySelectorAll(".recharts-bar-rectangle path, .recharts-bar-rectangle rect")];
    expect(rects.length).toBe(2);
    const zero = container.querySelector(".recharts-reference-line line");
    const zeroY = Number(zero.getAttribute("y1"));
    const box = (el) => {
      const y = Number(el.getAttribute("y"));
      const h = Number(el.getAttribute("height"));
      return [Math.min(y, y + h), Math.max(y, y + h)];
    };
    const [save, cost] = rects.map(box);
    expect(save[0]).toBeGreaterThanOrEqual(zeroY - 0.5);
    expect(cost[1]).toBeLessThanOrEqual(zeroY + 0.5);
    // Cost is 800 against a saving of 500: its bar is taller.
    expect(cost[1] - cost[0]).toBeGreaterThan(save[1] - save[0]);
  });
});
