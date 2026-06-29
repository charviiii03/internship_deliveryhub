# notifications.py
# Handles all email notifications sent by App Manager

import os
from flask_mail import Mail, Message
from flask import render_template

mail = Mail()

# Company config loaded from environment variables
COMPANY_NAME    = os.getenv("COMPANY_NAME")
COMPANY_WEBSITE = os.getenv("COMPANY_WEBSITE")
COMPANY_PHONE   = os.getenv("COMPANY_PHONE")
SUPPORT_EMAIL   = os.getenv("SUPPORT_EMAIL")


# --------------------------------------------------
# GENERIC EMAIL SENDER
# --------------------------------------------------
def send_email(app, recipient_email, subject, template_name, context):

    with app.app_context():

        email_body = render_template(
            f"email_templates/{template_name}",
            **context
        )

        msg = Message(
            subject=subject,
            sender=app.config["MAIL_USERNAME"],
            recipients=[recipient_email]
        )
        msg.body = email_body

        try:
            mail.send(msg)
            print(f"EMAIL SENT SUCCESSFULLY TO: {recipient_email}")
        except Exception as e:
            print(f"EMAIL FAILED: {e}")


# --------------------------------------------------
# ONBOARDING EMAIL
# Sent after a new application is created
# --------------------------------------------------
def send_onboarding_email(app, recipient_email, application_id, application_token, expiry_date):

    send_email(
        app,
        recipient_email,
        "DeliveryHub Application Credentials",
        "onboarding_email.md",
        {
            "customer_name":    recipient_email,
            "application_name": COMPANY_NAME,
            "application_id":   application_id,
            "access_token":     application_token,
            "expiration_date":  expiry_date,
            "portal_url":       COMPANY_WEBSITE,
            "support_email":    SUPPORT_EMAIL,
            "support_phone":    COMPANY_PHONE,
            "company_website":  COMPANY_WEBSITE,
            "company_name":     COMPANY_NAME,
            "sender_name":      "DeliveryHub Team",
            "sender_title":     "Application Support",
        }
    )


# --------------------------------------------------
# RENEWAL EMAIL
# Sent when an application's expiry date is extended
# --------------------------------------------------
def send_renewal_email(app, recipient_email, application_id, expiry_date):

    send_email(
        app,
        recipient_email,
        "DeliveryHub Application Renewal",
        "renewal_email.md",
        {
            "customer_name":   recipient_email,
            "application_name": COMPANY_NAME,
            "application_id":  application_id,
            "expiration_date": expiry_date,
            "support_email":   SUPPORT_EMAIL,
            "support_phone":   COMPANY_PHONE,
            "company_name":    COMPANY_NAME,
            "company_website": COMPANY_WEBSITE,
            "sender_name":     "DeliveryHub Team",
        }
    )


# --------------------------------------------------
# INACTIVE EMAIL
# Sent when an application is disabled
# --------------------------------------------------
def send_inactive_email(app, recipient_email, application_id):

    send_email(
        app,
        recipient_email,
        "DeliveryHub Application Inactive",
        "inactive_email.md",
        {
            "customer_name":   recipient_email,
            "application_name": COMPANY_NAME,
            "application_id":  application_id,
            "inactive_reason": "No inquiries or business activity detected in the last 30 days",
            "support_email":   SUPPORT_EMAIL,
            "support_phone":   COMPANY_PHONE,
            "company_name":    COMPANY_NAME,
            "company_website": COMPANY_WEBSITE,
        }
    )


# --------------------------------------------------
# BUSINESS REPORT EMAIL
# Sent to management with a summary report
# FIX: was incorrectly reading from app.config — now
#      uses module-level os.getenv() variables
# --------------------------------------------------
def send_report_email(app, recipient_email, total_enquiries, successful_customers, revenue, report_date):

    conversion_rate = 0
    if total_enquiries > 0:
        conversion_rate = round((successful_customers / total_enquiries) * 100, 2)

    average_revenue = 0
    if successful_customers > 0:
        average_revenue = round(revenue / successful_customers, 2)

    send_email(
        app,
        recipient_email,
        "DeliveryHub Business Report",
        "business_report_email.md",
        {
            "report_date":           report_date,
            "total_enquiries":       total_enquiries,
            "successful_customers":  successful_customers,
            "conversion_rate":       conversion_rate,
            "revenue":               revenue,
            "average_revenue":       average_revenue,
            # FIX: use module-level env vars, not app.config
            "company_website":       COMPANY_WEBSITE,
            "company_name":          COMPANY_NAME,
            "sender_name":           "DeliveryHub Team",
        }
    )


# --------------------------------------------------
# SHIPMENT LABEL EMAIL
# Sends PDF label to receiver
# --------------------------------------------------
def send_label_notification(app, recipient_email, shipment_id, label_file_path):

    with app.app_context():

        msg = Message(
            subject="DeliveryHub Shipment Label",
            sender=app.config["MAIL_USERNAME"],
            recipients=[recipient_email]
        )

        msg.body = (
            f"Hello,\n\n"
            f"Your shipment label is ready.\n\n"
            f"Shipment ID: {shipment_id}\n\n"
            f"The PDF label is attached to this email.\n\n"
            f"Regards,\nDeliveryHub Team"
        )

        with app.open_resource(label_file_path) as fp:
            msg.attach(
                filename="shipment_label.pdf",
                content_type="application/pdf",
                data=fp.read()
            )

        mail.send(msg)


# --------------------------------------------------
# SHIPMENT CONFIRMATION EMAIL
# Sent to the customer who created the shipment
# --------------------------------------------------
def send_shipment_confirmation_email(app, recipient_email, shipment_id, requestid, service, sender_name, receiver_name):

    with app.app_context():

        msg = Message(
            subject="DeliveryHub — Shipment Created Successfully",
            sender=app.config["MAIL_USERNAME"],
            recipients=[recipient_email]
        )

        msg.body = (
            f"Hello,\n\n"
            f"Your shipment request has been successfully created.\n\n"
            f"Shipment ID : {shipment_id}\n"
            f"Request ID  : {requestid}\n"
            f"Service     : {service}\n"
            f"Sender      : {sender_name}\n"
            f"Receiver    : {receiver_name}\n\n"
            f"Our team will process your shipment and upload the label shortly.\n\n"
            f"Regards,\nDeliveryHub Team"
        )

        try:
            mail.send(msg)
            print(f"SHIPMENT CONFIRMATION SENT TO: {recipient_email}")
        except Exception as e:
            print(f"SHIPMENT CONFIRMATION EMAIL FAILED: {e}")
