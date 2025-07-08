from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.decorators import role_required
from app.email import send_cc_submission_email # Import the new email function
import datetime
import logging

logger = logging.getLogger(__name__)
cc_bp = Blueprint('cc', __name__, template_folder='templates', url_prefix='/cc')

def get_next_cc_slip_id():
    """Generates a new sequential CC Slip ID."""
    db = current_app.db
    last_slip = db.counters.find_one_and_update(
        {'_id': 'cc_slip_id'},
        {'$inc': {'sequence_value': 1}},
        upsert=True,
        return_document=True
    )
    sequence = last_slip.get('sequence_value', 1)
    return f"CC-{datetime.datetime.now().year}-{sequence:04d}"

@cc_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'sales')
def new_cc_slip():
    if request.method == 'POST':
        logger.info(f"New CC submission started by user: {current_user.email}")
        db = current_app.db
        
        slip_id = get_next_cc_slip_id()
        
        cc_data = {
            'slip_id': slip_id,
            'slip_type': 'cc',
            'order_number': request.form.get('order_number'),
            'complaint_details': request.form.get('complaint_details'),
            'status': 'Open',
            'created_by_name': current_user.name,
            'created_by_email': current_user.email,
            'created_at': datetime.datetime.utcnow(),
        }
        
        logger.info(f"Form data collected for CC slip {slip_id}: {cc_data}")

        try:
            db.slips.insert_one(cc_data)
            logger.info(f"CC Slip {slip_id} successfully saved to MongoDB.")
            
            email_sent = send_cc_submission_email(cc_data)
            
            if email_sent:
                flash(f'New Customer Complaint {slip_id} created and email notification sent!', 'success')
            else:
                flash(f'New Customer Complaint {slip_id} was created, but the email notification failed. Please contact IT.', 'warning')

        except Exception as e:
            logger.error(f"Database error during CC slip submission: {e}")
            flash('A database error occurred. Please try again.', 'danger')
            return render_template('cc_form.html')

        return redirect(url_for('cc.view_cc_slips'))
        
    return render_template('cc_form.html')

@cc_bp.route('/view')
@login_required
@role_required('admin', 'qc', 'sales', 'ir', 'dispatch')
def view_cc_slips():
    db = current_app.db
    slips = list(db.slips.find({'slip_type': 'cc'}).sort('created_at', -1))
    return render_template('cc_viewer.html', slips=slips)
