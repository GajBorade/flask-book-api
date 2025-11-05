import logging
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
import json
from validators import (
    validate_book_id,
    validate_query_parameters,
    page_validation,
    limit_validation,
)
from collections import OrderedDict

# Define valid query keys
VALID_QUERY_KEYS = {"title", "author", "id", "year", "isbn", "page", "limit"}

# Define the order in which the keys appear
BOOK_KEYS_ORDER = ["id", "title", "author", "year", "isbn"]

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s, %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Configuring Client IP-Based Rate Limiting
limiter = Limiter(app=app, key_func=get_remote_address)

# Instruct Flask not to sort keys alphabetically during jsonify
app.config["JSON_SORT_KEYS"] = False


def reorder_books(books_list):
    """Return a list of books with keys in a fixed order."""
    ordered_books = []  # This will hold our books in the correct order

    for book in books_list:
        ordered_book = OrderedDict()  # empty dict
        for key in BOOK_KEYS_ORDER:
            ordered_book[key] = book.get(key)
        ordered_books.append(ordered_book)

    return ordered_books


def read_books():
    """Read and return all books from the JSON file"""
    try:
        with open("data/books.json", "r", encoding="utf-8") as file_object:
            return json.load(file_object)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return []  # return empty list if file is invalid or missing


def write_books(new_books):
    """
    Write books to JSON file for persistence.

    Uses ensure_ascii=False to ensure Hindi/Marathi characters are
    written directly, making the file easily readable and writable.
    """
    with open("data/books.json", "w", encoding="utf-8") as file_object:
        json.dump(new_books, file_object, indent=4, ensure_ascii=False)


# Function to standardize all JSON responses
def create_json_response(data, status_code):
    """
    Manually serializes data to a JSON string and returns a Flask Response
    with the correct Content-Type header and status code, guaranteeing key order.
    """
    # Use json.dumps to preserve the OrderedDict keys
    json_output = json.dumps(data, indent=4)

    # Return the string with the correct MIME type
    return json_output, status_code, {"Content-Type": "application/json"}


def log_book_action(method, book_id):
    """Logs a PUT or DELETE request with the method and ID."""
    app.logger.info("%s request received for book ID %d.", method, book_id)


