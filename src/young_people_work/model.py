"""Model mode: national figures from the full model on the frozen data.

One measure per process (``young-people-work model-run --measure ID``), run
under the heavy-run lock. Within the process only one microsimulation is
alive at a time: the baseline's arrays are extracted for every policy year,
the baseline is dropped, and only then is the reform built. Each run writes
one JSON file under ``data/runs/`` (git-ignored: these are not public until
the reconciler signs them off); ``young-people-work generate --mode model``
assembles them into ``results.json``.

Outputs, adapted from the AB2026 dashboard's calculators:
- budgetary impact: minus the change in ``gov_balance``, £m, so positive is a
  cost to the Exchequer;
- deciles: average change in household net income by equivalised household
  income decile, and the change as a share of the decile's net income;
- winners and losers: share of people by decile whose household gains or
  loses more or less than 5% (a change under £1 a year is no change);
- age bands: average change in household net income of people in each band,
  by their own age (AB2026 ``AgeImpactCalculator``), person-weighted;
- UC group: the same, for adults by UC work-related group;
- region: average change by ITL1 region and nation, and the total;
- poverty: BHC and AHC rates for all people, children and 16-24-year-olds;
- people affected: people in households whose net income changes by £1 or
  more a year.

Every cell counts the survey households behind it, and
``publication.apply_floor`` blanks any cell under the disclosure floor
before the file is written; the counts themselves are never written.
"""

import json
import os
import shutil
import signal
import subprocess
import threading
import time
from collections.abc import Callable, Iterable
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np

from young_people_work import data_build, publication, runtime_identity
from young_people_work.models import Reform, Route
from young_people_work.years import POLICY_YEARS, fiscal_label

AGE_BANDS = ["16-17", "18-20", "21-24", "25 and over"]
AGE_EDGES = [(16, 18), (18, 21), (21, 25), (25, 200)]
NO_CHANGE_GBP = 1.0
BIG_CHANGE = 0.05
LOCK_PATH = Path("/tmp/pe-heavy.lock")
LOCK_LABEL = "young-people-work"
MIN_FREE_GB = 22.0
RUNS_DIR = runtime_identity.REPO_ROOT / "data" / "runs"

HOUSEHOLD_VARIABLES = (
    "gov_balance",
    "household_net_income",
    "household_weight",
    "household_income_decile",
    "household_count_people",
    "region",
    "household_id",
)
PERSON_VARIABLES = (
    "age",
    "person_weight",
    "person_household_id",
    "uc_work_related_group_apart_from_earnings",
    "is_adult",
)
PERSON_MAPPED = ("in_poverty_bhc", "in_poverty_ahc")


# --- the heavy-run lock -------------------------------------------------
#
# The machine protocol: the lock is a FILE holding "<pid> <label>", created
# with noclobber (O_CREAT | O_EXCL, so a held file or legacy directory lock
# makes the caller wait), removed only by its owner, and the run waits for
# 22 GB of free plus inactive memory once it holds the lock.


def free_inactive_gb() -> float | None:
    """vm_stat free plus inactive memory in GB (macOS), or None elsewhere."""
    if shutil.which("vm_stat") is None:
        return None
    out = subprocess.run(["vm_stat"], capture_output=True, text=True, check=False).stdout
    page = None
    pages = 0
    for line in out.splitlines():
        if "page size of" in line:
            page = int(line.split("page size of")[1].split()[0])
        if line.startswith(("Pages free:", "Pages inactive:")):
            pages += int(line.split(":")[1].strip().rstrip("."))
    return None if page is None else pages * page / 1e9


def lock_owner(lock_path: Path) -> str | None:
    """The pid field of the lock file, or None if there is no such file."""
    try:
        fields = Path(lock_path).read_text().split()
    except OSError:
        return None
    return fields[0] if fields else None


def _try_lock(lock_path: Path, label: str) -> bool:
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w") as handle:
        handle.write(f"{os.getpid()} {label}\n")
    return True


def _release_lock(lock_path: Path) -> None:
    """Remove the lock only if this process wrote it."""
    if lock_owner(lock_path) == str(os.getpid()):
        Path(lock_path).unlink(missing_ok=True)


