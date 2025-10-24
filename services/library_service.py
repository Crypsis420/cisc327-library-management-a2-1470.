"""
Library Service Module - Business Logic Functions
Contains all the core business logic for the Library Management System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books, get_patron_borrowed_books, 
    get_borrow_records_by_patron
)

from services.payment_service import PaymentGateway

def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
    """
    Add a new book to the catalog.
    Implements R1: Book Catalog Management
    
    Args:
        title: Book title (max 200 chars)
        author: Book author (max 100 chars)
        isbn: 13-digit ISBN
        total_copies: Number of copies (positive integer)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Input validation
    if not title or not title.strip():
        return False, "Title is required."
    
    if len(title.strip()) > 200:
        return False, "Title must be less than 200 characters."
    
    if not author or not author.strip():
        return False, "Author is required."
    
    if len(author.strip()) > 100:
        return False, "Author must be less than 100 characters."
    
    if len(isbn) != 13:
        return False, "ISBN must be exactly 13 digits."
    
    for i in isbn:
        if not i.isdigit():
            return False, "ISBN must be digits."
    
    if not isinstance(total_copies, int) or total_copies <= 0:
        return False, "Total copies must be a positive integer."
    
    # Check for duplicate ISBN
    existing = get_book_by_isbn(isbn)
    if existing:
        return False, "A book with this ISBN already exists."
    
    # Insert new book
    success = insert_book(title.strip(), author.strip(), isbn, total_copies, total_copies)
    if success:
        return True, f'Book "{title.strip()}" has been successfully added to the catalog.'
    else:
        return False, "Database error occurred while adding the book."

def borrow_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Allow a patron to borrow a book.
    Implements R3 as per requirements  
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to borrow
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    # Check if book exists and is available
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."
    
    # Check patron's current borrowed books count
    current_borrowed = get_patron_borrow_count(patron_id)
    
    if current_borrowed >= 5:
        return False, "You have reached the maximum borrowing limit of 5 books."
    
    # Create borrow record
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    
    # Insert borrow record and update availability
    borrow_success = insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    if not borrow_success:
        return False, "Database error occurred while creating borrow record."
    
    availability_success = update_book_availability(book_id, -1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."
    
    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}.'

def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Process book return by a patron.
    Implements R4 as per requirements  

    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book being returned

    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."

    # Validate book exists
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."

    # Verify patron currently has this specific book and get its due date/title
    active = get_patron_borrowed_books(patron_id) or []
    record = next((r for r in active if r.get('book_id') == book_id), None)
    if not record:
        return False, "This patron does not have an active borrow for this book."

    if not isinstance(record.get('due_date'), datetime):
        return False, "Corrupt borrow record: missing due date."

    # Late fee (R5) via the public API function below
    fee_info = calculate_late_fee_for_book(patron_id, book_id)
    days = fee_info.get('days_overdue', 0)
    fee = fee_info.get('fee_amount', 0.0)

    # Persist return & increment availability
    return_date = datetime.now()
    if not update_borrow_record_return_date(patron_id, book_id, return_date):
        return False, "Database error occurred while recording the return."

    if not update_book_availability(book_id, +1):
        return False, "Database error occurred while updating book availability."

    if days > 0 and fee > 0:
        return True, (
            f'Return processed. "{book["title"]}" was {days} day(s) overdue. '
            f'Late fee: ${fee:.2f}.'
        )
    else:
        return True, f'Return processed. "{book["title"]}" was returned on time. No late fee.'

