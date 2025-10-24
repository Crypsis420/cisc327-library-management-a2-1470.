from services.library_service import borrow_book_by_patron
from database import get_db_connection
import pytest

def _insert_book(title="books R Cool", author="Cool Person", isbn="6767676767676", copies=2):
    conn = get_db_connection()
    cur = conn.execute(
        'INSERT INTO books (title, author, isbn, total_copies, available_copies) VALUES (?,?,?,?,?)',
        (title, author, isbn, copies, copies)
    )
    conn.commit()
    bid = cur.lastrowid
    conn.close()
    return bid

def _count_active_borrows(patron_id, book_id):
    conn = get_db_connection()
    c = conn.execute('SELECT COUNT(*) AS c FROM borrow_records WHERE patron_id=? AND book_id=? AND return_date IS NULL',
                     (patron_id, book_id)).fetchone()["c"]
    conn.close()
    return c

def test_creates_record_and_decrements_availability():
    book_id = _insert_book(copies=2)
    success, message = borrow_book_by_patron("123456", book_id)
    assert success is True

    conn = get_db_connection()
    ac = conn.execute('SELECT available_copies FROM books WHERE id=?', (book_id,)).fetchone()["available_copies"]
    conn.close()
    assert ac == 1
    assert _count_active_borrows("123456", book_id) == 1

def test_borrow_invalid_patron_format():
    book_id = _insert_book()
    success, message = borrow_book_by_patron("12a456", book_id)
    assert success is False
    assert "invalid patron id" in message.lower()

def test_borrow_fails_when_unavailable():
    book_id = _insert_book(copies=1)
    borrow_book_by_patron("123456", book_id)  # use the only copy
    success, message = borrow_book_by_patron("654321", book_id)
    assert success is False
    assert "not available" in message.lower()

def test_borrow_max_5_books():
    """
    This test should Fail but apsses because of code using >5 instead of >=.
    """
    # Create 5 active borrows for patron on dummy books
    for i in range(5):
        book_id = _insert_book(title=f"B{i}", isbn=f"55555555555{i:02d}", copies=1)
        borrow_book_by_patron("123456", book_id)

    # Try a 6th
    sixth = _insert_book(title="Sixth", isbn="5555555555599", copies=1)
    success, message = borrow_book_by_patron("123456", sixth)
    assert success is False