def _exit_on_term(signum, frame):
    raise SystemExit(128 + signum)


@contextmanager
def heavy_lock(
    lock_path: Path | None = None,
    min_free_gb: float | None = None,
    poll: float = 15.0,
    label: str = LOCK_LABEL,
):
    """Take the machine-wide heavy-run lock, then wait for memory; release on
    exit (SIGTERM included). Defaults are read at call time, so tests can
    point ``LOCK_PATH`` at a scratch file."""
    lock_path = Path(LOCK_PATH if lock_path is None else lock_path)
    min_free_gb = MIN_FREE_GB if min_free_gb is None else min_free_gb
    while not _try_lock(lock_path, label):
        time.sleep(poll)
    main = threading.current_thread() is threading.main_thread()
    previous = signal.signal(signal.SIGTERM, _exit_on_term) if main else None
    try:
        while True:
            free = free_inactive_gb()
            if free is None or free >= min_free_gb:
                break
            time.sleep(poll)
        yield
    finally:
        if main:
            signal.signal(signal.SIGTERM, previous)
        _release_lock(lock_path)


# --- simulations ----------------------------------------------------------


def fetch_dataset() -> Path:
    """The pinned build's file (``data_build.DATA_BUILD``), downloaded once
    into the Hugging Face cache with the saved read-only login."""
    from huggingface_hub import hf_hub_download

    runtime_identity.ensure_data_token()
    return Path(
        hf_hub_download(
            repo_id=data_build.HF_REPO,
            filename=data_build.DATA_BUILD.hf_path,
            repo_type=data_build.HF_REPO_TYPE,
        )
    )


def _runtime_dataset(path: Path):
    """The dataset object policyengine_uk reads, as policyengine.py's managed
    helper builds it from a local file."""
    from policyengine_uk.data.dataset_schema import UKMultiYearDataset, UKSingleYearDataset

    if UKMultiYearDataset.validate_file_path(str(path), False):
        return UKMultiYearDataset(str(path))
    if UKSingleYearDataset.validate_file_path(str(path), False):
        return UKSingleYearDataset(str(path))
    return str(path)


def build_microsimulation(scenario=None, dataset: str | None = None):
    """A Microsimulation on the pinned build, with the engine it was built on.

    policyengine_uk is loaded directly: no policyengine.py release covers
    the pair (``data_build.DATA_BUILD``). Refuses an installed policyengine-uk
    other than the build's, and a file whose SHA-256 is not the build's.
    """
    from policyengine_uk import Microsimulation

    build = data_build.DATA_BUILD
    runtime_identity.require_build_engine()
    path = Path(dataset) if dataset is not None else fetch_dataset()
    sha = _checked_sha256(path)
    if sha != build.sha256:
        raise RuntimeError(
            f"{path.name} has SHA-256 {sha}, not that of build {build.id} ({build.sha256})."
        )
    kwargs = {} if scenario is None else {"scenario": scenario}
    sim = Microsimulation(dataset=_runtime_dataset(path), **kwargs)
    sim.young_people_provenance = {
        "runtime_dataset_uri": f"hf://{data_build.HF_REPO}/{build.hf_path}",
        "runtime_dataset_revision": build.id,
        "runtime_dataset_source": str(path),
        "runtime_dataset_sha256": sha,
        "managed_by": "young_people_work.model (policyengine_uk directly)",
    }
    return sim


_SHA_CACHE: dict[tuple, str] = {}


def _checked_sha256(path: Path) -> str:
    """The file's SHA-256, hashed once per file version."""
    stat = path.stat()
    key = (str(path.resolve()), stat.st_size, stat.st_mtime_ns)
    if key not in _SHA_CACHE:
        _SHA_CACHE[key] = runtime_identity.file_sha256(path)
    return _SHA_CACHE[key]


def _values(result) -> np.ndarray:
    return np.asarray(getattr(result, "values", result))