def calculate_late_fee_for_book(patron_id: str, book_id: int) -> Dict:
    """
    Calculate late fees for a specific book.
    Implements R5 as per requirements  

    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to check for late fees

    Returns:
        dict: {
            'fee_amount': float,       # total fee in dollars
            'days_overdue': int,       # number of days overdue
            'status': str              # message about calculation
        }
    """
    # Validate inputs and existence
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {'fee_amount': 0.00, 'days_overdue': 0, 'status': 'Invalid patron ID'}

    book = get_book_by_id(book_id)
    if not book:
        return {'fee_amount': 0.00, 'days_overdue': 0, 'status': 'Book not found'}

    # Find this active borrow
    active = get_patron_borrowed_books(patron_id) or []
    record = next((r for r in active if r.get('book_id') == book_id), None)
    if not record:
        return {'fee_amount': 0.00, 'days_overdue': 0, 'status': 'No active borrow record found for this book'}

    due_date = record.get('due_date')
    if not isinstance(due_date, datetime):
        return {'fee_amount': 0.00, 'days_overdue': 0, 'status': 'Corrupt borrow record'}

    # Compute days overdue (non-negative whole days)
    now = datetime.now()
    days_overdue = max((now.date() - due_date.date()).days, 0)

    if days_overdue <= 0:
        fee = 0.00
    else:
        first7 = min(days_overdue, 7) * 0.50
        extra = max(days_overdue - 7, 0) * 1.00
        fee = min(first7 + extra, 15.00)

    return {
        'fee_amount': float(f"{fee:.2f}"),
        'days_overdue': days_overdue,
        'status': 'Overdue' if days_overdue > 0 else 'Not overdue'
    }

def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
    """
    Search for books in the catalog.
    Implements R6 as per requirements  

    Args:
        search_term: The text to search for (title, author, or ISBN)
        search_type: The type of search ('title', 'author', 'isbn')

    Returns:
        list: List of matching book records (each as a dict)
    """
    if not search_type or search_type not in {'title', 'author', 'isbn'}:
        return []

    term = (search_term or "").strip()
    if not term:
        return []

    if search_type == 'isbn':
        if len(term) != 13 or not term.isdigit():
            return []
        book = get_book_by_isbn(term)
        return [book] if book else []

    all_books = get_all_books() or []
    t = term.lower()

    if search_type == 'title':
        return [b for b in all_books if (b.get('title') or '').lower().find(t) != -1]

    if search_type == 'author':
        return [b for b in all_books if (b.get('author') or '').lower().find(t) != -1]

    return []

def get_patron_status_report(patron_id: str) -> Dict:
    """
    Get status report for a patron.
    Implements R7 as per requirements  

    Args:
        patron_id: 6-digit library card ID

    Returns:
        dict: {
            'patron_id': str,
            'currently_borrowed': list,   # books still borrowed
            'total_late_fees': float,     # total fees owed
            'borrowed_count': int,        # number of active borrows
            'history': list,              # all past borrow records
            'status': str                 # 'ok' or error message
        }
    """
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {
            'patron_id': patron_id,
            'currently_borrowed': [],
            'total_late_fees': 0.00,
            'borrowed_count': 0,
            'history': [],
            'status': 'Invalid patron ID'
        }

    active = get_patron_borrowed_books(patron_id)

    # Build list and sum late fees.
    now = datetime.now()
    current_rows: List[Dict] = []
    total_fees = 0.0
    for r in active:
        due = r.get('due_date')
        if not isinstance(due, datetime):
            continue
        days_overdue = max((now.date() - due.date()).days, 0)
        if days_overdue <= 0:
            fee = 0.00
        else:
            first7 = min(days_overdue, 7) * 0.50
            extra = max(days_overdue - 7, 0) * 1.00
            fee = min(first7 + extra, 15.00)
        total_fees += fee
        current_rows.append({
            'book_id': r.get('book_id'),
            'title': r.get('title'),
            'due_date': due.strftime('%Y-%m-%d'),
            'overdue_days': days_overdue,
            'accrued_fee': float(f"{fee:.2f}")
        })
        
    raw_rows = get_borrow_records_by_patron(patron_id) or []
    history: List[Dict] = []
    for row in raw_rows:
        bd = row['borrow_date']
        dd = row['due_date']
        rd = row['return_date']
        borrow_date_str = datetime.fromisoformat(bd).strftime('%Y-%m-%d') if bd else None
        due_date_str    = datetime.fromisoformat(dd).strftime('%Y-%m-%d') if dd else None
        return_date_str = datetime.fromisoformat(rd).strftime('%Y-%m-%d') if rd else None

        history.append({
            'book_id': row['book_id'],
            'title': row['title'],
            'borrow_date': borrow_date_str,
            'due_date': due_date_str,
            'return_date': return_date_str
        })

    return {
        'patron_id': patron_id,
        'currently_borrowed': current_rows,
        'total_late_fees': float(f"{round(total_fees, 2):.2f}"),
        'borrowed_count': len(active),
        'history': history,
        'status': 'ok'
    }

