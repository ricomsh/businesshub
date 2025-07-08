from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user

# Setup Blueprint
main_bp = Blueprint('main', __name__, template_folder='templates')

@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Homepage of the application, shown after login."""
    db = current_app.db
    
    # Fetch statistics from the database
    # We will count the documents in each collection/slip_type
    total_users = db.users.count_documents({})
    
    # Count slips for each module type
    total_qc_slips = db.slips.count_documents({'slip_type': 'qc'})
    total_ir_slips = db.slips.count_documents({'slip_type': 'ir'})
    total_cc_slips = db.slips.count_documents({'slip_type': 'cc'})

    # Create a dictionary to pass all stats to the template
    stats = {
        'total_users': total_users,
        'total_qc_slips': total_qc_slips,
        'total_ir_slips': total_ir_slips,
        'total_cc_slips': total_cc_slips,
    }

    return render_template('dashboard.html', user=current_user, stats=stats)

