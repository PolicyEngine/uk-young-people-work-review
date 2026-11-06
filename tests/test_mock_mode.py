from young_people_work import publication
from young_people_work.pipeline import MOCK_BANNER, build_placeholder_results


def _mock():
    results = build_placeholder_results()
    results["status"] = "mock"
    results["banner"] = MOCK_BANNER
    return results


def test_mock_file_passes_with_the_mock_banner():
    assert publication.validate_public(_mock()) == []


def test_mock_id_needs_mock_status():
    results = build_placeholder_results()
    results["measures"][0]["id"] = "mock_youth_route"
    assert any("mock_" in e for e in publication.validate_public(results))


def test_mock_status_needs_the_word_mock_in_the_banner():
    results = _mock()
    results["banner"] = "Drill figures"
    assert any("MOCK" in e for e in publication.validate_public(results))


def test_unknown_status_is_refused():
    results = _mock()
    results["status"] = "draft"
    assert publication.validate_public(results)
