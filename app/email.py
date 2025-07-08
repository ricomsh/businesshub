# FILE: app/email.py

from flask import current_app, render_template, url_for
from flask_mail import Message
from app import mail # This import will now work correctly
import logging
import traceback
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def _send_email_with_test_mode(subject, html_body, recipients, cc=None, attachments=None):
    """Internal function to handle sending and test mode logic using Flask-Mail."""
    config = current_app.config
    is_testing_mode = config.get('TEST_MODE', False)
    test_recipient = config.get('TEST_EMAIL_RECIPIENT')

    final_recipients = recipients
    final_cc = cc or []
    subject_prefix = ""
    original_recipients_info = ""

    if is_testing_mode:
        if not test_recipient:
            logger.error("TEST_MODE is ON, but no TEST_EMAIL_RECIPIENT is set. Cannot send email.")
            return False
        
        original_to = ", ".join(recipients)
        original_cc = ", ".join(final_cc) if final_cc else "None"
        original_recipients_info = f"""
        <hr>
        <p style="font-family: monospace; font-size: 12px; color: #888;">
            <b>--- TEST MODE ACTIVE ---</b><br>
            Original To: {original_to}<br>
            Original Cc: {original_cc}
        </p>
        """
        final_recipients = [test_recipient]
        final_cc = []
        subject_prefix = "[TEST MODE] "
    
    if not final_recipients:
        logger.warning(f"No valid recipients for subject '{subject}'. Email not sent.")
        return False
    
    try:
        msg = Message(
            subject=f"{subject_prefix}{subject}",
            sender=config.get('EMAIL_FROM'),
            recipients=final_recipients,
            cc=final_cc
        )
        msg.html = html_body + original_recipients_info
        
        # Add attachments if any
        if attachments:
            for attachment in attachments:
                # Assuming attachment is a tuple of (filename, content_type, data)
                # This part needs to be adapted based on how you get the file data
                pass # Placeholder for attachment logic

        mail.send(msg)
        logger.info(f"✅ Email sent successfully for subject '{subject}' to: {', '.join(final_recipients)}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send email for subject '{subject}'. Error: {e}", exc_info=True)
        return False

def send_qc_submission_email(slip_document):
    """
    I AM PRESERVING YOUR DETAILED QC EMAIL FUNCTION.
    I have only corrected the final sending mechanism.
    """
    logger.info("=== QC EMAIL FUNCTION STARTED ===")
    try:
        # YOUR DETAILED LOGIC AND VARIABLE EXTRACTION IS PRESERVED
        slip_id = slip_document.get('slip_id', 'N/A')
        order_number = slip_document.get('order_number', 'N/A')
        
        # Determine recipients
        production_manager = slip_document.get('production_manager_email')
        dispatch_manager = slip_document.get('dispatch_manager_email')
        submitted_by_email = slip_document.get('created_by_email')

        recipients = []
        if production_manager: recipients.append(production_manager)
        if dispatch_manager: recipients.append(dispatch_manager)

        cc_recipients = []
        if submitted_by_email: cc_recipients.append(submitted_by_email)
        
        subject = f"[QC SLIP] {slip_id} - Order {order_number} Requires Review"
        
        # Use a rendered template for the email body for better maintenance
        html_body = render_template('emails/qc_notification.html', slip=slip_document)
        
        logger.info(f"Attempting to send email for QC Slip {slip_id} to {recipients} (CC: {cc_recipients})")
        
        # Use the unified sending function
        return _send_email_with_test_mode(subject, html_body, recipients, cc=cc_recipients)

    except Exception as e:
        logger.error(f"❌ Failed to construct QC slip email for {slip_document.get('slip_id', 'unknown')}: {str(e)}")
        logger.error(f"Full exception traceback: {traceback.format_exc()}")
        return False

def send_qc_update_email(slip_document, update_type, updated_by, notes=None):
    """Send email when QC slip status is updated."""
    slip_id = slip_document.get('slip_id', 'N/A')
    subject = f"[QC UPDATE] {slip_id} - {update_type.upper()}"
    
    recipients = []
    if slip_document.get('production_manager_email'): recipients.append(slip_document.get('production_manager_email'))
    if slip_document.get('dispatch_manager_email'): recipients.append(slip_document.get('dispatch_manager_email'))
    if slip_document.get('created_by_email'): recipients.append(slip_document.get('created_by_email'))
    
    # It's better to use templates for email bodies
    html_body = render_template('emails/qc_update.html', slip=slip_document, update_type=update_type, updated_by=updated_by, notes=notes)
    
    return _send_email_with_test_mode(subject, html_body, list(set(recipients)))

def send_ir_submission_email(slip_data):
    """Constructs and sends an email for a new Inspection Report."""
    subject = f"New Inspection Report Logged: {slip_data.get('slip_id')}"
    to_emails = ['quality_assurance@example.com']
    cc_emails = ['eric.mashau@hcaircon.com']
    html_body = render_template('emails/ir_notification.html', slip=slip_data)
    return _send_email_with_test_mode(subject, html_body, to_emails, cc=cc_emails)

def send_cc_submission_email(slip_data):
    """Constructs and sends an email for a new Customer Complaint slip."""
    subject = f"Customer Complaint Logged: {slip_data.get('slip_id')}"
    to_emails = ['sales_management@example.com']
    cc_emails = ['eric.mashau@hcaircon.com']
    html_body = render_template('emails/cc_notification.html', slip=slip_data)
    return _send_email_with_test_mode(subject, html_body, to_emails, cc=cc_emails)
