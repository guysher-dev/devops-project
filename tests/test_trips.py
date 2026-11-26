import pytest

from app import main
from app.matcher import DAYS, QUESTIONS


@pytest.fixture
def client():
    return main.app.test_client()


def answers(**changes):
    data = {q["id"]: "0" for q in QUESTIONS if q["type"] == "level"}
    data.update(
        days=7,
        kansai="yes",
        car="no",
        tours="yes",
        pace="full",
        who="friends",
        budget="mid",
        cold="no",
    )
    data.update(changes)
    return data


def test_questions(client):
    r = client.get("/api/questions")
    assert r.status_code == 200
    assert len(r.get_json()) == 20


def test_plan_length(client):
    r = client.post("/api/plan", json=answers(days=9))
    assert r.status_code == 200
    assert len(r.get_json()["days"]) == 9


def test_plan_starts_and_ends_in_tokyo(client):
    days = client.post("/api/plan", json=answers()).get_json()["days"]
    assert days[0]["title"] == DAYS[0]["title"]
    assert days[-1]["title"] == DAYS[-1]["title"]


def test_no_car_no_car_days(client):
    days = client.post("/api/plan", json=answers(days=18, cars="3")).get_json()["days"]
    assert not any("יום רכב" in d["title"] for d in days)


def test_car_lover_gets_car_days(client):
    data = answers(days=6, car="yes", cars="3")
    days = client.post("/api/plan", json=data).get_json()["days"]
    assert any("יום רכב" in d["title"] for d in days)


def test_tokyo_only(client):
    data = answers(days=12, kansai="no")
    days = client.post("/api/plan", json=data).get_json()["days"]
    assert {d["region"] for d in days} == {"tokyo"}


def test_transfer_between_cities(client):
    days = client.post("/api/plan", json=answers(days=10, food="3")).get_json()["days"]
    assert any(d["transfer"] for d in days)


def test_relaxed_drops_optional_stops(client):
    full = client.post("/api/plan", json=answers(days=18)).get_json()["days"]
    relaxed = client.post("/api/plan", json=answers(days=18, pace="relaxed")).get_json()
    count = sum(len(d["items"]) for d in full)
    assert sum(len(d["items"]) for d in relaxed["days"]) < count


def test_free_days_fill_the_trip(client):
    data = answers(days=18, kansai="no", tours="no")
    days = client.post("/api/plan", json=data).get_json()["days"]
    assert len(days) == 18
    assert any(d["title"] == "יום חופשי בטוקיו" for d in days)


def test_missing_answer(client):
    data = answers()
    del data["pace"]
    r = client.post("/api/plan", json=data)
    assert r.status_code == 422
    assert "pace" in r.get_json()["detail"]


def test_bad_answer(client):
    r = client.post("/api/plan", json=answers(days=40))
    assert r.status_code == 422


def test_plan_not_json(client):
    r = client.post("/api/plan", data="hello")
    assert r.status_code == 422


def test_no_personal_details():
    text = str(DAYS)
    for word in ["גיא", "עידו", "שניכם", "המלון", "CJN"]:
        assert word not in text
