import json

from young_people_work import pair_check, runtime_identity


def _release(tmp_path, engine=None):
    gates = {"gates": {"projection": {"details": {}}}}
    if engine:
        gates["gates"]["projection"]["details"]["projection_engine"] = f"policyengine-uk=={engine}"
    (tmp_path / "terminal_gates.json").write_text(json.dumps(gates))
    (tmp_path / "release_certification.json").write_text(json.dumps({"kind": "uk"}))
    return tmp_path


def test_matching_pair_passes(tmp_path):
    assert pair_check.problems(_release(tmp_path, "2.177.7"), "2.177.7") == []


def test_build_on_another_engine_fails(tmp_path):
    found = pair_check.problems(_release(tmp_path, "2.177.7"), "2.151.0")
    assert len(found) == 1
    assert "2.177.7" in found[0] and "2.151.0" in found[0]


def test_no_recorded_engine_needs_a_stated_one(tmp_path):
    release = _release(tmp_path)
    assert "--build-engine" in pair_check.problems(release, "2.174.1")[0]
    assert pair_check.problems(release, "2.174.1", stated="2.174.1") == []
    assert pair_check.problems(release, "2.174.1", stated="2.177.7")


def test_missing_engine_fails(tmp_path):
    assert pair_check.problems(_release(tmp_path, "2.174.1"), None)


def test_cli_exit_code(tmp_path, monkeypatch, capsys):
    release = _release(tmp_path, "2.177.7")
    monkeypatch.setattr(pair_check, "installed_engine", lambda: "2.151.0")
    assert pair_check.main([str(release)]) == 1
    monkeypatch.setattr(pair_check, "installed_engine", lambda: "2.177.7")
    assert pair_check.main([str(release)]) == 0


def _manifests_only(tmp_path, engine="2.177.7"):
    """A release folder shaped like 9e18f010's two manifests, with no
    terminal_gates.json (as when only the manifests are downloaded)."""
    (tmp_path / "build_manifest.json").write_text(
        json.dumps(
            {
                "release": "microcosm-uk-2024-25-national",
                "runtime": {
                    "python": "3.14.6",
                    "policyengine-core": "3.34.10",
                    "policyengine-uk": engine,
                },
            }
        )
    )
    (tmp_path / "release_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "built_with_model_package": {"name": "policyengine-uk", "version": engine},
                "compatible_model_packages": [
                    {"name": "policyengine-uk", "specifier": f"=={engine}"}
                ],
                "built_with_core_package": {"name": "policyengine-core", "version": "3.34.10"},
            },
            indent=2,
        )
    )
    return tmp_path


def test_manifests_alone_record_the_engine(tmp_path):
    release = _manifests_only(tmp_path)
    assert not (release / "terminal_gates.json").exists()
    assert pair_check.recorded_engines(release) == {"2.177.7"}
    assert pair_check.problems(release, "2.177.7") == []
    found = pair_check.problems(release, "2.174.1")
    assert len(found) == 1 and "2.177.7" in found[0]


def test_each_manifest_field_is_read(tmp_path):
    (tmp_path / "build_manifest.json").write_text(
        json.dumps({"runtime": {"policyengine-uk": "1.0.0"}})
    )
    (tmp_path / "release_manifest.json").write_text(
        json.dumps(
            {
                "built_with_model_package": {"name": "policyengine-uk", "version": "2.0.0"},
                "compatible_model_packages": [
                    {"name": "policyengine-uk", "specifier": "==3.0.0"},
                    {"name": "policyengine-uk", "specifier": ">=4.0.0"},
                    {"name": "policyengine-core", "specifier": "==5.0.0"},
                ],
            }
        )
    )
    assert pair_check.recorded_engines(tmp_path) == {"1.0.0", "2.0.0", "3.0.0"}


class _Sim:
    def __init__(self, bundle):
        self.policyengine_bundle = bundle


CERTIFIED = "microcosm-uk-2024-25-national-20261107T020434Z-eeb6093e"
OTHER = "uk-frs-calibration-attempt-20261110T204756Z-9e18f010"


def test_receipt_labels_the_loaded_build_not_the_certified_one(tmp_path, monkeypatch):
    path = tmp_path / "releases" / "microcosm-uk-2024-25-national" / OTHER / "file.h5"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"not the certified file")
    monkeypatch.setattr(
        runtime_identity, "installed_versions", lambda: {"policyengine_uk": "2.174.1"}
    )
    block = runtime_identity.engine_block(
        _Sim(
            {
                "certified_data_build_id": CERTIFIED,
                "certified_data_artifact_sha256": "0" * 64,
                "model_version": "2.174.1",
                "runtime_dataset_source": str(path),
                "runtime_dataset_uri": str(path),
            }
        )
    )
    assert block["dataset"] == OTHER
    assert block["validated_pair"] is False
    assert str(tmp_path) not in json.dumps(block)


def test_receipt_keeps_the_certified_label_for_the_certified_file(tmp_path, monkeypatch):
    path = tmp_path / "file.h5"
    path.write_bytes(b"certified")
    sha = runtime_identity.file_sha256(path)
    monkeypatch.setattr(
        runtime_identity, "installed_versions", lambda: {"policyengine_uk": "2.174.1"}
    )
    block = runtime_identity.engine_block(
        _Sim(
            {
                "certified_data_build_id": CERTIFIED,
                "certified_data_artifact_sha256": sha,
                "model_version": "2.174.1",
                "runtime_dataset_source": str(path),
            }
        )
    )
    assert (block["dataset"], block["validated_pair"]) == (CERTIFIED, True)


def test_unnamed_unmanaged_file_is_labelled_by_hash():
    label = runtime_identity.dataset_label({"runtime_dataset_sha256": "ab" * 32}, "/x.h5", False)
    assert label == "unmanaged dataset (sha256 abababababab)"
