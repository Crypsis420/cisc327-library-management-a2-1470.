"""
API Routes - JSON API endpoints
"""

from flask import Blueprint, jsonify, request
from services.library_service import calculate_late_fee_for_book, search_books_in_catalog

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/late_fee/<patron_id>/<int:book_id>')
def get_late_fee(patron_id, book_id):
    """
    Calculate late fee for a specific book borrowed by a patron.
    API endpoint for R4: Late Fee Calculation
    """
    result = calculate_late_fee_for_book(patron_id, book_id)
    return jsonify(result), 501 if 'not implemented' in result.get('status', '') else 200

@api_bp.route('/search')
def search_books_api():
    """
    Search for books via API endpoint.
    Alternative API interface for R5: Book Search Functionality
    """
    search_term = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'title')
    
    if not search_term:
        return jsonify({'error': 'Search term is required'}), 400
    
    # Use business logic function
    books = search_books_in_catalog(search_term, search_type)
    
    return jsonify({
        'search_term': search_term,
        'search_type': search_type,
        'results': books,
        'count': len(books)
    })
