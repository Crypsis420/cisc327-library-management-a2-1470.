"""
Database module for Library Management System
Handles all database operations and connections
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Database configuration
DATABASE = 'library.db'

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def init_database():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    
    # Create books table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE NOT NULL,
            total_copies INTEGER NOT NULL,
            available_copies INTEGER NOT NULL
        )
    ''')
    
    # Create borrow_records table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS borrow_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patron_id TEXT NOT NULL,
            book_id INTEGER NOT NULL,
            borrow_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT,
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_sample_data():
    """Add sample data to the database if it's empty."""
    conn = get_db_connection()
    book_count = conn.execute('SELECT COUNT(*) as count FROM books').fetchone()['count']
    
    if book_count == 0:
        # Add sample books
        sample_books = [
            ('The Great Gatsby', 'F. Scott Fitzgerald', '9780743273565', 3),
            ('To Kill a Mockingbird', 'Harper Lee', '9780061120084', 2),
            ('1984', 'George Orwell', '9780451524935', 1)
        ]
        
        for title, author, isbn, copies in sample_books:
            conn.execute('''
                INSERT INTO books (title, author, isbn, total_copies, available_copies)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, author, isbn, copies, copies))
        
        # Make 1984 unavailable by adding a borrow record
        conn.execute('''
            INSERT INTO borrow_records (patron_id, book_id, borrow_date, due_date)
            VALUES (?, ?, ?, ?)
        ''', ('123456', 3, 
              (datetime.now() - timedelta(days=5)).isoformat(),
              (datetime.now() + timedelta(days=9)).isoformat()))
        
        # Update available copies for 1984
        conn.execute('UPDATE books SET available_copies = 0 WHERE id = 3')
        
        conn.commit()
    
    conn.close()

# Helper Functions for Database Operations

def get_all_books() -> List[Dict]:
    """Get all books from the database."""
    conn = get_db_connection()
    books = conn.execute('SELECT * FROM books ORDER BY title').fetchall()
    conn.close()
    return [dict(book) for book in books]

def get_book_by_id(book_id: int) -> Optional[Dict]:
    """Get a specific book by ID."""
    conn = get_db_connection()
    book = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
    conn.close()
    return dict(book) if book else None

def get_book_by_isbn(isbn: str) -> Optional[Dict]:
    """Get a specific book by ISBN."""
    conn = get_db_connection()
    book = conn.execute('SELECT * FROM books WHERE isbn = ?', (isbn,)).fetchone()
    conn.close()
    return dict(book) if book else None

def get_patron_borrowed_books(patron_id: str) -> List[Dict]:
    """Get currently borrowed books for a patron."""
    conn = get_db_connection()
    records = conn.execute('''
        SELECT br.*, b.title, b.author 
        FROM borrow_records br 
        JOIN books b ON br.book_id = b.id 
        WHERE br.patron_id = ? AND br.return_date IS NULL
        ORDER BY br.borrow_date
    ''', (patron_id,)).fetchall()
    conn.close()
    
    borrowed_books = []
    for record in records:
        borrowed_books.append({
            'book_id': record['book_id'],
            'title': record['title'],
            'author': record['author'],
            'borrow_date': datetime.fromisoformat(record['borrow_date']),
            'due_date': datetime.fromisoformat(record['due_date']),
            'is_overdue': datetime.now() > datetime.fromisoformat(record['due_date'])
        })
    
    return borrowed_books

def get_patron_borrow_count(patron_id: str) -> int:
    """Get the number of books currently borrowed by a patron."""
    conn = get_db_connection()
    count = conn.execute('''
        SELECT COUNT(*) as count FROM borrow_records 
        WHERE patron_id = ? AND return_date IS NULL
    ''', (patron_id,)).fetchone()['count']
    conn.close()
    return count

def insert_book(title: str, author: str, isbn: str, total_copies: int, available_copies: int) -> bool:
    """Insert a new book into the database."""
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO books (title, author, isbn, total_copies, available_copies)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, author, isbn, total_copies, available_copies))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def insert_borrow_record(patron_id: str, book_id: int, borrow_date: datetime, due_date: datetime) -> bool:
    """Insert a new borrow record into the database."""
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO borrow_records (patron_id, book_id, borrow_date, due_date)
            VALUES (?, ?, ?, ?)
        ''', (patron_id, book_id, borrow_date.isoformat(), due_date.isoformat()))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def update_book_availability(book_id: int, change: int) -> bool:
    """Update the available copies of a book by a given amount (+1 for return, -1 for borrow)."""
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE books SET available_copies = available_copies + ? WHERE id = ?
        ''', (change, book_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def update_borrow_record_return_date(patron_id: str, book_id: int, return_date: datetime) -> bool:
    """Update the return date for a borrow record."""
    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE borrow_records 
            SET return_date = ? 
            WHERE patron_id = ? AND book_id = ? AND return_date IS NULL
        ''', (return_date.isoformat(), patron_id, book_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False
    
def get_borrow_records_by_patron(patron_id: str) -> List[Dict]:
    """Get full borrow history"""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            '''
            SELECT br.*, b.title, b.author
            FROM borrow_records br
            JOIN books b ON b.id = br.book_id
            WHERE br.patron_id = ?
            ORDER BY datetime(br.borrow_date) DESC
            ''',
            (patron_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        conn.close()
        return False