def pay_late_fees(patron_id: str, book_id: int, payment_gateway: PaymentGateway = None) -> Tuple[bool, str, Optional[str]]:
    """
    Process payment for late fees using external payment gateway.
    
    NEW FEATURE FOR ASSIGNMENT 3: Demonstrates need for mocking/stubbing
    This function depends on an external payment service that should be mocked in tests.
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book with late fees
        payment_gateway: Payment gateway instance (injectable for testing)
        
    Returns:
        tuple: (success: bool, message: str, transaction_id: Optional[str])
        
    Example for you to mock:
        # In tests, mock the payment gateway:
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.process_payment.return_value = (True, "txn_123", "Success")
        success, msg, txn = pay_late_fees("123456", 1, mock_gateway)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits.", None
    
    # Calculate late fee first
    fee_info = calculate_late_fee_for_book(patron_id, book_id)
    
    # Check if there's a fee to pay
    if not fee_info or 'fee_amount' not in fee_info:
        return False, "Unable to calculate late fees.", None
    
    fee_amount = fee_info.get('fee_amount', 0.0)
    
    if fee_amount <= 0:
        return False, "No late fees to pay for this book.", None
    
    # Get book details for payment description
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found.", None
    
    # Use provided gateway or create new one
    if payment_gateway is None:
        payment_gateway = PaymentGateway()
    
    # Process payment through external gateway
    # THIS IS WHAT YOU SHOULD MOCK IN THEIR TESTS!
    try:
        success, transaction_id, message = payment_gateway.process_payment(
            patron_id=patron_id,
            amount=fee_amount,
            description=f"Late fees for '{book['title']}'"
        )
        
        if success:
            return True, f"Payment successful! {message}", transaction_id
        else:
            return False, f"Payment failed: {message}", None
            
    except Exception as e:
        # Handle payment gateway errors
        return False, f"Payment processing error: {str(e)}", None


def refund_late_fee_payment(transaction_id: str, amount: float, payment_gateway: PaymentGateway = None) -> Tuple[bool, str]:
    """
    Refund a late fee payment (e.g., if book was returned on time but fees were charged in error).
    
    NEW FEATURE FOR ASSIGNMENT 3: Another function requiring mocking
    
    Args:
        transaction_id: Original transaction ID to refund
        amount: Amount to refund
        payment_gateway: Payment gateway instance (injectable for testing)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate inputs
    if not transaction_id or not transaction_id.startswith("txn_"):
        return False, "Invalid transaction ID."
    
    if amount <= 0:
        return False, "Refund amount must be greater than 0."
    
    if amount > 15.00:  # Maximum late fee per book
        return False, "Refund amount exceeds maximum late fee."
    
    # Use provided gateway or create new one
    if payment_gateway is None:
        payment_gateway = PaymentGateway()
    
    # Process refund through external gateway
    # THIS IS WHAT YOU SHOULD MOCK IN YOUR TESTS!
    try:
        success, message = payment_gateway.refund_payment(transaction_id, amount)
        
        if success:
            return True, message
        else:
            return False, f"Refund failed: {message}"
            
    except Exception as e:
        return False, f"Refund processing error: {str(e)}"