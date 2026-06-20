# -----------------------------
# EMAIL SERVICE
# -----------------------------
# Handles email notifications
# sent by App Manager


from flask_mail import Mail, Message

mail = Mail()

# -----------------------------
# SEND APPLICATION EMAIL
# -----------------------------
# Sends application credentials
# to the email provided by admin
# during application onboarding

def send_application_credentials(
        app,
        recipient_email,
        application_id,
        application_token,
        expiry_date):

    with app.app_context():
        
        # Create email message
        # containing application details

        msg = Message(
            subject="DeliveryHub Application Credentials",
            sender=app.config["MAIL_USERNAME"],
            recipients=[recipient_email]
        )

        msg.body = f"""
Hello,

Your application has been created.

Application ID:
{application_id}

Application Token:
{application_token}

Expiry Date:
{expiry_date}

Regards,
DeliveryHub Team
"""

        mail.send(msg)


def send_label_notification(
        app,
        recipient_email,
        shipment_id,
        label_file_path):

    with app.app_context():

        msg = Message(
            subject="DeliveryHub Shipment Label",
            sender=app.config["MAIL_USERNAME"],
            recipients=[recipient_email]
        )

        msg.body = f"""
Hello,

Your shipment label is ready.

Shipment ID:
{shipment_id}

The PDF label is attached with this email.

Regards,
DeliveryHub Team
"""

        with app.open_resource(label_file_path) as fp:
            msg.attach(
                filename="shipment_label.pdf",
                content_type="application/pdf",
                data=fp.read()
            )

        mail.send(msg)