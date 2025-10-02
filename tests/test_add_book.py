from library_service import add_book_to_catalog
from database import get_book_by_isbn
import pytest

def test_add_book_valid_input():
    success, message = add_book_to_catalog("I like Potatoes", "Russet", "1234567890123", 5)
    assert success is True
    assert "successfully added" in message.lower()
    assert get_book_by_isbn("1234567890123") is not None

def test_add_book_duplicate_isbn_blocks():
    add_book_to_catalog("A", "B", "1111111111111", 1)
    success, message = add_book_to_catalog("A2", "B2", "1111111111111", 2)
    assert success is False
    assert "already exists" in message.lower()

def test_add_book_invalid_isbn_length():
    success, message = add_book_to_catalog("Western Sucks", "Me", "12345", 1)
    assert success is False
    assert "13 digits" in message

def test_add_book_empty_title():
    success, message = add_book_to_catalog("", "I wrote nothing", "2222222222222", 1)
    assert success is False
    assert "title is required" in message.lower()
    
def test_add_book_empty_author():
    success, message = add_book_to_catalog("No one wrote me", "", "2222222222222", 1)
    assert success is False
    assert "author is required" in message.lower()

def test_add_book_non_positive_total_copies():
    success, message = add_book_to_catalog("Can he fix it", "Bob the Builder", "3333333333333", 0)
    assert success is False
    assert "positive integer" in message.lower()
    
def test_add_book_invalid_isbn_non_digit():
    """ISBN has non-digit characters."""
    success, msg = add_book_to_catalog("Book Title", "Author Name", "12345abc90123", 5)
    assert success is False
    assert "isbn must be digits" in msg.lower()

def test_add_book_title_too_long():
    """Title exceeds 200 characters."""
    long_title = "A" * 201
    success, msg = add_book_to_catalog(long_title, "Author Name", "1234567890123", 5)
    assert success is False
    assert "title must be less than 200 characters" in msg.lower()

def test_add_book_author_too_long():
    """Author exceeds 100 characters."""
    long_author = "B" * 101
    success, msg = add_book_to_catalog("Book Title", long_author, "1234567890123", 5)
    assert success is False
    assert "author must be less than 100 characters" in msg.lower()
