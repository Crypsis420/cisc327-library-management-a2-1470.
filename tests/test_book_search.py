from database import get_db_connection
from library_service import search_books_in_catalog
import pytest

def _insert_book(title, author, isbn):
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO books (title, author, isbn, total_copies, available_copies) VALUES (?,?,?,?,?)',
        (title, author, isbn, 1, 1)
    )
    conn.commit(); conn.close()

def test_search_title_partial_case_insensitive():
    _insert_book("The Great Gatsby", "F. Scott Fitzgerald", "9780743273565")
    _insert_book("1984", "George Orwell", "9780451524935")
    result = search_books_in_catalog("great", "title")
    assert len(result) == 1 and result[0]["title"] == "The Great Gatsby"

def test_search_author_partial_case_insensitive():
    _insert_book("Frog and Toad", "I DONT REMEMBER", "9780060850524")
    result = search_books_in_catalog("remember", "author")
    assert len(result) == 1 and result[0]["author"].lower() == "i dont remember".lower()

def test_search_isbn_exact_match_only():
    _insert_book("Dune", "Frank Herbert", "9780441013593")
    result_success = search_books_in_catalog("9780441013593", "isbn")
    result_fail = search_books_in_catalog("978044101359", "isbn")  # too short
    assert len(result_success) == 1 and result_success[0]["title"] == "Dune"
    assert result_fail == []

def test_search_invalid_type_or_empty_term_returns_empty():
    assert search_books_in_catalog("anything", "publisher") == []
    assert search_books_in_catalog("   ", "title") == []
    
def test_search_incomplete_isbn_returns_error():
    result = search_books_in_catalog("123456", "isbn")
    assert result == []
    