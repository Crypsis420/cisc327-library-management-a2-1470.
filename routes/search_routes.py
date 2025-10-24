"""
Search Routes - Book search functionality
"""

from flask import Blueprint, render_template, request, flash
from services.library_service import search_books_in_catalog

search_bp = Blueprint('search', __name__)

@search_bp.route('/search')
def search_books():
    """
    Search for books in the catalog.
    Web interface for R5: Book Search Functionality
    """
    search_term = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'title')
    
    if not search_term:
        return render_template('search.html', books=[], search_term='', search_type=search_type)
    
    # Use business logic function
    books = search_books_in_catalog(search_term, search_type)
    
    if not books:
        flash('Not Found.', 'error')
    
    return render_template('search.html', books=books, search_term=search_term, search_type=search_type)
