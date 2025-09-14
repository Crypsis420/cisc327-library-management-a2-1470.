from datetime import datetime, timedelta
from library_service import calculate_late_fee_for_book
from database import get_db_connection
import pytest

def _seed_active_borrow(patron="123456", isbn="8888888888888", overdue_days=0):
    conn = get_db_connection()
    conn.execute('INSERT INTO books (title, author, isbn, total_copies, available_copies) VALUES (?,?,?,?,?)',
                 ("Book", "Auth", isbn, 1, 1))
    book_id = conn.execute('SELECT id FROM books WHERE isbn=?', (isbn,)).fetchone()["id"]
    borrow_date = datetime.now() - timedelta(days=14 + overdue_days)
    due_date = borrow_date + timedelta(days=14)
    conn.execute('INSERT INTO borrow_records (patron_id, book_id, borrow_date, due_date) VALUES (?,?,?,?)',
                 (patron, book_id, borrow_date.isoformat(), due_date.isoformat()))
    conn.execute('UPDATE books SET available_copies = available_copies - 1 WHERE id=?', (book_id,))
    conn.commit(); conn.close()
    return book_id

def test_fee_not_overdue():
    bid = _seed_active_borrow(overdue_days=0)
    res = calculate_late_fee_for_book("123456", bid)
    assert res["days_overdue"] == 0
    assert res["fee_amount"] == 0.0
    assert res["status"] == "Not overdue"

def test_fee_1_day_overdue():
    bid = _seed_active_borrow(isbn="8888888888881", overdue_days=1)
    res = calculate_late_fee_for_book("123456", bid)
    assert res["days_overdue"] == 1
    assert res["fee_amount"] == 0.50

def test_fee_8_days_overdue():
    bid = _seed_active_borrow(isbn="8888888888882", overdue_days=8)
    res = calculate_late_fee_for_book("123456", bid)
    assert res["days_overdue"] == 8
    assert res["fee_amount"] == 4.50  # 7*0.5 + 1*1.0

def test_fee_cap_at_15():
    bid = _seed_active_borrow(isbn="8888888888883", overdue_days=40)
    res = calculate_late_fee_for_book("123456", bid)
    assert res["fee_amount"] == 15.00
    assert res["status"] == "Overdue"
