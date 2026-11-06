"""Check the bundle's certified dataset: download it and compare its SHA-256.

``python -m young_people_work.certified_data`` materialises the installed
policyengine.py bundle's default dataset (needs read access to the private
data; the CI job takes it from a repository secret) and checks the file's
SHA-256 against the bundle's ``certified_data_artifact_sha256`` and against
``runtime_identity.PINNED``. Light: a download and a hash, no simulation.
"""

import sys

from young_people_work import runtime_identity


def main() -> int:
    from policyengine.provenance.dataset_materialization import materialize_dataset
    from policyengine.tax_benefit_models.uk import uk_latest

    runtime_identity.ensure_data_token()
    bundle = uk_latest.release_bundle
    source = materialize_dataset("uk")
    sha = runtime_identity.file_sha256(source.path)
    expected = bundle.get("certified_data_artifact_sha256")
    problems = []
    if sha != expected:
        problems.append(f"dataset SHA-256 {sha} is not the bundle's certified {expected}")
    if bundle.get("certified_data_build_id") != runtime_identity.PINNED["dataset"]:
        problems.append(
            f"bundle build {bundle.get('certified_data_build_id')} is not the pinned "
            f"{runtime_identity.PINNED['dataset']}"
        )
    if sha != runtime_identity.PINNED["dataset_sha256"]:
        problems.append("dataset SHA-256 differs from runtime_identity.PINNED")
    for problem in problems:
        print(problem, file=sys.stderr)
    if not problems:
        print(f"Certified dataset {bundle.get('certified_data_build_id')} sha256 {sha}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