@app.route("/api/books", methods=["GET", "POST"])
@limiter.limit("10/minute")  # Limit to 10 requests per minute
def books():
    """
    Handle GET and POST requests for the /api/books endpoint.

    GET (Retrieve Books):
        - **Functionality:** Returns a list of books, optionally filtered
          and paginated.
        - **Rate Limit:** Enforced by @limiter.limit("10/minute")
          (Flask-Limiter).
        - **Query Parameters:** Supports filtering by fields like 'title',
          'author', 'year', etc., and controls for pagination.
        - **Pagination:** Supports **Limit/Page-Based Pagination** via
          'limit' (max 10) and 'page' parameters.
        - **Logging:** Logs the request and final book count at **INFO** level (app.logger.info).
        - **Success (200 OK):** Returns the requested list of books.
        - **Error Conditions:**
            - 404 Not Found: No books found matching the filter or page
              criteria.
            - 400 Bad Request: Invalid query parameter key or invalid
              data type (e.g., non-integer 'year').
            - 429 Too Many Requests: Rate limit exceeded (handled by
              Limiter extension).

    POST (Create Book(s)):
        - **Functionality:** Accepts one or more book entries in JSON
          format (dict or list of dicts).
        - **Data Persistence:** Appends new, unique books to
          data/books.json.
        - **Validation:** Performs duplicate checking based on 'title' and
          'author'. Client-provided 'id' is ignored/deleted.
        - **Success (201 Created):** Returns the newly added book(s),
          including server-assigned 'id'.
        - **Error Conditions:**
            - 400 Bad Request: Invalid payload format or if all submitted
              books are duplicates.

    Other Methods:
        - Unsupported HTTP methods return **405 Method Not Allowed**.

    :return: JSON response containing requested data or an error payload.
    :rtype: flask.Response
    """
    app.logger.info(f"{request.method} request received for /api/books")

    if request.method == "GET":
        # Read all stored books
        books_list = read_books()
        app.logger.debug("Read books from file.")

        # Extract and validate query parameters
        # Convert query string to a regular python dict
        # & get all query parameters dynamically
        query_parameters = request.args.to_dict()

        # Check for invalid keys from the client / user
        is_valid, invalid_keys = validate_query_parameters(
            query_parameters, VALID_QUERY_KEYS
        )

        # Action on invalid keys
        if not is_valid:
            return (
                jsonify(
                    {"error": "Invalid query parameters", "invalid_keys": invalid_keys}
                ),
                400,
            )

        # Separate filtering and pagination parameters
        filter_parameters = {
            k: v for k, v in query_parameters.items() if k not in ("page", "limit")
        }
        # Apply filters: keep books matching all provided query parameters
        for key, value in filter_parameters.items():
            value = value.strip().strip('"')
            if key in ("id", "year"):
                try:
                    num_value = int(value)
                except ValueError:
                    return jsonify({"error": f"Invalid integer for '{key}'"}), 400
                books_list = [book for book in books_list if book.get(key) == num_value]
            else:
                books_list = [
                    book
                    for book in books_list
                    if value.lower().strip().strip('"')
                    in str(book.get(key, "")).lower().strip()
                ]
        # Reorder / sort books
        ordered_books = reorder_books(books_list)

        if not ordered_books:
            return jsonify({"error": "No books found"}), 404

        # Validate and extract pagination params
        # Offset-Based Pagination or Limit/Offset Pagination
        limit_str = request.args.get("limit", 10)
        page_str = request.args.get("page", 1)

        # Step 1: validate limit FIRST, because page_validation depends on it
        limit = limit_validation(limit_str, max_limit=10)

        # Step 2: validate page using the cleaned integer limit
        try:
            page = page_validation(
                page_str, total_books=len(ordered_books), limit=limit
            )
        except ValueError:
            return jsonify({"Error": "No books found"}), 404

        # Step 3: calculate indices safely
        start_index = (page - 1) * limit
        end_index = start_index + limit

        # Step 4: slice and respond
        paginated_books = ordered_books[start_index:end_index]

        app.logger.info(f"Returning {len(paginated_books)} books for page {page}")
        # print("DEBUG - read_paginated_books:", paginated_books)
        # Handle no matches
        if not paginated_books:
            return jsonify({"error": "No books found for the given criteria"}), 404
        return create_json_response(paginated_books, 200)
        # return jsonify(ordered_books), 200

    elif request.method == "POST":
        app.logger.debug("Attempting to parse JSON payload for new book(s).")
        # Read the JSON sent by the client (could be dict/ list)
        # Get the new book(s) data from the client
        # silent=True prevents Flask from immediately raising a 400 error on bad JSON.
        data = request.get_json(silent=True)

        # Check explicitly if the JSON failed to parse (data is None)
        if data is None:
            # Handle empty body case
            app.logger.error("POST request received with empty or invalid JSON payload")
            return (
                jsonify(
                    {
                        "error": "Invalid JSON format or empty request body.",
                        "message": "Ensure the Content-Type is 'application/json' "
                        "& body is valid JSON.",
                    }
                ),
                400,
            )

        existing_books = read_books()

        # New list to hold final, server-validated books
        final_books_to_add = []

        # Convert single book (dict) to list for uniform processing
        if isinstance(data, dict):
            data = [data]

        if not data:
            return jsonify({"error": "Bad Request", "message": "No data provided"}), 400

        # Finding max_id
        max_id = max((book["id"] for book in existing_books), default=0)
        new_id = max_id + 1

        # Loop through each submitted book and validate/process it
        for submitted_book in data:

            # 1. CRITICAL: Remove client ID first to prevent conflicts
            if "id" in submitted_book:
                del submitted_book["id"]

            duplicate_found = False
            title = submitted_book.get("title", "Unknown")
            author = submitted_book.get("author", "Anonymous")

            # 2. Duplicate Check: Check against all existing books
            for book in existing_books:
                if title == book.get("title") and author == book.get("author"):
                    duplicate_found = True
                    break

            # 3. Process Only If Not Duplicate
            if not duplicate_found:
                # 4. Construct the final, correct book object
                ordered_book = {
                    "id": new_id,
                    "title": title,
                    "author": author,
                    "year": submitted_book.get("year", ""),
                    "isbn": submitted_book.get("isbn", ""),
                }
                final_books_to_add.append(ordered_book)
                new_id += 1  # Increment ID for the next book

        # If nothing is left to add, return an error
        if not final_books_to_add:
            # Added a more descriptive message
            return (
                jsonify(
                    {
                        "error": "Bad Request",
                        "message": "Book already exists (or no valid books submitted)",
                    }
                ),
                400,
            )

            # 5. Use the final, corrected list for persistence
        existing_books.extend(final_books_to_add)
        write_books(existing_books)

        app.logger.info(
            "Successfully added %d new unique book(s). Max ID is now %d.",
            len(final_books_to_add),
            new_id - 1,
        )
        # 6. Return the correct, ordered list
        return create_json_response(final_books_to_add, 201)

    # Fallback for any unsupported HTTP method (besides POST/GET)
    return "Method not allowed", 405


