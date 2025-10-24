from datetime import datetime, timedelta
from database import get_db_connection
from services.library_service import get_patron_status_report
import pytest

def _insert_book(title, author, isbn):
    conn = get_db_connection()
    cur = conn.execute(
        'INSERT INTO books (title, author, isbn, total_copies, available_copies) VALUES (?,?,?,?,?)',
        (title, author, isbn, 1, 1)
    )
    bid = cur.lastrowid
    conn.commit(); conn.close()
    return bid

def _add_active_borrow(patron, book_id, days_overdue=0):
    conn = get_db_connection()
    borrow_date = datetime.now() - timedelta(days=14 + days_overdue)
    due_date = borrow_date + timedelta(days=14)
    conn.execute('INSERT INTO borrow_records (patron_id, book_id, borrow_date, due_date) VALUES (?,?,?,?)',
                 (patron, book_id, borrow_date.isoformat(), due_date.isoformat()))
    conn.execute('UPDATE books SET available_copies = available_copies - 1 WHERE id=?', (book_id,))
    conn.commit(); conn.close()

def _add_returned_borrow(patron, book_id, days_ago_borrowed=20, returned_days_ago=5):
    conn = get_db_connection()
    borrow_date = datetime.now() - timedelta(days=days_ago_borrowed)
    due_date = borrow_date + timedelta(days=14)
    return_date = datetime.now() - timedelta(days=returned_days_ago)
    conn.execute('INSERT INTO borrow_records (patron_id, book_id, borrow_date, due_date, return_date) VALUES (?,?,?,?,?)',
                 (patron, book_id, borrow_date.isoformat(), due_date.isoformat(), return_date.isoformat()))
    conn.commit(); conn.close()

def test_patron_status_invalid_id():
    report = get_patron_status_report("12a456")
    assert report["status"] == "Invalid patron ID"
    assert report["borrowed_count"] == 0
    assert report["total_late_fees"] == 0.0

def test_patron_status_includes_active_fees_and_history():
    
    # Active overdue 3 days = 3 * 0.50 = $1.50
    b1 = _insert_book("1984", "George Orwell", "9999999999991")
    _add_active_borrow("123456", b1, days_overdue=3)

    # Returned history row
    b2 = _insert_book("Gatsby", "F. Scott Fitzgerald", "9999999999992")
    _add_returned_borrow("123456", b2)

    report = get_patron_status_report("123456")
    assert report["status"] == "ok"
    assert report["borrowed_count"] == 1
    assert report["total_late_fees"] == 1.50
    assert any(h["title"] == "Gatsby" for h in report["history"])
    assert report["currently_borrowed"][0]["title"] == "1984"
