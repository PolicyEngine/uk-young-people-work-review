"""G0 check: the dataset build and the installed engine are one pair.

A Microcosm build may run only under the policyengine-uk version it was
built on. A build under another engine version gives national figures that
are invalid, and the "unvalidated under this engine" label does not make them
usable. ``python -m young_people_work.pair_check <release dir>`` reads every
policyengine-uk version the build's release files record, compares each with
the installed policyengine-uk and exits 1 on any difference.

A release folder records the build engine in up to three places, and any one
is enough (``terminal_gates.json`` is not needed):
- ``build_manifest.json``: ``runtime["policyengine-uk"]``;
- ``release_manifest.json``: ``built_with_model_package.version`` and each
  ``compatible_model_packages[].specifier`` pinned with ``==``;
- any ``policyengine-uk==<version>`` string, such as a gate's details in
  ``terminal_gates.json``.
A folder that records none fails too, unless ``--build-engine`` states the
version from the data owner's release note. Light: reads JSON, no simulation.
"""

import argparse
import importlib.metadata
import json
import re
import sys
from pathlib import Path

ENGINE_PIN = re.compile(r"policyengine[-_]uk\s*==\s*([0-9][0-9A-Za-z.+-]*)")


def _is_uk(package) -> bool:
    name = str(package.get("name", "")) if isinstance(package, dict) else ""
    return name.replace("_", "-") == "policyengine-uk"


def _manifest_engines(data) -> set[str]:
    """policyengine-uk versions in the build and release manifests' fields."""
    if not isinstance(data, dict):
        return set()
    found = set()
    runtime = data.get("runtime")
    if isinstance(runtime, dict) and runtime.get("policyengine-uk"):
        found.add(str(runtime["policyengine-uk"]))
    built = data.get("built_with_model_package")
    if _is_uk(built) and built.get("version"):
        found.add(str(built["version"]))
    for package in data.get("compatible_model_packages") or []:
        specifier = str(package.get("specifier", "")) if _is_uk(package) else ""
        if specifier.startswith("=="):
            found.add(specifier[2:].strip())
    return found


def recorded_engines(release_dir: Path) -> set[str]:
    """Every policyengine-uk version the build's release JSON files record."""
    found: set[str] = set()
    for path in sorted(Path(release_dir).glob("*.json")):
        text = path.read_text(errors="replace")
        found.update(ENGINE_PIN.findall(text))
        try:
            found.update(_manifest_engines(json.loads(text)))
        except json.JSONDecodeError:
            pass
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