def extract(sim, years: Iterable[int]) -> dict[int, dict[str, np.ndarray]]:
    """The arrays the figures need, by year, as plain numpy (no weights lost)."""
    out: dict[int, dict[str, np.ndarray]] = {}
    for year in years:
        arrays: dict[str, np.ndarray] = {}
        for name in HOUSEHOLD_VARIABLES:
            arrays[name] = _values(sim.calculate(name, year, map_to="household"))
        for name in PERSON_VARIABLES:
            arrays[name] = _values(sim.calculate(name, year, map_to="person"))
        for name in PERSON_MAPPED:
            arrays[f"person_{name}"] = _values(sim.calculate(name, year, map_to="person"))
        arrays["person_household_net_income"] = _values(
            sim.calculate("household_net_income", year, map_to="person")
        )
        out[year] = arrays
    return out


# --- figures --------------------------------------------------------------


def _round(value: float, digits: int = 0) -> float:
    return float(round(float(value), digits))


def _band_index(age: np.ndarray) -> np.ndarray:
    index = np.full(age.shape, -1)
    for i, (low, high) in enumerate(AGE_EDGES):
        index[(age >= low) & (age < high)] = i
    return index


def figures(
    base: dict[str, np.ndarray], reform: dict[str, np.ndarray], year: int
) -> dict[str, Any]:
    """Every published output for one year, before the disclosure floor."""
    w = base["household_weight"]
    people = base["household_count_people"]
    change = reform["household_net_income"] - base["household_net_income"]
    income = base["household_net_income"]
    decile = base["household_income_decile"]
    budget = -float(np.sum((reform["gov_balance"] - base["gov_balance"]) * w)) / 1e6

    deciles, winners = [], []
    for d in range(1, 11):
        m = decile == d
        weight = w[m]
        total = float(weight.sum())
        avg = float(np.sum(change[m] * weight) / total) if total else None
        base_income = float(np.sum(income[m] * weight))
        pct = 100 * float(np.sum(change[m] * weight)) / base_income if base_income else None
        deciles.append(
            {"decile": d, "avg_change_gbp": avg, "pct_change": pct, "n_households": int(m.sum())}
        )
        pw = weight * people[m]
        rel = np.divide(
            change[m], np.abs(income[m]), out=np.zeros(int(m.sum())), where=income[m] != 0
        )
        groups = {
            "gain_more_5": (change[m] >= NO_CHANGE_GBP) & (rel > BIG_CHANGE),
            "gain_less_5": (change[m] >= NO_CHANGE_GBP) & (rel <= BIG_CHANGE),
            "no_change": np.abs(change[m]) < NO_CHANGE_GBP,
            "lose_less_5": (change[m] <= -NO_CHANGE_GBP) & (rel >= -BIG_CHANGE),
            "lose_more_5": (change[m] <= -NO_CHANGE_GBP) & (rel < -BIG_CHANGE),
        }
        denom = float(pw.sum())
        row = {"decile": d, "n_households": int(m.sum())}
        for key, mask in groups.items():
            row[key] = 100 * float(pw[mask].sum()) / denom if denom else None
        winners.append(row)

    # People: each gets their household's change, by own age.
    p_w = base["person_weight"]
    p_change = reform["person_household_net_income"] - base["person_household_net_income"]
    p_house = base["person_household_id"]
    bands = _band_index(base["age"])
    age_rows = []
    for i, label in enumerate(AGE_BANDS):
        m = bands == i
        total = float(p_w[m].sum())
        age_rows.append(
            {
                "age_band": label,
                "avg_change_gbp": float(np.sum(p_change[m] * p_w[m]) / total) if total else None,
                "n_households": int(len(np.unique(p_house[m]))),
            }
        )

    uc_rows = []
    groups = base["uc_work_related_group_apart_from_earnings"].astype(str)
    adult = base["is_adult"].astype(bool)
    for group in sorted(set(groups[adult]) - {"NOT_A_CLAIMANT"}):
        m = adult & (groups == group)
        total = float(p_w[m].sum())
        uc_rows.append(
            {
                "uc_group": group,
                "avg_change_gbp": float(np.sum(p_change[m] * p_w[m]) / total) if total else None,
                "people_k": total / 1e3,
                "n_households": int(len(np.unique(p_house[m]))),
            }
        )

    region = base["region"].astype(str)
    region_rows = []
    for name in sorted(set(region)):
        m = region == name
        total = float(w[m].sum())
        region_rows.append(
            {
                "region": name,
                "avg_change_gbp": float(np.sum(change[m] * w[m]) / total) if total else None,
                "total_change_m": float(np.sum(change[m] * w[m])) / 1e6,
                "n_households": int(m.sum()),
            }
        )

    young = (base["age"] >= 16) & (base["age"] < 25)
    child = base["age"] < 16
    poverty = []
    for measure in ("bhc", "ahc"):
        b = base[f"person_in_poverty_{measure}"].astype(float)
        r = reform[f"person_in_poverty_{measure}"].astype(float)
        for group, m in (("all", np.ones_like(young)), ("children", child), ("aged_16_24", young)):
            total = float(p_w[m].sum())
            poverty.append(
                {
                    "basis": measure,
                    "group": group,
                    "baseline_rate_pct": 100 * float(np.sum(b[m] * p_w[m])) / total
                    if total
                    else None,
                    "reform_rate_pct": 100 * float(np.sum(r[m] * p_w[m])) / total
                    if total
                    else None,
                    "change_k": float(np.sum((r[m] - b[m]) * p_w[m])) / 1e3,
                    "n_households": int(len(np.unique(p_house[m]))),
                }
            )

    affected = np.abs(change) >= NO_CHANGE_GBP
    return {
        "year": year,
        "budgetary_impact_m": budget,
        "people_affected_k": float(np.sum(people[affected] * w[affected])) / 1e3,
        "affected_households": int(affected.sum()),
        "decile": deciles,
        "winners_losers": winners,
        "age_band": age_rows,
        "uc_group": uc_rows,
        "region": region_rows,
        "poverty": poverty,
    }


