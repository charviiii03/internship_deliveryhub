from flask_mail import Mail, Message

mail = Mail()


def send_application_credentials(
        app,
        recipient_email,
        application_id,
        application_token,
        expiry_date):

    with app.app_context():

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