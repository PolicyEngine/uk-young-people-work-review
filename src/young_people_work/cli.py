"""Command line for the young people and work review dashboard.

- ``generate``: write ``data/results.json`` (placeholder, or model mode from
  the run files), and ``manifest.json`` beside it in model mode.
- ``model-run``: one measure, or the package, through the full model on the
  frozen data. Heavy: takes ``/tmp/pe-heavy.lock`` and waits for 14 GB.
- ``household``: one preset household from the full model.
- ``households``: a household file (CSV or JSON, the drill's specimen
  sheet) on the scoring basis, one row per household and measure.
- ``reconcile``: model figures against official costings; fails when a gap
  over 10% has no reason.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

from young_people_work import pipeline, runtime_identity
from young_people_work.household import PRESETS_BY_ID, calculate
from young_people_work.reforms import REFORMS, get_reform
from young_people_work.years import POLICY_YEARS

RESULTS = pipeline.REPO_ROOT / "data" / "results.json"
DASHBOARD_COPY = pipeline.REPO_ROOT / "dashboard" / "public" / "data" / "results.json"


def _reforms(ids: str | None):
    if not ids:
        return [r for r in REFORMS if r.computable]
    return [get_reform(i) for i in ids.split(",")]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="young-people-work")
    commands = parser.add_subparsers(dest="command", required=True)

    generate = commands.add_parser("generate", help="Write data/results.json")
    generate.add_argument("--mode", choices=["placeholder", "model"], default="placeholder")
    generate.add_argument(
        "--status",
        choices=["placeholder", "mock", "provisional"],
        help="placeholder mode: placeholder (default) or mock; model mode: provisional (default) or mock",
    )
    generate.add_argument("--runs", type=Path, default=None, help="Run files (model mode)")
    generate.add_argument(
        "--no-curves", action="store_true", help="Model mode: skip the net income curves"
    )
    generate.add_argument("--out", type=Path, default=RESULTS)
    generate.add_argument("--dashboard-copy", type=Path, default=DASHBOARD_COPY)

    model_run = commands.add_parser(
        "model-run", help="One measure (or the package) through the full model"
    )
    target = model_run.add_mutually_exclusive_group(required=True)
    target.add_argument("--measure")
    target.add_argument(
        "--package", action="store_true", help="The headline measures as one reform"
    )
    model_run.add_argument("--runs", type=Path, default=None)
    model_run.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Score an uncommitted tree (never for publication)",
    )

    household = commands.add_parser(
        "household", help="One preset household (needs the model extra)"
    )
    household.add_argument("preset", choices=sorted(PRESETS_BY_ID))
    household.add_argument("--reform")
    household.add_argument("--year", type=int, default=POLICY_YEARS[0])

    households = commands.add_parser("households", help="Score a household file on the drill basis")
    households.add_argument("path", type=Path)
    households.add_argument(
        "--reforms", help="Comma-separated measure ids (default: every computable measure)"
    )
    households.add_argument("--out", type=Path, help="CSV output (default: standard output)")

    reconcile = commands.add_parser("reconcile", help="Model figures against official costings")
    reconcile.add_argument(
        "official", type=Path, help="CSV: measure_id, year, value_m, basis[, reason]"
    )
    reconcile.add_argument("--results", type=Path, default=RESULTS)
    reconcile.add_argument("--out", type=Path, default=Path("reconciliation.csv"))
    reconcile.add_argument("--tolerance", type=float, default=0.10)

    args = parser.parse_args(argv)
    if args.command == "generate":
        return _generate(args)
    if args.command == "model-run":
        return _model_run(args)
    if args.command == "household":
        reform = get_reform(args.reform) if args.reform else None
        print(json.dumps(calculate(args.preset, reform, year=args.year), indent=2))
        return 0
    if args.command == "households":
        return _households(args)
    return _reconcile(args)


def _generate(args) -> int:
    from young_people_work import model

    if args.mode == "placeholder":
        results = pipeline.build_placeholder_results()
        if args.status == "mock":
            results["status"] = "mock"
            results["banner"] = pipeline.MOCK_BANNER
        pipeline.write_results(results, args.out, args.dashboard_copy)
        print(f"Wrote {args.out} and {args.dashboard_copy}")
        return 0
    commit = runtime_identity.require_clean_tree()
    from young_people_work.household import precompute_presets

    computable = [r for r in REFORMS if r.computable]
    households = precompute_presets(computable)
    curves = [] if args.no_curves else _model_curves(computable)
    results = pipeline.build_model_results(
        args.runs or model.RUNS_DIR,
        status=args.status or "provisional",
        households=households,
        curves=curves,
        commit=commit,
    )
    pipeline.write_results(results, args.out, args.dashboard_copy)
    pipeline.write_manifest(results, args.out.parent / "manifest.json", commit)
    print(f"Wrote {args.out}, {args.dashboard_copy} and {args.out.parent / 'manifest.json'}")
    return 0


def _model_curves(reforms) -> list[dict]:
    from young_people_work.household import CURVE_HOURS, PRESETS, simulate, to_situation

    year = POLICY_YEARS[0]
    curves = []
    for preset_id in pipeline.CURVE_PRESETS:
        preset = next(p for p in PRESETS if p["id"] == preset_id)
        rows = []
        for hours in CURVE_HOURS:
            situation = to_situation({**preset, "weekly_hours": hours}, year)
            row = {
                "hours": hours,
                "baseline": simulate(situation, None, year)["net_income_monthly"],
            }
            for reform in reforms:
                row[reform.id] = simulate(situation, reform, year)["net_income_monthly"]
            rows.append(row)
        curves.append(
            {
                "preset": preset_id,
                "label": preset["label"],
                "hourly_wage": preset["hourly_wage"],
                "rows": rows,
            }
        )
    return curves


def _model_run(args) -> int:
    from young_people_work import model

    commit = (
        runtime_identity.git_sha() if args.allow_dirty else runtime_identity.require_clean_tree()
    )
    if args.package:
        members = [r for r in REFORMS if r.computable and r.in_headline]
        reform = model.package_reform(members)
    else:
        reform = get_reform(args.measure)
        if not reform.computable:
            print(f"{reform.id} is {reform.route.value}: nothing to run", file=sys.stderr)
            return 1
    runs = args.runs or model.RUNS_DIR
    with model.heavy_lock():
        output = model.run_measure(reform)
    output["commit"] = commit
    output["dirty"] = bool(args.allow_dirty and not runtime_identity.tree_is_clean())
    model.write_run(output, runs / f"{reform.id}.json")
    print(f"Wrote {runs / (reform.id + '.json')}")
    return 0


def _households(args) -> int:
    from young_people_work.household import score_households

    rows = score_households(args.path, _reforms(args.reforms), runtime_identity.git_sha())
    handle = args.out.open("w", newline="") if args.out else sys.stdout
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["id"])
    writer.writeheader()
    writer.writerows(rows)
    if args.out:
        handle.close()
    return 0


def _reconcile(args) -> int:
    from young_people_work.reconcile import reconcile

    results = json.loads(args.results.read_text())
    with args.official.open(newline="") as handle:
        official = list(csv.DictReader(handle))
    rows, failures = reconcile(results, official, args.tolerance)
    with args.out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["measure_id"])
        writer.writeheader()
        writer.writerows(rows)
    print(
        f"Wrote {args.out}: {len(rows)} rows, {len(failures)} gaps over {args.tolerance:.0%} without a reason"
    )
    for failure in failures:
        print(f"  {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
