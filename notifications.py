# -----------------------------
# EMAIL SERVICE
# -----------------------------
# Handles email notifications
# sent by App Manager


from flask_mail import Mail, Message
from flask import render_template

mail = Mail()


# -----------------------------
# GENERIC EMAIL SENDER
# -----------------------------
# Loads email template
# and sends email using
# Flask-Mail service

def send_email(
        app,
        recipient_email,
        subject,
        template_name,
        context):

    with app.app_context():

        # Load email template
        # and replace variables

        email_body = render_template(
            f"email_templates/{template_name}",
            **context
        )

        # Create email message

        msg = Message(
            subject=subject,
            sender=app.config["MAIL_USERNAME"],
            recipients=[recipient_email]
        )

        msg.body = email_body

        try:

            mail.send(msg)

            print(
                f"EMAIL SENT SUCCESSFULLY TO: {recipient_email}"
            )

        except Exception as e:

            print(
                f"EMAIL FAILED: {e}"
            )


# -----------------------------
# APPLICATION ONBOARDING EMAIL
# -----------------------------
# Sends application credentials
# after application creation

def send_onboarding_email(
        app,
        recipient_email,
        application_id,
        application_token,
        expiry_date):

    send_email(
        app,
        recipient_email,
        "ParcelMyBox Application Credentials",
        "onboarding_email.txt",
        {

            "customer_name":
            recipient_email,

            "application_name":
            "ParcelMyBox",

            "application_id":
            application_id,

            "access_token":
            application_token,

            "expiration_date":
            expiry_date,

            "portal_url":
            "https://parcelmybox.com",

            "support_email":
            "parcelmybox3@gmail.com",

            "support_phone":
            "+1 (209) 302-1767",

            "company_website":
            "https://parcelmybox.com",

            "company_name":
            "ParcelMyBox",

            "sender_name":
            "ParcelMyBox Team",

            "sender_title":
            "Application Support"
        }
    )


# -----------------------------
# APPLICATION RENEWAL EMAIL
# -----------------------------
# Sends notification when
# application expiry is extended

def send_renewal_email(
        app,
        recipient_email,
        application_id,
        expiry_date):

    send_email(
        app,
        recipient_email,
        "ParcelMyBox Application Renewal",
        "renewal_email.txt",
        {

            "customer_name":
            recipient_email,

            "application_id":
            application_id,

            "expiration_date":
            expiry_date,

            "company_name":
            "ParcelMyBox",

            "company_website":
            "https://parcelmybox.com",

            "sender_name":
            "ParcelMyBox Team"
        }
    )


# -----------------------------
# APPLICATION INACTIVE EMAIL
# -----------------------------
# Sends notification when
# application is disabled

def send_inactive_email(
        app,
        recipient_email,
        application_id):

    send_email(
        app,
        recipient_email,
        "ParcelMyBox Application Inactive",
        "inactive_email.txt",
        {

            "customer_name":
            recipient_email,

            "application_id":
            application_id,

            "support_email":
            "parcelmybox3@gmail.com",

            "company_name":
            "ParcelMyBox",

            "company_website":
            "https://parcelmybox.com"
        }
    )


# -----------------------------
# BUSINESS REPORT EMAIL
# -----------------------------
# Sends summary report
# to management team

def send_report_email(
        app,
        recipient_email,
        total_enquiries,
        successful_customers,
        revenue,
        report_date):

    send_email(
        app,
        recipient_email,
        "ParcelMyBox Business Report",
        "report_email.txt",
        {

            "total_enquiries":
            total_enquiries,

            "successful_customers":
            successful_customers,

            "revenue":
            revenue,

            "report_date":
            report_date,

            "company_name":
            "ParcelMyBox"
        }
    )
   