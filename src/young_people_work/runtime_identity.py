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

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGES = ("policyengine", "policyengine-uk", "policyengine-core")

# The pinned pair (uv.lock, README). tests/test_runtime_identity.py checks
# these against uv.lock, and the model job against the installed packages.
PINNED = {
    "policyengine": "6.17.2",
    "policyengine_uk": "2.174.1",
    "policyengine_core": "3.33.3",
    "dataset": "microcosm-uk-2024-25-national-20261107T020434Z-eeb6093e",
    "dataset_sha256": "0a9b77db1c0dee2693cb2d47bad68da34cb662916eee4829942bcd45de581f25",
}


def ensure_data_token() -> None:
    """policyengine.py reads HUGGING_FACE_TOKEN only; fall back to the saved
    Hugging Face login so the token never goes on a command line."""
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


def bundle_dataset(microsim) -> dict[str, Any]:
    """The dataset provenance policyengine.py attaches to a managed run,
    plus the SHA-256 of the file it loaded (policyengine.py records the
    certified hash, not the loaded file's)."""
    bundle = dict(getattr(microsim, "policyengine_bundle", {}) or {})
    keep = {
        key: value
        for key, value in bundle.items()
        if isinstance(value, (str, int, float, bool)) or value is None
    }
    source = keep.pop("runtime_dataset_source", None)  # a local path: never published
    if source and Path(source).is_file():
        keep["runtime_dataset_sha256"] = file_sha256(source)
    return keep


def engine_block(microsim=None) -> dict[str, Any]:
    """The ``engine`` block of results.json.

    Without a simulation: the pinned strings. With one: what is installed and
    the dataset the bundle loaded, and whether it is the certified build.
    """
    if microsim is None:
        return {
            "policyengine": PINNED["policyengine"],
            "policyengine_uk": PINNED["policyengine_uk"],
            "policyengine_core": PINNED["policyengine_core"],
            "dataset": PINNED["dataset"],
            "dataset_sha256": PINNED["dataset_sha256"],
            "validated_pair": True,
        }
    versions = installed_versions()
    bundle = bundle_dataset(microsim)
    build = bundle.get("certified_data_build_id")
    sha = bundle.get("runtime_dataset_sha256")
    certified = (
        build is not None
        and bundle.get("model_version") == versions["policyengine_uk"]
        and sha is not None
        and sha == bundle.get("certified_data_artifact_sha256")
    )
    return {
        **versions,
        "dataset": build or bundle.get("runtime_dataset_uri"),
        "dataset_revision": bundle.get("runtime_dataset_revision"),
        "dataset_sha256": sha,
        "validated_pair": bool(certified),
    }