def run(
    scenario,
    years: Iterable[int] = POLICY_YEARS,
    baseline_scenario=None,
    build: Callable = build_microsimulation,
    upper_scenario=None,
) -> dict[str, Any]:
    """Baseline, reform and optional upper bound, one simulation alive at a time."""
    years = list(years)
    sim = build(baseline_scenario)
    identity = {"engine": runtime_identity.engine_block(sim)}
    base = extract(sim, years)
    del sim
    sim = build(scenario)
    reform = extract(sim, years)
    del sim
    out = {"identity": identity, "years": [figures(base[y], reform[y], y) for y in years]}
    if upper_scenario is not None:
        sim = build(upper_scenario)
        upper = extract(sim, years)
        del sim
        out["upper"] = [
            {"year": y, "budgetary_impact_m": figures(base[y], upper[y], y)["budgetary_impact_m"]}
            for y in years
        ]
    return out


# --- package: the headline set as one combined reform ---------------------


def _chain(modifiers: list[Callable]) -> Callable:
    def package_modifier(sim):
        for modifier in modifiers:
            modifier(sim)

    package_modifier.__qualname__ = (
        "package_modifier[" + ",".join(m.__qualname__ for m in modifiers) + "]"
    )
    return package_modifier


def package_reform(members: list[Reform]) -> Reform:
    """The published set as one reform, so interactions are scored once."""
    if not members:
        raise ValueError("A package needs at least one measure")
    changes: dict[str, dict[str, Any]] = {}
    for member in members:
        for path, values in (member.parameter_changes or {}).items():
            if path in changes and changes[path] != values:
                raise ValueError(f"{path} is set differently by two package members")
            changes[path] = dict(values)
    modifiers = [m.simulation_modifier for m in members if m.simulation_modifier is not None]
    timings = {m.applied_before_data_load for m in members if m.simulation_modifier is not None}
    if len(timings) > 1:
        raise ValueError("Package members' modifiers run at different times; score them apart")
    return Reform(
        id="package",
        name="Selected package",
        description="The headline measures run together as one reform.",
        recommendation="The headline measures together",
        likelihood="high",
        route=Route.DASHBOARD_STRUCTURAL if modifiers else Route.DASHBOARD_PARAM,
        route_reason="Run as one reform, so interactions between measures are counted once.",
        placeholder=all(m.placeholder for m in members),
        parameter_changes=changes or None,
        simulation_modifier=_chain(modifiers) if modifiers else None,
        applied_before_data_load=bool(timings and timings.pop()),
    )


# --- assembling a measure's published entry -------------------------------


