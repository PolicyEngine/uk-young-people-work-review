"""G0 check: the dataset build and the installed engine are one pair.

A Microcosm build may run only under the policyengine-uk version it was
built on. A build under another engine version gives national figures that
are invalid, and the "unvalidated under this engine" label does not make them
usable. ``python -m young_people_work.pair_check <release dir>`` reads every
``policyengine-uk==<version>`` the build's release files record, compares
each with the installed policyengine-uk and exits 1 on any difference.

The release files record the build engine only in some gate details, so a
build that records none fails too, unless ``--build-engine`` states the
version from the data owner's release note. Light: reads JSON, no simulation.
"""

import argparse
import importlib.metadata
import re
import sys
from pathlib import Path

ENGINE_PIN = re.compile(r"policyengine[-_]uk\s*==\s*([0-9][0-9A-Za-z.+-]*)")


def recorded_engines(release_dir: Path) -> set[str]:
    """Every policyengine-uk version pinned in the build's release JSON files."""
    found: set[str] = set()
    for path in sorted(Path(release_dir).glob("*.json")):
        found.update(ENGINE_PIN.findall(path.read_text(errors="replace")))
    return found


def installed_engine() -> str | None:
    try:
        return importlib.metadata.version("policyengine-uk")
    except importlib.metadata.PackageNotFoundError:
        return None


def problems(release_dir: Path, installed: str | None, stated: str | None = None) -> list[str]:
    """What stops the pair; an empty list means the pair holds."""
    if installed is None:
        return ["policyengine-uk is not installed in this environment"]
    out = []
    recorded = recorded_engines(release_dir)
    if stated:
        recorded.add(stated)
    if not recorded:
        out.append(
            f"no policyengine-uk version recorded in {release_dir}: "
            "state the build engine with --build-engine"
        )
    for version in sorted(recorded - {installed}):
        out.append(
            f"the build was made with policyengine-uk {version}, "
            f"but {installed} is installed: change the environment or the build"
        )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("release_dir", type=Path, help="Folder with the build's release JSON files")
    parser.add_argument("--build-engine", help="policyengine-uk version the build was made with")
    args = parser.parse_args(argv)
    found = problems(args.release_dir, installed_engine(), args.build_engine)
    for problem in found:
        print(problem, file=sys.stderr)
    if not found:
        print(f"Pair holds: build and environment both on policyengine-uk {installed_engine()}")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