def find_book_by_id(book_id):
    """Find the book with the id 'book_id'
    If there is no book with this id, return None.
    """
    book_id = validate_book_id(book_id)

    all_books = read_books()
    for book in all_books:
        # Ensure both book_id from flask (str)
        # & book_id from books.json are integers before comparing
        if book_id == int(book["id"]):
            return book
    return None


@app.route("/api/books/<int:book_id>", methods=["PUT"])
@limiter.limit("5/minute")  # Limit to 5 requests per minute
def handle_book(book_id):
    """Find book with the entered id
    And update its author or title or both"""
    log_book_action(request.method, book_id)

    # Read books from data/books_manual.json
    all_books = read_books()

    # Validate ID Conversion
    book_id = validate_book_id(book_id)

    book = find_book_by_id(book_id)

    # Book not found error
    if book is None:
        return (
            jsonify(
                {
                    "error": "Book Not Found",
                    "message": f"Book with id {book_id} not found",
                }
            ),
            404,
        )

    # Update the book with new data
    new_data = request.get_json()

    # Case formatting step
    if "title" in new_data:
        new_data["title"] = new_data["title"].strip().title()
    if "author" in new_data:
        new_data["author"] = new_data["author"].strip().title()
    if "year" in new_data:
        book["year"] = new_data["year"]
    if "isbn" in new_data:
        book["isbn"] = new_data["isbn"]

    # Apply ALL updates to the local 'book' object
    book.update(new_data)
    # get index of the book to update books.json
    # for i in range(len(all_books)):
    #     if all_books[i]['id'] == book_id:
    #         all_books[i].update(new_data)

    # Using enumerate to get the index
    for i, b in enumerate(all_books):
        if b["id"] == book_id:
            all_books[i].update(new_data)
    # Save all books back to the JSON file
    write_books(all_books)

    # 🔑 Reorder the single updated book before returning it
    ordered_book_response = reorder_books([book])[0]

    app.logger.info("Successfully updated book_ID %d.", book_id)
    # Return the updated book
    return create_json_response(ordered_book_response, 200)
    # return jsonify(ordered_book_response)


# Delete method
@app.route("/api/books/<int:book_id>", methods=["DELETE"])
@limiter.limit("3/minute")  # Limit to 10 requests per minute
def delete_book(book_id):
    """Find the book with the given ID
    And delete the particular book"""
    log_book_action(request.method, book_id)

    # Read books from data/books.json
    all_books = read_books()

    # Validate ID Conversion
    book_id = validate_book_id(book_id)

    book = find_book_by_id(book_id)

    # Book not found error
    if book is None:
        app.logger.warning("Attempted deletion on non-existent book ID %d.", book_id)
        return (
            jsonify(
                {
                    "error": "Book Not Found",
                    "message": f"Book with id {book_id} not found",
                }
            ),
            404,
        )

    # Remove the book from the list
    all_books.remove(book)

    # Save all books back to the JSON file
    write_books(all_books)

    app.logger.info("Successfully deleted book ID %d.", book_id)
    # Return the deleted book
    return (
        jsonify(
            {
                "message": f"Book with id {book_id} deleted successfully.",
                "deleted_book": book,
            }
        ),
        200,
    )


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not Found"}), 404


@app.errorhandler(405)
def method_not_allowed_error(error):
    return jsonify({"error": "Method Not Allowed for this endpoint"}), 405


@app.errorhandler(RateLimitExceeded)
def handle_rate_limit(e):
    return jsonify(
        {
            "error": "Too Many Requests",
            "message": "You have exceeded your rate limit. Try again later",
        }
    )


if __name__ == "__main__":
    app.run(port=5055, host="0.0.0.0", debug=True)
