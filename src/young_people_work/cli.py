"""Command line: ``young-people-work generate`` and ``young-people-work household``."""

import argparse
import json
from pathlib import Path

from young_people_work import pipeline
from young_people_work.household import PRESETS_BY_ID, calculate
from young_people_work.reforms import get_reform


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="young-people-work")
    commands = parser.add_subparsers(dest="command", required=True)

    generate = commands.add_parser("generate", help="Write data/results.json")
    generate.add_argument("--mode", choices=["placeholder", "model"], default="placeholder")
    generate.add_argument("--out", type=Path, default=pipeline.REPO_ROOT / "data" / "results.json")
    generate.add_argument(
        "--dashboard-copy",
        type=Path,
        default=pipeline.REPO_ROOT / "dashboard" / "public" / "data" / "results.json",
    )

    household = commands.add_parser("household", help="One preset household (needs the model extra)")
    household.add_argument("preset", choices=sorted(PRESETS_BY_ID))
    household.add_argument("--reform")
    household.add_argument("--year", type=int)

    args = parser.parse_args(argv)
    if args.command == "generate":
        results = (
            pipeline.build_placeholder_results()
            if args.mode == "placeholder"
            else pipeline.build_model_results()
        )
        pipeline.write_results(results, args.out, args.dashboard_copy)
        print(f"Wrote {args.out} and {args.dashboard_copy}")
        return 0
    reform = get_reform(args.reform) if args.reform else None
    kwargs = {"year": args.year} if args.year else {}
    print(json.dumps(calculate(args.preset, reform, **kwargs), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
