"""
client_fetch_books.py

Fetches all books from the Flask API (/api/books) in pages of 10. Loops through
pages until all books are retrieved or the API returns 404. Fetched books are
stored in `all_books` and progress is printed to the console.

Usage:
    python client_fetch_books.py

Variables:
    BASE_URL (str): API endpoint URL.
    LIMIT (int): Number of books per page.
    page (int): Current page number.
    all_books (list): Accumulates all fetched book dictionaries.

Example Output:
    Fetched 10 books on page 1
    Fetched 10 books on page 2
    ...
    No more books after page 11
    Finished fetching 103 books

Requirements:
    - Python 3.x
    - requests library
    - Flask API running at BASE_URL
"""

import requests

BASE_URL = "http://127.0.0.1:5055/api/books"
LIMIT = 10
page = 1
all_books = []

while True:
    response = requests.get(BASE_URL, params={"page": page, "limit": LIMIT})

    if response.status_code == 404:
        print(f"No more books after page {page - 1}")
        break

    elif response.status_code != 200:
        print(f"Error {response.status_code} on page {page}")
        break

    books = response.json()
    if not books:
        print(f"No more books after page {page - 1}")
        break

    print(f"Fetched {len(books)} books on page {page}")
    all_books.extend(books)
    page += 1

print(f" Finished fetching {len(all_books)} books.")
