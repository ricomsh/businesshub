# FILE: app/qc_module/routes.py

import os
import datetime
import traceback
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.decorators import role_required
from app.email import send_qc_submission_email  # Make sure this import is correct
import json

qc_bp = Blueprint('qc', __name__, template_folder='templates', url_prefix='/qc')

def get_next_qc_slip_id():
    """Generates a new sequential QC Slip ID (e.g., QC-2025-0001)."""
    db = current_app.db
    # Atomically find and increment the counter for 'qc_slip_id'
    sequence_doc = db.counters.find_one_and_update(
        {'_id': 'qc_slip_id'},
        {'$inc': {'sequence_value': 1}},
        upsert=True,
        return_document=True
    )
    # The sequence value is the new, incremented number
    sequence = sequence_doc.get('sequence_value', 1)
    # Format the ID with the current year and the sequence number
    return f"QC-{datetime.datetime.now().year}-{sequence:04d}"

@qc_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'qc', 'sales') # Added sales for broader access if needed
def new_qc_slip():
    if request.method == 'POST':
        current_app.logger.info("=== QC SLIP CREATION STARTED ===")
        current_app.logger.info(f"Current user: {current_user.name} ({current_user.email})")
        
        db = current_app.db
        form_data = request.form
        order_number = form_data.get('order_number')

        current_app.logger.info(f"Form data keys: {list(form_data.keys())}")
        current_app.logger.info(f"Order number: {order_number}")

        if not order_number:
            flash('You must select an order number.', 'danger')
            return render_template('qc_form.html')

        # Find all line numbers that were selected via their checkbox
        line_numbers = {key.split('_')[-1] for key in form_data if key.startswith('line_checkbox_')}
        current_app.logger.info(f"Selected line numbers: {line_numbers}")
        
        if not line_numbers:
            flash('You must select at least one line item to action.', 'danger')
            return render_template('qc_form.html')

        slip_id = get_next_qc_slip_id()
        current_app.logger.info(f"Generated slip ID: {slip_id}")
        
        actioned_lines = []
        today_date_str = datetime.datetime.now().strftime('%Y-%m-%d')

        for line_num in line_numbers:
            current_app.logger.info(f"Processing line number: {line_num}")
            
            # Extract line data with logging
            line_data = {
                'lineNumber': line_num,
                'partId': form_data.get(f'partId_{line_num}'),
                'partDescription': form_data.get(f'partDescription_{line_num}'),
                'miscReference': form_data.get(f'miscReference_{line_num}'),
                'orderQty': form_data.get(f'orderQty_{line_num}'),
                'actionQty': form_data.get(f'actionQty_{line_num}'),
                'comment': form_data.get(f'comment_{line_num}'),
                'attachments': []
            }
            
            current_app.logger.info(f"Line {line_num} data: {json.dumps(line_data, default=str)}")

            # Handle file uploads for this specific line item
            files = request.files.getlist(f'photos_{line_num}')
            current_app.logger.info(f"Files for line {line_num}: {len(files) if files else 0}")
            
            if files and files[0].filename:
                # Create a dedicated directory for this slip's attachments
                upload_folder = os.path.join(current_app.root_path, '..', 'uploads', 'qc_slips', slip_id)
                os.makedirs(upload_folder, exist_ok=True)
                current_app.logger.info(f"Created upload folder: {upload_folder}")

                for index, file in enumerate(files):
                    if file:
                        original_filename = secure_filename(file.filename)
                        # Create the new filename based on your requested format
                        new_filename = f"{order_number}_{today_date_str}_L{line_num}_{index+1}_{original_filename}"
                        
                        file_path = os.path.join(upload_folder, new_filename)
                        file.save(file_path)
                        current_app.logger.info(f"Saved file: {new_filename}")
                        
                        # Store the relative path for future access
                        relative_path = os.path.join('uploads', 'qc_slips', slip_id, new_filename).replace('\\', '/')
                        line_data['attachments'].append(relative_path)
            
            actioned_lines.append(line_data)

        # Construct the final document to be saved in MongoDB
        slip_document = {
            'slip_id': slip_id,
            'slip_type': 'qc',
            'order_number': order_number,
            'coa_number': form_data.get('coa_number'),
            'qc_type': form_data.get('qc_type'),
            'production_manager_email': form_data.get('production_manager_email'),
            'dispatch_manager_email': form_data.get('dispatch_manager_email'),
            'status': 'Complete',
            'created_at': datetime.datetime.utcnow(),
            'created_by': current_user.name,  # This should match what the template expects
            'created_by_email': current_user.email,
            'actioned_lines': actioned_lines
        }

        current_app.logger.info(f"Final slip document: {json.dumps(slip_document, default=str, indent=2)}")

        # Save to database
        current_app.logger.info("Saving slip document to database...")
        result = db.slips.insert_one(slip_document)
        current_app.logger.info(f"Document saved with ID: {result.inserted_id}")
        
        # Send email notification with extensive logging
        current_app.logger.info("Attempting to send QC submission email...")
        current_app.logger.info(f"Email function available: {send_qc_submission_email}")
        
        try:
            email_result = send_qc_submission_email(slip_document)
            if email_result:
                current_app.logger.info("✅ Email sent successfully")
            else:
                current_app.logger.warning("⚠️ Email function returned False")
        except Exception as e:
            current_app.logger.error(f"❌ Exception occurred while sending email: {str(e)}")
            current_app.logger.error(f"Email exception traceback: {traceback.format_exc()}")

        flash(f'QC Slip {slip_id} created successfully!', 'success')
        current_app.logger.info("=== QC SLIP CREATION COMPLETED ===")
        return redirect(url_for('qc.view_qc_slips'))

    return render_template('qc_form.html')

@qc_bp.route('/view')
@login_required
@role_required('admin', 'qc', 'sales', 'ir', 'dispatch')
def view_qc_slips():
    """Renders the page that displays all submitted QC slips."""
    db = current_app.db
    qc_slips = list(db.slips.find({'slip_type': 'qc'}).sort('created_at', -1))
    return render_template('qc_viewer.html', slips=qc_slips)

# Add a test route to verify email functionality
@qc_bp.route('/test-email')
@login_required
@role_required('admin')
def test_email():
    """Test route to verify email functionality"""
    current_app.logger.info("Manual email test triggered")
    
    try:
        from app.email import send_test_qc_email
        result = send_test_qc_email()
        if result:
            flash('Test email sent successfully! Check your inbox.', 'success')
        else:
            flash('Test email failed. Check the logs.', 'danger')
    except Exception as e:
        current_app.logger.error(f"Test email exception: {str(e)}")
        flash(f'Test email error: {str(e)}', 'danger')
    
    return redirect(url_for('qc.view_qc_slips'))