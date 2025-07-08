# FILE: app/api_routes.py

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required
from .database import get_mongo_db, get_sql_conn
import re

# Create a Blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')
# I have removed the database connection from the module level to fix the context error.

@api_bp.route('/get_part_details/<stock_code>')
@login_required
def get_part_details(stock_code):
    """
    API endpoint to fetch part details from the MongoDB 'parts' collection.
    """
    # A database connection is now correctly established inside the function.
    db = get_mongo_db()
    try:
        part = db.parts.find_one({'stock_code': stock_code})
        if part:
            # Convert ObjectId to string for JSON serialization
            part['_id'] = str(part['_id'])
            return jsonify(part)
        else:
            return jsonify({'error': 'Part not found'}), 404
    except Exception as e:
        current_app.logger.error(f"Error fetching part details for {stock_code}: {e}")
        return jsonify({'error': 'An internal error occurred'}), 500

@api_bp.route('/search-orders')
@login_required
def search_orders():
    """API endpoint to search for sales orders for Select2 dropdowns."""
    db = get_mongo_db()
    search_term = request.args.get('q', '')
    if len(search_term) < 2:
        return jsonify({'results': []})
    
    query = {"OrderID": {"$regex": search_term, "$options": "i"}}
    distinct_orders = db.orders.distinct("OrderID", query)
    results = [{"id": order, "text": order} for order in distinct_orders]
    return jsonify({'results': results})

@api_bp.route('/order-details/<order_id>')
@login_required
def get_order_details(order_id):
    """API endpoint to get line item details for a given sales order."""
    sql_conn = None
    try:
        sql_conn = get_sql_conn()
        cursor = sql_conn.cursor()
        
        # This is the corrected query that prioritizes Misc_Reference.
        query = """
            SELECT
                CUST_ORDER_LINE.LINE_NO AS LineNumber,
                COALESCE(NULLIF(TRIM(CUST_ORDER_LINE.Misc_Reference), ''), TRIM(PART.DESCRIPTION)) AS PartDescription,
                TRIM(CUST_ORDER_LINE.PART_ID) AS PartID,
                TRIM(CUST_ORDER_LINE.Misc_Reference) AS MiscReference,
                CUST_ORDER_LINE.ORDER_QTY AS OrderQty
            FROM CUST_ORDER_LINE
            LEFT JOIN PART ON PART.ID = CUST_ORDER_LINE.PART_ID
            WHERE CUST_ORDER_LINE.CUST_ORDER_ID = ?
        """
        cursor.execute(query, order_id)
        
        # This is the corrected, robust way to process the SQL results.
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        line_items = [dict(zip(columns, row)) for row in rows]
        
        return jsonify(line_items)
        
    except Exception as e:
        current_app.logger.error(f"Failed to fetch order details for {order_id}: {e}")
        return jsonify({"error": "Failed to fetch details"}), 500
    finally:
        if sql_conn:
            sql_conn.close()

@api_bp.route('/search-users')
@login_required
def search_users():
    """
    API endpoint to search within a specific list (e.g., production_managers)
    from the dropdown_options collection in MongoDB.
    """
    db = get_mongo_db()
    list_name = request.args.get('list')
    search_term = request.args.get('q', '')

    if not list_name:
        return jsonify({"results": []})
    
    # This is the corrected logic to search the 'dropdown_options' collection.
    pipeline = [
        {'$match': {'_id': list_name}},
        {'$unwind': '$options'},
        {
            '$match': {
                'options.name': {'$regex': re.escape(search_term), '$options': 'i'}
            }
        },
        {
            '$project': {
                'id': '$options.email',
                'text': '$options.name'
            }
        }
    ]
    
    results = list(db.dropdown_options.aggregate(pipeline))
    return jsonify({"results": results})
