"""Check the pinned Microcosm build: download it and compare its SHA-256.

``python -m young_people_work.certified_data`` downloads the build named in
``data_build.DATA_BUILD`` from the private Hugging Face dataset repository
(needs read access; the CI job takes it from a repository secret) and checks
the file's SHA-256 against the build's and against
``runtime_identity.PINNED``. The build was made and certified on
policyengine-uk 2.177.7; no policyengine.py release covers that pair. Light:
a download and a hash, no simulation.
"""

import sys

from young_people_work import data_build, runtime_identity


def main() -> int:
    from young_people_work.model import fetch_dataset

    build = data_build.DATA_BUILD
    path = fetch_dataset()
    sha = runtime_identity.file_sha256(path)
    problems = []
    if sha != build.sha256:
        problems.append(f"dataset SHA-256 {sha} is not build {build.id}'s {build.sha256}")
    if runtime_identity.PINNED["dataset"] != build.id:
        problems.append(f"runtime_identity.PINNED names {runtime_identity.PINNED['dataset']}")
    if sha != runtime_identity.PINNED["dataset_sha256"]:
        problems.append("dataset SHA-256 differs from runtime_identity.PINNED")
    for problem in problems:
        print(problem, file=sys.stderr)
    if not problems:
        print(f"Pinned dataset {build.id} sha256 {sha}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
