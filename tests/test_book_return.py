from datetime import datetime, timedelta
from library_service import return_book_by_patron
from database import get_db_connection
import pytest

def _seed_active_borrow(patron="123456", title="Dune", isbn="6666666666666", overdue_days=0):
    """Create a book active borrow, that was overdue days ago."""
    conn = get_db_connection()
    cur = conn.execute(
        'INSERT INTO books (title, author, isbn, total_copies, available_copies) VALUES (?,?,?,?,?)',
        (title, "Author", isbn, 1, 1)
    )
    book_id = cur.lastrowid
    borrow_date = datetime.now() - timedelta(days=14 + overdue_days)
    due_date = borrow_date + timedelta(days=14)
    conn.execute('INSERT INTO borrow_records (patron_id, book_id, borrow_date, due_date) VALUES (?,?,?,?)',
                 (patron, book_id, borrow_date.isoformat(), due_date.isoformat()))
    conn.execute('UPDATE books SET available_copies = available_copies - 1 WHERE id=?', (book_id,))
    conn.commit()
    conn.close()
    return book_id

def test_return_validates_parameters():
    success, message = return_book_by_patron("12a456", 1)
    assert success is False
    assert "invalid patron id" in message.lower()

def test_return_verifies_borrowed_by_patron():
    # Create a book but do not create an active borrow for this patron/book
    conn = get_db_connection()
    cur = conn.execute(
        'INSERT INTO books (title, author, isbn, total_copies, available_copies) VALUES (?,?,?,?,?)',
        ("book", "A", "7777777777777", 1, 1)
    )
    bid = cur.lastrowid
    conn.commit(); conn.close()

    success, message = return_book_by_patron("123456", bid)
    assert success is False
    assert "does not have an active borrow" in message.lower()

def test_return_updates_availability_and_records_return_date():
    book_id = _seed_active_borrow(overdue_days=0)
    success, message = return_book_by_patron("123456", book_id)
    assert success is True
    conn = get_db_connection()
    ac = conn.execute('SELECT available_copies FROM books WHERE id=?', (book_id,)).fetchone()["available_copies"]
    ret = conn.execute('SELECT return_date FROM borrow_records WHERE patron_id=? AND book_id=?',
                       ("123456", book_id)).fetchone()["return_date"]
    conn.close()
    assert ac == 1
    assert ret is not None

def test_return_calculates_and_displays_late_fees():
    # 10 days overdue fee = 7*0.5 + 3*1.0 = 6.50
    book_id = _seed_active_borrow(overdue_days=10)
    success, message = return_book_by_patron("123456", book_id)
    assert success is True
    assert "10 day(s) overdue" in message
    assert "$6.50" in message
