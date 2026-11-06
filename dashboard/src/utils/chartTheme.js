// The one JS home of colour literals (docs/COLOURS.md). Roles copied from the
// AB2026 dashboard: teals for what households gain, ambers for what they lose,
// greys for no change and for the baseline or official figure.
export const CHART_COLOURS = {
  gain: "#319795",
  gainLight: "#81E6D9",
  loss: "#D97706",
  lossLight: "#FBBF24",
  noChange: "#9CA3AF",
  before: "#9CA3AF",
  after: "#319795",
  official: "#6B7280",
  zeroLine: "#374151",
  grid: "#E5E7EB",
  tick: "#6B7280",
  text: "#374151",
  surface: "#FFFFFF",
  highlight: "#285E61",
  net: "#101828",
};

// The measures' colour ramps, from the AB2026 dashboard (POLICY_RAMPS):
// measures that cost the Exchequer (households gain) in teals, savings
// (households lose) in ambers, each darkest first. Each direction's
// measures take its steps in order of size, largest darkest; with more
// measures than steps the steps repeat with a dash in the legend swatch,
// and every measure is named in the legend and the tooltip.
export const POLICY_RAMPS = {
  cost: ["#0F766E", "#0D9488", "#14B8A6", "#2DD4BF", "#5EEAD4"],
  saving: ["#78350F", "#92400E", "#B45309", "#D97706", "#F59E0B", "#FBBF24"],
};

export function measureColour(direction, rank) {
  const ramp = direction === "saving" ? POLICY_RAMPS.saving : POLICY_RAMPS.cost;
  return ramp[rank % ramp.length];
}

export const WINNERS_LOSERS_SERIES = [
  { key: "gain_more_5", label: "Gain more than 5%", colour: CHART_COLOURS.gain },
  { key: "gain_less_5", label: "Gain less than 5%", colour: CHART_COLOURS.gainLight },
  { key: "no_change", label: "No change", colour: CHART_COLOURS.noChange },
  { key: "lose_less_5", label: "Lose less than 5%", colour: CHART_COLOURS.lossLight },
  { key: "lose_more_5", label: "Lose more than 5%", colour: CHART_COLOURS.loss },
];
