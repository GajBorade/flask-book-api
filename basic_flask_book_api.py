"""
Flask Book API (Beginner Version)
A minimal REST API using Flask that manages books in memory.
Includes CRUD operations and basic request validation.
"""

import logging
from flask import Flask, jsonify, request
from collections import OrderedDict
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded


app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Limiter
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["100 per hour"])
# @app.route('/api/books', methods=['GET'])
# def get_books():
#     # For now, we'll return a static list
#     books = [
#         {"id": 1, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
#         {"id": 2, "title": "1984", "author": "George Orwell"}
#     ]
#     return jsonify(books)

# Our list of books
books = [
    {"id": 1, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
    {"id": 2, "title": "1984", "author": "George Orwell"},
]


def validate_book_data(data):
    if "title" not in data or "author" not in data:
        return False
    return True


@app.route("/")
def home():
    data = OrderedDict()
    data["message"] = "Welcome to the Flask Book API!"
    data["endpoints"] = {
        "GET /api/books": "List all books",
        "POST /api/books": "Add a new book",
        "PUT /api/books/<id>": "Update a book",
        "DELETE /api/books/<id>": "Delete a book",
    }
    return jsonify(data)


@app.route("/api/books", methods=["GET", "POST"])
def handle_books():
    app.logger.info(f"{request.method} request received for /api/books")

    if request.method == "POST":
        # Get the new book data from the client
        new_book = request.get_json()

        # validate book data
        if not validate_book_data(new_book):
            return jsonify({"error": "Invalid book data"}), 400

        # Generate a new ID for the book
        new_id = max(book["id"] for book in books) + 1
        new_book["id"] = new_id

        # Add the new book to in-memory list
        books.append(new_book)

        # Return the new book data to the client
        return jsonify(new_book), 201

    elif request.method == "GET":
        author = request.args.get("author")
        title = request.args.get("title")

        filtered_books = books
        if author:
            filtered_books = [
                book
                for book in filtered_books
                if author.lower() in book["author"].lower()
            ]
        if title:
            filtered_books = [
                book
                for book in filtered_books
                if title.lower() in book["title"].lower()
            ]

        # Pagination
        # use max function to avoid -ve or zero values
        # 1 is the minimum safe value for both page & limit
        page = max(int(request.args.get("page", 1)), 1)
        limit = max(int(request.args.get("limit", 10)), 1)

        start_index = (page - 1) * limit
        end_index = start_index + limit

        paginated_books = filtered_books[start_index:end_index]
        app.logger.info(f"Returning {len(paginated_books)} books for page {page}")

        return jsonify(paginated_books)

    # Fallback for any unsupported HTTP method
    return jsonify({"Error": "Method Not Allowed"}), 405


def find_book_by_id(book_id):
    """Find the book with the id `book_id`.
    If there is no book with this id, return None."""
    # TODO: implement this
    for book in books:
        if book_id == int(book["id"]):
            return book
    return None


@app.route("/api/books/<int:id>", methods=["PUT"])
def handle_book(id):
    # Find the book with the given ID
    book = find_book_by_id(id)

    # If the book wasn't found, return a 404 error
    if book is None:
        return "", 404

    # Update the book with the new data
    new_data = request.get_json()
    book.update(new_data)

    # Return the updated book
    return jsonify(book)


@app.route("/api/books/<int:id>", methods=["DELETE"])
def delete_book(id):
    # Find the book with the given ID
    book = find_book_by_id(id)

    # If the book wasn't found, return a 404 error
    if book is None:
        return "", 404

    # Remove the book from the list
    # TODO: implement this
    books.remove(book)

    # Return the deleted book
    return jsonify(book)


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not Found"}), 404


@app.errorhandler(405)
def method_not_allowed_error(error):
    return jsonify({"error": "Method Not Allowed"}), 405


@app.errorhandler(RateLimitExceeded)
def handle_rate_limit(e):
    return jsonify(
        {
            "error": "Too Many Requests",
            "message": "You have exceeded your rate limit. Try again later",
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
