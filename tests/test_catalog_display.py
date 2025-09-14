from database import get_db_connection, get_all_books
import pytest

def _insert_book(title, author, isbn, copies):
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO books (title, author, isbn, total_copies, available_copies) VALUES (?, ?, ?, ?, ?)',
        (title, author, isbn, copies, copies)
    )
    conn.commit()
    conn.close()

def test_catalog_lists_books_and_fields():
    _insert_book("The Great Gatsby", "F. Scott Fitzgerald", "9780743273565", 3)
    _insert_book("1984", "George Orwell", "9780451524935", 1)

    books = get_all_books()
    assert isinstance(books, list)
    assert any(b["title"] == "The Great Gatsby" for b in books)
    assert any(b["title"] == "1984" for b in books)

    # Required columns present
    sample = books[0]
    for key in ["id", "title", "author", "isbn", "total_copies", "available_copies"]:
        assert key in sample
