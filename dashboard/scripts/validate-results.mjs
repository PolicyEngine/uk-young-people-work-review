// Build-time check of public/data/results.json: the schema the page needs,
// the banner while any measure is a placeholder or a mock, MOCK ids only in
// a mock file, and no unvalidated engine pair in a public build. Mirrors
// young_people_work.publication.validate_public.
import { readFileSync } from "node:fs";

const path = process.argv[2] ?? new URL("../public/data/results.json", import.meta.url);
const data = JSON.parse(readFileSync(path));
const errors = [];
const STATUSES = ["placeholder", "mock", "provisional", "final"];
for (const key of ["schema_version", "status", "years", "measures", "age_bands", "context", "households", "net_income_curves", "basis", "engine"]) {
  if (!(key in data)) errors.push(`missing ${key}`);
}
if (!STATUSES.includes(data.status)) errors.push(`status ${data.status} is not one of ${STATUSES.join(", ")}`);
if (data.measures?.some((m) => m.placeholder) && !["placeholder", "mock"].includes(data.status)) {
  errors.push("placeholder measures need status 'placeholder' or 'mock'");
}
if (["placeholder", "mock"].includes(data.status) && !data.banner) errors.push(`${data.status} figures need banner text`);
if (data.measures?.some((m) => String(m.id).startsWith("mock_")) && data.status !== "mock") errors.push("mock_ measures need status 'mock'");
if (data.status === "mock" && !String(data.banner).includes("MOCK")) errors.push("a mock file's banner must say MOCK");
if (process.env.NEXT_PUBLIC_MOCK === "1" && !["mock", "placeholder"].includes(data.status)) {
  errors.push("a MOCK build (NEXT_PUBLIC_MOCK=1) reads a mock or placeholder file only");
}
if (["provisional", "final"].includes(data.status) && !data.engine?.validated_pair) {
  errors.push("a public build needs the certified engine and data pair");
}
for (const m of data.measures ?? []) {
  if (!m.computable && m.budgetary_impact !== null) errors.push(`${m.id}: not computable but carries a figure`);
  if (m.computable && !Array.isArray(m.budgetary_impact)) errors.push(`${m.id}: computable but has no figures`);
}
if (errors.length) {
  console.error(errors.join("\n"));
  process.exit(1);
}
console.log(`results.json ok: ${data.measures.length} measures, status ${data.status}`);
