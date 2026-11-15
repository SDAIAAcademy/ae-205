"""The similar-claims endpoint (lab 2.4)."""

from __future__ import annotations

import pytest

from conftest import SIMILAR_DIR, make_client


@pytest.fixture
def shabih():
    with make_client(service="shabih", similar_dir=SIMILAR_DIR) as c:
        yield c


def test_ready_with_the_index_loaded(shabih):
    r = shabih.get("/readyz")
    assert r.status_code == 200, r.text
    assert r.json()["model"]["name"] == "shabih"


def test_returns_k_neighbours_sorted_by_score(shabih):
    r = shabih.post("/v1/similar", json={"description": "Windscreen cracked by a stone on the highway", "k": 5})
    assert r.status_code == 200, r.text
    res = r.json()["results"]
    assert len(res) == 5
    scores = [x["score"] for x in res]
    assert scores == sorted(scores, reverse=True)
    assert sum(x["incident"] == "windscreen" for x in res) >= 4


def test_finds_arabic_descriptions_too(shabih):
    r = shabih.post("/v1/similar", json={"description": "تسرب مياه من أنبوب في المطبخ", "k": 5, "line": "property"})
    res = r.json()["results"]
    assert all(x["line"] == "property" for x in res)
    assert sum(x["incident"] == "water_leak" for x in res) >= 4


def test_returns_no_personal_field(shabih):
    res = shabih.post("/v1/similar", json={"description": "Car stolen from outside the house", "k": 3}).json()["results"]
    for x in res:
        assert set(x) == {"claim_id", "line", "incident", "score"}


def test_validates_its_input(shabih):
    r = shabih.post("/v1/similar", json={"description": "x", "k": 500})
    assert r.status_code == 422
    assert r.json()["type"] == "urn:rifd:problem:validation-error"
