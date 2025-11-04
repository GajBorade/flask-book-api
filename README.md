📚 Flask Book API: A RESTful CRUD Service

A beginner-friendly REST API built with Python and the Flask micro-framework. 
This project demonstrates core backend skills by providing a complete service 
to manage a collection of books, including CRUD operations, dynamic query filtering, 
and file-based data persistence.

Two versions are included:
- basic_flask_book_api.py — In-memory storage for learning and quick demos.
- app.py — Persistent version with pagination, rate limiting, and improved error handling.

## ✨ Features

Full CRUD Implementation: Supports all standard REST operations (GET, POST, PUT, DELETE).

- **GET /api/books**: Retrieve all books or filter by 
                      `title`, `author`, `id`, `year`, or `isbn`.
    - **Pagination** supported with ?page=<number>&limit=<number> query parameters.
- **POST /api/books**: Add new books. Duplicate books (same title & author) are ignored.
- **PUT /api/books/<book_id>**: Update a book's information.
- **DELETE /api/books/<book_id>**: Delete a book by ID.
- **Rate Limiting**: Prevents abuse of API endpoints.
    - GET /api/books → 10 requests per minute
    - PUT /api/books/<book_id> → 5 requests per minute
    - DELETE /api/books/<book_id> → 3 requests per minute
- **Error Handling**: Returns clear HTTP status codes and JSON error messages 
                      for invalid requests:
    - 400 Bad Request → invalid input or duplicate book
    - 404 Not Found → book or page not found
    - 429 Too Many Requests → rate limit exceeded
- **Persistence**: Books are stored in `data/books.json`.
- **Validation**: Invalid query parameters and invalid book IDs return proper error messages.

## 📁 Project Structure

```text
.
├── data/                      # JSON storage files
│   ├── books.json             # Primary data file used by the API
│   ├── books_manual.json
│   └── varied_books.json
├── scripts/                   # Utility scripts (e.g., data generation) ignored in Git
├── app.py                     # Main Flask application and API routes
├── client_fetch_books.py      # Employs loop to fetch all books from the Flask API (/api/books) in pages of 10
├── basic_flask_book_api.py    # (Optional) Basic, non-persistent version
├── requirements.txt           # Project dependencies
└── validators.py              # Functions for data validation (ID, query params)


## ⚙️ Installation

Prerequisites
    - Python 3.x

Steps
1. Clone the repository:

git clone <repo-url>
cd <repo-folder>


2. Create a virtual environment and activate it:

python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows


3. Install dependencies:

    pip install -r requirements.txt


🚀 Usage

Run the Flask API: python app.py

The API will be available at: http://127.0.0.1:5055/api/books

## API Endpoints and Examples

| Method   | Endpoint            | Description                   | Example Request/Body                                                                       |
|----------|---------------------|-------------------------------|--------------------------------------------------------------------------------------------|
| GET      | /api/books          | Retrieve all books            | `GET http://127.0.0.1:5055/api/books`                                                      |
| GET      | /api/books?filter   | Filter books by any valid key | `GET http://127.0.0.1:5055/api/books?author=George Orwell`                                 |
| POST     | /api/books          | Add one or more new books     | ```json {"title": "New Book", "author": "John Doe", "year": 2025} ```                      |
| PUT      | /api/books/<int:id> | Update an existing book by ID | ```json PUT http://127.0.0.1:5055/api/books/1 {"title": "Updated Title", "year": 2023} ``` |
| DELETE   | /api/books/<int:id> | Delete a book by ID           | `DELETE http://127.0.0.1:5055/api/books/1`                                                 |


 
 ## 🖥 Client Script: Fetch All Books

The `client_fetch_books.py` script acts as a client to fetch books from the API
in pages of 10 until all books are retrieved. It prints progress and totals
to the console.

## 🚀 Usage

Make sure the Flask API is running: 

```
python app.py
```

Then run the client script: 

```
python client_fetch_books.py
```

### Example Output

```
Fetched 10 books on page 1
Fetched 10 books on page 2
...
No more books after page 11
Finished fetching 103 books
```
## 🧰 Requirements

- Python 3.x
- Flask==2.3.2
- Flask-Limiter~=4.0.0
- requests~=2.32.5
- A running instance of the Flask Book API at `http://127.0.0.1:5055/api/books`
