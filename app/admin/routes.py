from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.decorators import role_required
from bson.objectid import ObjectId
import datetime

admin_bp = Blueprint('admin', __name__, template_folder='templates', url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    """Admin dashboard to manage users and data."""
    db = current_app.db
    
    # Fetch orders that are flagged for review
    flagged_orders = list(db.slips.find({'status': 'Dispatched - Pending Review'}))
    
    # Fetch the current email testing status, defaulting to True (ON) if not set
    email_setting = db.settings.find_one({'_id': 'email_config'})
    email_testing_status = email_setting.get('testing_mode', True) if email_setting else True

    return render_template('admin_dashboard.html', flagged_orders=flagged_orders, email_testing_status=email_testing_status)

@admin_bp.route('/toggle_email_testing', methods=['POST'])
@login_required
@role_required('admin')
def toggle_email_testing():
    """Toggles the email testing mode on or off."""
    db = current_app.db
    settings_collection = db.settings

    # Find the current setting, default to True (ON) if it doesn't exist
    current_setting = settings_collection.find_one({'_id': 'email_config'})
    current_status = current_setting.get('testing_mode', True) if current_setting else True
    
    # Toggle the status
    new_status = not current_status
    
    # Update the setting in the database, or create it if it doesn't exist (upsert=True)
    settings_collection.update_one(
        {'_id': 'email_config'},
        {'$set': {'testing_mode': new_status}},
        upsert=True
    )
    
    mode = "ON" if new_status else "OFF"
    flash(f"Email testing mode has been turned {mode}.", "success")
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/review_dispatch/<slip_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def review_dispatch(slip_id):
    db = current_app.db
    slip_to_review = db.slips.find_one({'_id': ObjectId(slip_id)})

    if not slip_to_review:
        flash('Slip not found.', 'danger')
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        qc_comments = request.form.get('comments')
        
        db.slips.update_one(
            {'_id': ObjectId(slip_id)},
            {'$set': {'status': 'Dispatched', 'reviewed_by': current_user.email, 'reviewed_at': datetime.datetime.utcnow()}}
        )
        
        db.slips.insert_one({
            'slip_type': 'qc',
            'order_number': slip_to_review.get('order_number'),
            'status': 'Complete',
            'created_at': datetime.datetime.utcnow(),
            'created_by': current_user.email,
            'comments': qc_comments,
            'is_retroactive': True
        })

        flash(f"Order {slip_to_review.get('order_number')} has been approved and a retroactive QC slip was created.", 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('review_dispatch.html', slip=slip_to_review)
