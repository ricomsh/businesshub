from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.decorators import role_required
from app.email import send_ir_submission_email # Import the new email function
import datetime
import logging

logger = logging.getLogger(__name__)
ir_bp = Blueprint('ir', __name__, template_folder='templates', url_prefix='/ir')

def get_next_ir_slip_id():
    """Generates a new sequential IR Slip ID."""
    db = current_app.db
    # Find the last slip to determine the next number
    last_slip = db.counters.find_one_and_update(
        {'_id': 'ir_slip_id'},
        {'$inc': {'sequence_value': 1}},
        upsert=True,
        return_document=True
    )
    sequence = last_slip.get('sequence_value', 1)
    return f"IR-{datetime.datetime.now().year}-{sequence:04d}"

@ir_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'qc', 'ir')
def new_ir_slip():
    if request.method == 'POST':
        logger.info(f"New IR submission started by user: {current_user.email}")
        db = current_app.db
        
        slip_id = get_next_ir_slip_id()
        
        # Collect form data
        ir_data = {
            'slip_id': slip_id,
            'slip_type': 'ir',
            'order_number': request.form.get('order_number'),
            'nature_of_complaint': request.form.get('nature_of_complaint'),
            'corrective_action': request.form.get('corrective_action'),
            'status': 'Open',
            'created_by_name': current_user.name,
            'created_by_email': current_user.email,
            'created_at': datetime.datetime.utcnow(),
        }
        
        logger.info(f"Form data collected for IR slip {slip_id}: {ir_data}")

        try:
            # Save to database
            db.slips.insert_one(ir_data)
            logger.info(f"IR Slip {slip_id} successfully saved to MongoDB.")
            
            # Send email notification
            email_sent = send_ir_submission_email(ir_data)
            
            if email_sent:
                flash(f'New Incident Report {slip_id} created and email notification sent!', 'success')
            else:
                flash(f'New Incident Report {slip_id} was created, but the email notification failed. Please contact IT.', 'warning')

        except Exception as e:
            logger.error(f"Database error during IR slip submission: {e}")
            flash('A database error occurred. Please try again.', 'danger')
            return render_template('ir_form.html')

        return redirect(url_for('ir.view_ir_slips'))
        
    return render_template('ir_form.html')

@ir_bp.route('/view')
@login_required
@role_required('admin', 'qc', 'sales', 'ir', 'dispatch')
def view_ir_slips():
    db = current_app.db
    # Fetch all slips with the type 'ir'
    slips = list(db.slips.find({'slip_type': 'ir'}).sort('created_at', -1))
    return render_template('ir_viewer.html', slips=slips)
