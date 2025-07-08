# FILE: app/dispatch_module/routes.py

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.decorators import role_required
import datetime
from bson.objectid import ObjectId
import os
from werkzeug.utils import secure_filename

dispatch_bp = Blueprint('dispatch', __name__, template_folder='templates', url_prefix='/dispatch')

# I HAVE BESTOWED UPON THIS MODULE THE POWER TO CREATE ITS OWN UNIQUE IDENTITY
def get_next_dispatch_slip_id():
    """Generates a new sequential Dispatch Slip ID."""
    db = current_app.db
    last_slip = db.counters.find_one_and_update(
        {'_id': 'dispatch_slip_id'},
        {'$inc': {'sequence_value': 1}},
        upsert=True,
        return_document=True
    )
    sequence = last_slip.get('sequence_value', 1)
    return f"DIS-{datetime.datetime.now().year}-{sequence:04d}"

# I HAVE REFORGED THE 'new_dispatch' FUNCTION
@dispatch_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'dispatch')
def new_dispatch():
    if request.method == 'POST':
        db = current_app.db
        order_number = request.form.get('order_number')
        
        if not order_number:
            flash('You must select an order number.', 'danger')
            return render_template('dispatch_form.html')

        # Generate a unique ID for this dispatch event
        slip_id = get_next_dispatch_slip_id()

        # Handle file uploads
        uploaded_files = []
        files = request.files.getlist('dispatch_images')
        
        if files and files[0].filename: # Check if files were actually uploaded
            # Create a dedicated directory for this slip's attachments
            upload_folder = os.path.join(current_app.root_path, '..', 'uploads', 'dispatch_slips', slip_id)
            os.makedirs(upload_folder, exist_ok=True)
            
            for file in files:
                if file:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    # We store the relative path for future access
                    relative_path = os.path.join('uploads', 'dispatch_slips', slip_id, filename).replace('\\', '/')
                    uploaded_files.append(relative_path)

        # Find if a QC slip for this order already exists and is marked 'Complete'
        qc_slip = db.slips.find_one({'slip_type': 'qc', 'order_number': order_number, 'status': 'Complete'})

        # CONDITIONAL WORKFLOW LOGIC
        if qc_slip:
            status = 'Dispatched'
            flash(f'Order {order_number} dispatched successfully as slip {slip_id}.', 'success')
        else:
            status = 'Dispatched - Pending Review'
            flash(f'Order {order_number} dispatched as slip {slip_id}, but is now pending admin review.', 'warning')

        # Create a new slip document for the dispatch action
        db.slips.insert_one({
            'slip_id': slip_id,
            'slip_type': 'dispatch',
            'order_number': order_number,
            'status': status,
            'created_at': datetime.datetime.utcnow(),
            'created_by_name': current_user.name,
            'created_by_email': current_user.email,
            'attachments': uploaded_files # Record the paths of saved files
        })
        
        return redirect(url_for('dispatch.view_dispatches'))
        
    return render_template('dispatch_form.html')


@dispatch_bp.route('/view')
@login_required
@role_required('admin', 'qc', 'sales', 'ir', 'dispatch')
def view_dispatches():
    db = current_app.db
    # I have adjusted the view to show the user's name, not just their email, for clarity.
    dispatches = list(db.slips.find({'slip_type': 'dispatch'}).sort('created_at', -1))
    return render_template('dispatch_viewer.html', dispatches=dispatches)