def _floor(rows: list[dict[str, Any]], keys: list[str]) -> list[dict[str, Any]]:
    out = publication.apply_floor(rows, keys)
    for row in out:
        row.setdefault("suppressed", False)
    return out


def measure_figures(run_output: dict[str, Any]) -> dict[str, Any]:
    """The figure fields of a results.json measure, floored and rounded."""
    years = run_output["years"]
    last = years[-1]
    budget = [
        {
            "year": y["year"],
            "fiscal_year": fiscal_label(y["year"]),
            "value_m": _round(y["budgetary_impact_m"]),
        }
        for y in years
    ]
    decile = _floor(
        [
            {
                **r,
                "avg_change_gbp": None
                if r["avg_change_gbp"] is None
                else _round(r["avg_change_gbp"]),
                "pct_change": None if r["pct_change"] is None else _round(r["pct_change"], 2),
            }
            for r in last["decile"]
        ],
        ["avg_change_gbp", "pct_change"],
    )
    wl_keys = ["gain_more_5", "gain_less_5", "no_change", "lose_less_5", "lose_more_5"]
    winners = _floor(
        [
            {**r, **{k: None if r[k] is None else _round(r[k], 1) for k in wl_keys}}
            for r in last["winners_losers"]
        ],
        wl_keys,
    )
    age = _floor(
        [
            {
                **r,
                "avg_change_gbp": None
                if r["avg_change_gbp"] is None
                else _round(r["avg_change_gbp"]),
            }
            for r in last["age_band"]
        ],
        ["avg_change_gbp"],
    )
    uc = _floor(
        [
            {
                **r,
                "avg_change_gbp": None
                if r["avg_change_gbp"] is None
                else _round(r["avg_change_gbp"]),
                "people_k": _round(r["people_k"]),
            }
            for r in last["uc_group"]
        ],
        ["avg_change_gbp", "people_k"],
    )
    region = _floor(
        [
            {
                **r,
                "avg_change_gbp": None
                if r["avg_change_gbp"] is None
                else _round(r["avg_change_gbp"]),
                "total_change_m": _round(r["total_change_m"]),
            }
            for r in last["region"]
        ],
        ["avg_change_gbp", "total_change_m"],
    )
    poverty = _floor(
        [
            {
                **r,
                "baseline_rate_pct": None
                if r["baseline_rate_pct"] is None
                else _round(r["baseline_rate_pct"], 1),
                "reform_rate_pct": None
                if r["reform_rate_pct"] is None
                else _round(r["reform_rate_pct"], 1),
                "change_k": _round(r["change_k"]),
            }
            for r in last["poverty"]
        ],
        ["baseline_rate_pct", "reform_rate_pct", "change_k"],
    )
    affected = (
        _round(last["people_affected_k"])
        if last["affected_households"] >= publication.DISCLOSURE_FLOOR
        else None
    )
    out = {
        "budgetary_impact": budget,
        "decile": decile,
        "winners_losers": winners,
        "age_band": age,
        "uc_group": uc,
        "region": region,
        "poverty": poverty,
        "people_affected_k": affected,
        "distribution_year": last["year"],
    }
    if "upper" in run_output:
        out["budgetary_impact_upper"] = [
            {
                "year": y["year"],
                "fiscal_year": fiscal_label(y["year"]),
                "value_m": _round(y["budgetary_impact_m"]),
            }
            for y in run_output["upper"]
        ]
    return out


def run_measure(
    reform: Reform, years: Iterable[int] = POLICY_YEARS, build: Callable = build_microsimulation
) -> dict[str, Any]:
    """One measure's run file: its receipt, identity and raw figures.

    A computable measure that a live data limit refuses never runs.
    """
    from young_people_work.publication import refuse_data_limited

    refuse_data_limited([reform])
    out = run(
        reform.to_scenario(),
        years,
        baseline_scenario=reform.to_baseline_scenario(),
        build=build,
        upper_scenario=reform.to_upper_bound_scenario(),
    )
    out["id"] = reform.id
    return out


def write_run(output: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2, default=float) + "\n")


def read_runs(directory: Path) -> dict[str, dict[str, Any]]:
    runs = {}
    for path in sorted(directory.glob("*.json")):
        data = json.loads(path.read_text())
        runs[data["id"]] = data
    return runs
