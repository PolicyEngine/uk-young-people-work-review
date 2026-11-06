import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import results from "../../public/data/results.json";
import { bannerFor } from "./Banner";
import Dashboard, { VIEWS } from "./Dashboard";

beforeEach(() => window.history.replaceState(null, "", "/"));
afterEach(cleanup);

describe("Dashboard", () => {
  it("shows the placeholder banner", () => {
    render(<Dashboard data={results} />);
    expect(screen.getByTestId("placeholder-banner")).toHaveTextContent("placeholder figures");
  });

  it("shows the MOCK banner for a mock file, whatever the measure flags say", () => {
    const mock = {
      ...results,
      status: "mock",
      banner: "MOCK: drill figures",
      measures: results.measures.map((m) => ({ ...m, placeholder: false })),
    };
    render(<Dashboard data={mock} />);
    expect(screen.getByTestId("mock-banner")).toHaveTextContent("MOCK");
    for (const view of VIEWS) {
      fireEvent.click(screen.getByRole("tab", { name: view.label }));
      expect(screen.getByTestId("mock-banner")).toBeInTheDocument();
    }
  });

  it("forces the MOCK banner on a drill build", () => {
    expect(bannerFor({ ...results, status: "provisional" }, true).kind).toBe("mock");
    expect(bannerFor({ ...results, status: "provisional" }, false)).toBeNull();
  });

  it("publishes no likelihood and links issues", () => {
    window.history.replaceState(null, "", "/?tab=policies");
    render(<Dashboard data={results} />);
    expect(document.body.textContent).not.toMatch(/Likelihood/);
    expect(document.querySelector('a[href$="/issues/2"]')).not.toBeNull();
  });

  it("has the five AB2026 views", () => {
    render(<Dashboard data={results} />);
    const tabs = within(screen.getByRole("tablist", { name: "Views" })).getAllByRole("tab");
    expect(tabs.map((t) => t.textContent)).toEqual(VIEWS.map((v) => v.label));
  });

  it("keeps the tab in the address", () => {
    render(<Dashboard data={results} />);
    fireEvent.click(screen.getByRole("tab", { name: "Methodology" }));
    expect(window.location.search).toContain("tab=method");
    expect(screen.getByTestId("replication-line")).toHaveTextContent("a6299504");
  });

  it("opens the tab named in the address", () => {
    window.history.replaceState(null, "", "/?tab=policies");
    render(<Dashboard data={results} />);
    expect(screen.getByRole("tab", { name: "Policies" })).toHaveAttribute("aria-selected", "true");
  });

  it("shows a reason, never a figure, for measures that are not computable", () => {
    window.history.replaceState(null, "", "/?tab=policies");
    render(<Dashboard data={results} />);
    for (const m of results.measures.filter((x) => !x.computable)) {
      const card = screen.getByTestId(`policy-${m.id}`);
      expect(within(card).getByTestId("route-reason")).toHaveTextContent(m.route_reason);
      expect(card.textContent).not.toMatch(/£0\b/);
    }
  });

  it("reads the measure list from results.json, not a fixed list", () => {
    const extra = {
      ...results,
      measures: [...results.measures, { ...results.measures[0], id: "added_measure", name: "Added measure" }],
    };
    window.history.replaceState(null, "", "/?tab=policies");
    render(<Dashboard data={extra} />);
    expect(screen.getByTestId("policy-added_measure")).toBeInTheDocument();
  });

  it("has an age band view that reads the bands from results.json", () => {
    window.history.replaceState(null, "", "/?tab=impact&sub=age");
    render(<Dashboard data={results} />);
    expect(screen.getByRole("tab", { name: "By age" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("Average change by age band")).toBeInTheDocument();
  });

  it("never shows arithmetic for presets that need the full model", () => {
    window.history.replaceState(null, "", "/?tab=household");
    render(<Dashboard data={results} />);
    for (const h of results.households.filter((x) => x.full_model_only)) {
      expect(within(screen.getByTestId(`household-${h.id}`)).getByText("Full model on the day")).toBeInTheDocument();
    }
  });

  it("drops unknown policies from the address and falls back to the headline set", () => {
    window.history.replaceState(null, "", "/?policies=nope");
    render(<Dashboard data={results} />);
    const pressed = screen.getAllByRole("button", { pressed: true });
    expect(pressed.length).toBe(results.measures.filter((m) => m.computable && m.in_headline).length);
  });

  it("lists spending lines apart from the modelled total, never as £0", () => {
    render(<Dashboard data={results} />);
    const table = screen.getByTestId("spending-lines");
    expect(table.textContent).toContain("No figure published yet");
    expect(table.textContent).not.toMatch(/£0\b/);
  });
});
