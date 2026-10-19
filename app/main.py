from datetime import date

from flask import Flask, jsonify, request

app = Flask(__name__)

books = {}
next_id = 1


def check_book(data):
    if not isinstance(data, dict):
        return "body must be a JSON object"
    title = data.get("title")
    if not isinstance(title, str) or not 1 <= len(title) <= 200:
        return "title must be 1-200 characters"
    author = data.get("author")
    if not isinstance(author, str) or not 1 <= len(author) <= 100:
        return "author must be 1-100 characters"
    year = data.get("year")
    if year is not None:
        if isinstance(year, bool) or not isinstance(year, int):
            return "year must be a number"
        if not 0 <= year <= date.today().year:
            return "year must be between 0 and this year"
    if not isinstance(data.get("read", False), bool):
        return "read must be true or false"
    return None


def make_book(book_id, data):
    return {
        "id": book_id,
        "title": data["title"],
        "author": data["author"],
        "year": data.get("year"),
        "read": data.get("read", False),
    }


@app.get("/healthz")
def healthz():
    return jsonify(status="ok")


@app.post("/books")
def create_book():
    global next_id
    data = request.get_json(silent=True)
    error = check_book(data)
    if error:
        return jsonify(detail=error), 422
    book = make_book(next_id, data)
    books[next_id] = book
    next_id += 1
    return jsonify(book), 201, {"Location": f"/books/{book['id']}"}


@app.get("/books")
def list_books():
    return jsonify(list(books.values()))


@app.get("/books/<int:book_id>")
def get_book(book_id):
    if book_id not in books:
        return jsonify(detail="book not found"), 404
    return jsonify(books[book_id])


@app.put("/books/<int:book_id>")
def update_book(book_id):
    if book_id not in books:
        return jsonify(detail="book not found"), 404
    data = request.get_json(silent=True)
    error = check_book(data)
    if error:
        return jsonify(detail=error), 422
    books[book_id] = make_book(book_id, data)
    return jsonify(books[book_id])


@app.delete("/books/<int:book_id>")
def delete_book(book_id):
    if book_id not in books:
        return jsonify(detail="book not found"), 404
    del books[book_id]
    return "", 204


@app.errorhandler(404)
def not_found(e):
    return jsonify(detail="not found"), 404