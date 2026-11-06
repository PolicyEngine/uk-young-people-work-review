import { measureColour } from "./chartTheme";

const lastValue = (m) => m.budgetary_impact?.at(-1)?.value_m ?? 0;

// The catalogue: every view reads the measure list from results.json, never
// from a hard-coded list, so a measure added to the registry shows everywhere.
// Colour by direction (cost teal, saving amber), largest darkest.
export function catalogue(data) {
  const computable = data.measures.filter((m) => m.computable);
  const rank = {};
  for (const direction of ["cost", "saving"]) {
    computable
      .filter((m) => (lastValue(m) < 0 ? "saving" : "cost") === direction)
      .sort((a, b) => Math.abs(lastValue(b)) - Math.abs(lastValue(a)))
      .forEach((m, i) => {
        rank[m.id] = measureColour(direction, i);
      });
  }
  return data.measures.map((m) => ({ ...m, colour: m.computable ? rank[m.id] : null }));
}

// The measures in the headline package by default: those the registry marks
// in_headline. All-ages and older stand-ins are separate scenarios.
export function headlineIds(measures) {
  return measures.filter((m) => m.computable && m.in_headline !== false).map((m) => m.id);
}

export const ROUTE_LABELS = {
  "dashboard-param": "Modelled: parameter change",
  "dashboard-structural": "Modelled: structural change",
  ledger: "Spending line only",
  "not-computable": "Not computable with current data",
  "needs-pe-uk-first": "Needs a model change first",
};

export const REPO_ISSUES = "https://github.com/PolicyEngine/uk-young-people-work-review/issues";

// Banner and tile notes follow the results file's status, never fixed text.
export const STATUS_NOTES = {
  placeholder: "Placeholder figures",
  mock: "MOCK drill figures",
  provisional: "Provisional",
  final: "",
};

export function fiscalYear(year) {
  return `${year}-${String((year + 1) % 100).padStart(2, "0")}`;
}

export function fiscalShort(year) {
  return `${String(year % 100).padStart(2, "0")}-${String((year + 1) % 100).padStart(2, "0")}`;
}

export function formatMillions(value) {
  if (value === null || value === undefined) return "Not computable";
  const sign = value < 0 ? "-" : "";
  const abs = Math.abs(value);
  if (abs >= 1000) return `${sign}£${(abs / 1000).toFixed(1)}bn`;
  return `${sign}£${Math.round(abs)}m`;
}

export function formatPounds(value) {
  if (value === null || value === undefined) return "n/a";
  const sign = value < 0 ? "-" : "";
  return `${sign}£${Math.abs(Math.round(value)).toLocaleString("en-GB")}`;
}

export function formatPence(value) {
  if (value === null || value === undefined) return "n/a";
  const sign = value < 0 ? "-" : "";
  return `${sign}£${Math.abs(value).toLocaleString("en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// A missing year is null (not computable), never 0. The total sums the
// cells that exist and says when one is missing.
export function totalByYear(measures, years) {
  return years.map((year) => {
    const row = { year };
    let total = 0;
    let missing = false;
    for (const m of measures) {
      const cell = m.budgetary_impact?.find((r) => r.year === year);
      const value = cell?.value_m ?? null;
      row[m.id] = value;
      if (value === null) missing = true;
      else total += value;
    }
    row.total = measures.length ? total : null;
    row.incomplete = missing;
    return row;
  });
}

export function sameSet(a, b) {
  return a.length === b.length && a.every((x) => b.includes(x));
}

// The package's figures when the selection is the package run, else null:
// a different selection is a sum of single-measure figures, labelled so.
export function packageFor(data, selected) {
  const pkg = data.package;
  if (!pkg || !sameSet(pkg.members ?? [], selected)) return null;
  return pkg;
}

// CSV with readable headers: a measure id becomes its name.
export function toCsv(rows, labels = {}) {
  if (!rows.length) return "";
  const keys = Object.keys(rows[0]);
  const escape = (v) => (typeof v === "string" && /[",\n]/.test(v) ? `"${v.replaceAll('"', '""')}"` : v ?? "");
  const header = keys.map((k) => escape(labels[k] ?? k));
  return [header.join(","), ...rows.map((r) => keys.map((k) => escape(r[k])).join(","))].join("\n");
}

export function labelsFor(measures) {
  return Object.fromEntries(measures.map((m) => [m.id, m.name]));
}
