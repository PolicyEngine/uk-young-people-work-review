"""What produced a results file: installed versions, data, code and limits.

Copied in shape from the AB2026 dashboard's ``runtime_identity`` and
``certified_data``. Model mode records all of it in each receipt and in
``manifest.json``; placeholder and mock files carry the pinned strings only.
"""

import hashlib
import importlib.metadata
import json
import subprocess
from pathlib import Path
from typing import Any

from young_people_work.data_build import DATA_BUILD, LABEL

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGES = ("policyengine", "policyengine-uk", "policyengine-core")

# The pinned pair (data_build.DATA_BUILD, uv.lock, README): the Microcosm
# build and the policyengine-uk and policyengine-core versions it was built
# and certified on. No policyengine.py release covers the pair, so
# ``policyengine`` is None. tests/test_runtime_identity.py checks these
# against uv.lock, and the model job against the installed packages.
PINNED = {
    "policyengine": None,
    "policyengine_uk": DATA_BUILD.engine,
    "policyengine_core": DATA_BUILD.core,
    "dataset": DATA_BUILD.id,
    "dataset_sha256": DATA_BUILD.sha256,
}


def ensure_data_token() -> None:
    """Set HUGGING_FACE_TOKEN from the saved Hugging Face login if it is
    unset, so the token never goes on a command line."""
    import os

    if os.environ.get("HUGGING_FACE_TOKEN"):
        return
    try:
        from huggingface_hub import get_token
    except ImportError:
        return
    token = get_token()
    if token:
        os.environ["HUGGING_FACE_TOKEN"] = token


def installed_versions() -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for name in PACKAGES:
        try:
            out[name.replace("-", "_")] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            out[name.replace("-", "_")] = None
    return out


def require_build_engine() -> str:
    """The installed policyengine-uk, if it is the one DATA_BUILD was made on.

    Model mode and the household path both call this, so neither scores on
    another engine. Raises otherwise: never mix a build with another engine.
    """
    installed = installed_versions()["policyengine_uk"]
    if installed != DATA_BUILD.engine:
        raise RuntimeError(
            f"policyengine-uk {installed} is installed, but build {DATA_BUILD.id} "
            f"was made on {DATA_BUILD.engine}. Never mix a build with another "
            "engine version."
        )
    return installed


def git_sha(root: Path = REPO_ROOT) -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def tree_is_clean(root: Path = REPO_ROOT) -> bool:
    """No tracked file differs from HEAD (untracked outputs are allowed)."""
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return False
    return out.strip() == ""


def require_clean_tree(root: Path = REPO_ROOT) -> str:
    """The commit a model run scores. Refuses a dirty tree."""
    if not tree_is_clean(root):
        raise RuntimeError(
            "Model mode scores a commit: commit or stash tracked changes first "
            "(git status --untracked-files=no is not empty)."
        )
    sha = git_sha(root)
    if sha is None:
        raise RuntimeError("Model mode needs a git checkout")
    return sha


def limits_digest() -> str:
    """SHA-256 of the data and model limit registries, as published."""
    from young_people_work import data_limits, model_limits

    payload = {
        "data": [vars(limit) for limit in data_limits.LIMITS],
        "missing": [vars(item) for item in data_limits.MISSING_INPUTS],
        "model": [vars(limit) for limit in model_limits.LIMITS],
    }
    text = json.dumps(payload, sort_keys=True, default=list)
    return hashlib.sha256(text.encode()).hexdigest()


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dataset_provenance(microsim) -> dict[str, Any]:
    """The dataset a simulation built by ``model.build_microsimulation``
    loaded, with the SHA-256 of the file itself."""
    record = dict(getattr(microsim, "young_people_provenance", {}) or {})
    keep = {
        key: value
        for key, value in record.items()
        if isinstance(value, (str, int, float, bool)) or value is None
    }
    source = keep.pop("runtime_dataset_source", None)  # a local path: never published
    if source and "runtime_dataset_sha256" not in keep and Path(source).is_file():
        keep["runtime_dataset_sha256"] = file_sha256(source)
    return keep


def is_validated_pair(engine: dict[str, Any]) -> bool:
    """Whether an engine block's dataset SHA-256 and versions are the pinned
    build's (``DATA_BUILD``). Computed, never read from the block itself."""
    return (
        engine.get("dataset_sha256") == DATA_BUILD.sha256
        and engine.get("policyengine_uk") == DATA_BUILD.engine
        and engine.get("policyengine_core") == DATA_BUILD.core
    )


def engine_block(microsim=None) -> dict[str, Any]:
    """The ``engine`` block of results.json.

    Without a simulation: the pinned strings. With one: what is installed and
    the dataset it loaded. ``validated_pair`` holds only when the file is the
    pinned build (by SHA-256) and the installed policyengine-uk and
    policyengine-core are the versions that build was made and certified on.
    """
    if microsim is None:
        return {
            "policyengine": PINNED["policyengine"],
            "policyengine_uk": PINNED["policyengine_uk"],
            "policyengine_core": PINNED["policyengine_core"],
            "dataset": PINNED["dataset"],
            "dataset_sha256": PINNED["dataset_sha256"],
            "validated_pair": True,
            "label": LABEL,
        }
    versions = installed_versions()
    record = dataset_provenance(microsim)
    sha = record.get("runtime_dataset_sha256")
    validated = (
        sha is not None
        and sha == DATA_BUILD.sha256
        and versions["policyengine_uk"] == DATA_BUILD.engine
        and versions["policyengine_core"] == DATA_BUILD.core
    )
    return {
        **versions,
        "dataset": DATA_BUILD.id if validated else record.get("runtime_dataset_uri"),
        "dataset_revision": record.get("runtime_dataset_revision"),
        "dataset_sha256": sha,
        "validated_pair": bool(validated),
        "label": LABEL if validated else None,
    }
