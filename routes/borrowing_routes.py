"""
Borrowing Routes - Book borrowing and returning endpoints
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from services.library_service import borrow_book_by_patron, return_book_by_patron

borrowing_bp = Blueprint('borrowing', __name__)

@borrowing_bp.route('/borrow', methods=['POST'])
def borrow_book():
    """
    Process book borrowing request.
    Web interface for R2: Book Borrowing
    """
    patron_id = request.form.get('patron_id', '').strip()
    
    try:
        book_id = int(request.form.get('book_id', ''))
    except (ValueError, TypeError):
        flash('Invalid book ID.', 'error')
        return redirect(url_for('catalog.catalog'))
    
    # Use business logic function
    success, message = borrow_book_by_patron(patron_id, book_id)
    
    flash(message, 'success' if success else 'error')
    return redirect(url_for('catalog.catalog'))

@borrowing_bp.route('/return', methods=['GET', 'POST'])
def return_book():
    """
    Process book return.
    Web interface for R3: Book Return Processing
    """
    if request.method == 'GET':
        return render_template('return_book.html')
    
    patron_id = request.form.get('patron_id', '').strip()
    
    try:
        book_id = int(request.form.get('book_id', ''))
    except (ValueError, TypeError):
        flash('Invalid book ID.', 'error')
        return render_template('return_book.html')
    
    # Use business logic function
    success, message = return_book_by_patron(patron_id, book_id)
    
    flash(message, 'success' if success else 'error')
    return render_template('return_book.html')
