import pytest

from app import main


@pytest.fixture
def client():
    main.books.clear()
    main.next_id = 1
    return main.app.test_client()


def add_book(client, title="Dune", author="Frank Herbert"):
    return client.post("/books", json={"title": title, "author": author})


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_create_book(client):
    r = add_book(client)
    assert r.status_code == 201
    assert r.headers["Location"] == "/books/1"
    assert r.get_json()["read"] is False


def test_list_empty(client):
    assert client.get("/books").get_json() == []


def test_list_oldest_first(client):
    add_book(client, title="First")
    add_book(client, title="Second")
    titles = [b["title"] for b in client.get("/books").get_json()]
    assert titles == ["First", "Second"]


def test_get_book(client):
    add_book(client)
    r = client.get("/books/1")
    assert r.status_code == 200
    assert r.get_json()["title"] == "Dune"


def test_update_book(client):
    add_book(client)
    r = client.put("/books/1", json={"title": "Dune", "author": "F. Herbert", "read": True})
    assert r.status_code == 200
    assert r.get_json()["read"] is True


def test_delete_book(client):
    add_book(client)
    assert client.delete("/books/1").status_code == 204
    assert client.get("/books/1").status_code == 404


def test_missing_book(client):
    r = client.get("/books/99")
    assert r.status_code == 404
    assert "detail" in r.get_json()


def test_invalid_book(client):
    r = client.post("/books", json={"title": "", "author": "X"})
    assert r.status_code == 422


def test_not_json(client):
    r = client.post("/books", data="hello")
    assert r.status_code == 422