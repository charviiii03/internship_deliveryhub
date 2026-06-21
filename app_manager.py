# generates unique ids
import uuid

# -----------------------------
# EMAIL NOTIFICATION MODULE
# -----------------------------
# Used to send application
# credentials to applicants

from notifications import (
    mail,
    send_application_credentials
)
import os

from dotenv import load_dotenv

# generates secure random tokens
import secrets

# used for date and time operations
from datetime import datetime, timedelta

# used to hash passwords/tokens securely
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from werkzeug.utils import secure_filename
from notifications import send_label_notification
from notifications import (
    mail,
    send_application_credentials,
    send_label_notification
)

from flask import Flask, request, jsonify, render_template
from db import get_db_connection

app = Flask(__name__)
# -----------------------------
# EMAIL CONFIGURATION
# -----------------------------
# Load environment variables
# from .env file

load_dotenv()

# Configure SMTP settings
# used for sending emails
# Email configuration

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True

# Sender email credentials
# are stored in .env file

app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

# Initialize Flask-Mail

mail.init_app(app)

# -----------------------------
# AUTHENTICATION LOGGING
# -----------------------------
def log_auth_attempt(
    application_id,
    endpoint,
    status,
    reason=None,
    ip_address=None,
    request_details=None
):

    connection = get_db_connection()

    if not connection:
        return

    cursor = connection.cursor()

    sql = """
    INSERT INTO authentication_logs
    (
        application_id,
        endpoint,
        status,
        reason,
        ip_address,
        request_details
    )
    VALUES (%s,%s,%s,%s,%s,%s)
    """

    cursor.execute(sql, (
        application_id,
        endpoint,
        status,
        reason,
        ip_address,
        request_details
    ))

    connection.commit()

    cursor.close()
    connection.close()


# -----------------------------
# COMMON AUTH VALIDATION
# -----------------------------
def check_application_auth(
    application_id,
    application_token,
    endpoint
):

    ip_address = request.remote_addr
    request_details = (
        f"method={request.method}, path={request.path}"
    )

    if not application_id or not application_token:

        log_auth_attempt(
            application_id or "unknown",
            endpoint,
            "failure",
            "application id or token missing",
            ip_address,
            request_details
        )

        return None

    connection = get_db_connection()

    if not connection:
        return None

    cursor = connection.cursor(dictionary=True)

    sql = """
    SELECT *
    FROM applications
    WHERE application_id = %s
      AND expiry_date >= CURDATE()
      AND is_active = TRUE
    """

    cursor.execute(sql, (application_id,))
    application = cursor.fetchone()

    cursor.close()
    connection.close()

    if not application:

        log_auth_attempt(
            application_id,
            endpoint,
            "failure",
            "application not found, expired, or inactive",
            ip_address,
            request_details
        )

        return None

    if not check_password_hash(
        application["application_token"],
        application_token
    ):

        log_auth_attempt(
            application_id,
            endpoint,
            "failure",
            "invalid token",
            ip_address,
            request_details
        )

        return None

    log_auth_attempt(
        application_id,
        endpoint,
        "success",
        None,
        ip_address,
        request_details
    )

    return application


# -----------------------------
# VALIDATE AUTH API
# -----------------------------
@app.route("/validate-auth", methods=["POST"])
def validate_auth():

    data = request.get_json()

    application_id = (
        data.get("application_id")
        if data else None
    )

    application_token = (
        data.get("application_token")
        if data else None
    )

    application = check_application_auth(
        application_id,
        application_token,
        "/validate-auth"
    )

    if application:

        return jsonify({
            "status": "valid",
            "message": "valid application"
        }), 200

    return jsonify({
        "status": "invalid",
        "reason": "invalid or expired application"
    }), 401


# -----------------------------
# ADMIN CREATE APPLICATION
# -----------------------------
@app.route(
    "/admin/create-application",
    methods=["POST"]
)
def signup():

    data = request.get_json()

    application_name = data.get(
        "application_name"
    )

    user_email = data.get(
        "user_email"
    )

    application_id = str(
        uuid.uuid4()
    )

    application_token = (
        secrets.token_urlsafe(32)
    )

    hashed_token = (
        generate_password_hash(
            application_token
        )
    )

    expiry_date = (
        datetime.now() +
        timedelta(days=90)
    )

    connection = get_db_connection()

    if not connection:

        return jsonify({
            "status": "error",
            "reason": "database unavailable"
        }), 500

    cursor = connection.cursor()

    sql = """
    INSERT INTO applications
    (
        application_id,
        application_token,
        application_name,
        user_email,
        expiry_date
    )
    VALUES (%s,%s,%s,%s,%s)
    """

    cursor.execute(sql, (
        application_id,
        hashed_token,
        application_name,
        user_email,
        expiry_date
    ))

    connection.commit()

    # -----------------------------
    # SEND APPLICATION CREDENTIALS
    # -----------------------------
    # After successful application
    # creation, send generated
    # credentials to applicant email

    try:
        send_application_credentials(
        app,
        user_email,
        application_id,
        application_token,
        expiry_date.strftime("%Y-%m-%d")
    )
    except Exception as e:

    # Application creation should
    # continue even if email fails

        print("Email sending failed:", e)

    cursor.close()
    connection.close()

    return jsonify({
        "status": "success",
        "message": "application created successfully",
        "application_id": application_id,
        "application_token": application_token,
        "expiry_date": expiry_date.strftime(
            "%Y-%m-%d"
        )
    }), 201


# -----------------------------
# VIEW APPLICATIONS
# -----------------------------
@app.route(
    "/admin/applications",
    methods=["GET"]
)
def view_applications():

    connection = get_db_connection()

    if not connection:

        return jsonify({
            "status": "error",
            "reason": "database unavailable"
        }), 500

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT
            application_id,
            application_name,
            user_email,
            expiry_date,
            is_active
        FROM applications
    """)

    applications = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({
        "status": "success",
        "applications": applications
    }), 200


# -----------------------------
# UPDATE APPLICATION STATUS
# -----------------------------
@app.route(
    "/admin/update-status",
    methods=["PUT"]
)
def update_status():

    data = request.get_json()

    application_id = data.get(
        "application_id"
    )

    is_active = data.get(
        "is_active"
    )

    connection = get_db_connection()

    if not connection:

        return jsonify({
            "status": "error",
            "reason": "database unavailable"
        }), 500

    cursor = connection.cursor()

    cursor.execute("""
        UPDATE applications
        SET is_active = %s
        WHERE application_id = %s
    """, (
        is_active,
        application_id
    ))

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({
        "status": "success",
        "message": "application status updated"
    }), 200


# -----------------------------
# UPDATE EXPIRY DATE
# -----------------------------
@app.route(
    "/admin/update-expiry",
    methods=["PUT"]
)
def update_expiry():

    data = request.get_json()

    application_id = data.get(
        "application_id"
    )

    new_expiry_date = data.get(
        "expiry_date"
    )

    connection = get_db_connection()

    if not connection:

        return jsonify({
            "status": "error",
            "reason": "database unavailable"
        }), 500

    cursor = connection.cursor()

    cursor.execute("""
        UPDATE applications
        SET expiry_date = %s
        WHERE application_id = %s
    """, (
        new_expiry_date,
        application_id
    ))

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({
        "status": "success",
        "message": "expiry date updated"
    }), 200


# -----------------------------
# VIEW AUTH LOGS
# -----------------------------
@app.route(
    "/admin/auth-logs",
    methods=["GET"]
)
def view_auth_logs():

    connection = get_db_connection()

    if not connection:

        return jsonify({
            "status": "error",
            "reason": "database unavailable"
        }), 500

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute("""
        SELECT
            application_id,
            endpoint,
            request_time,
            status,
            reason,
            ip_address,
            request_details
        FROM authentication_logs
        ORDER BY request_time DESC
    """)

    logs = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({
        "status": "success",
        "logs": logs
    }), 200


# -----------------------------
# SIGNIN API
# -----------------------------
@app.route("/signin", methods=["POST"])
def signin():

    data = request.get_json()

    application_id = data.get(
        "application_id"
    )

    application_token = data.get(
        "application_token"
    )

    application = check_application_auth(
        application_id,
        application_token,
        "/signin"
    )

    if not application:

        return jsonify({
            "status": "invalid",
            "reason": "application not found, expired, inactive, or token invalid"
        }), 401

    return jsonify({
        "status": "valid",
        "message": "signin successful"
    }), 200

# -----------------------------
# ADMIN DASHBOARD UI
# -----------------------------

@app.route("/admin-ui")
def admin_dashboard():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS count FROM applications")
    total_applications = cursor.fetchone()["count"]

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM authentication_logs
        WHERE status = 'success'
    """)
    valid_auth = cursor.fetchone()["count"]

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM authentication_logs
        WHERE status = 'failure'
    """)
    invalid_auth = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) AS count FROM shipments")
    total_shipments = cursor.fetchone()["count"]

    cursor.close()
    connection.close()

    return render_template(
        "admin_dashboard.html",
        total_applications=total_applications,
        valid_auth=valid_auth,
        invalid_auth=invalid_auth,
        total_shipments=total_shipments
    )

# -------------------------------
# CREATE-APPLICATIONS - ADMIN UI 
# -------------------------------

@app.route("/admin-ui/create-application", methods=["GET", "POST"])
def admin_ui_create_application():

    if request.method == "GET":
        return render_template("create_application.html")

    application_name = request.form.get("application_name")
    user_email = request.form.get("user_email")

    application_id = str(uuid.uuid4())
    application_token = secrets.token_urlsafe(32)
    hashed_token = generate_password_hash(application_token)
    expiry_date = datetime.now() + timedelta(days=90)

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO applications
        (application_id, application_token, application_name, user_email, expiry_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        application_id,
        hashed_token,
        application_name,
        user_email,
        expiry_date
    ))

    connection.commit()

    try:
        send_application_credentials(
            app,
            user_email,
            application_id,
            application_token,
            expiry_date.strftime("%Y-%m-%d")
        )
    except Exception as e:
        print("Email sending failed:", e)

    cursor.close()
    connection.close()

    return f"""
    <h1>Application Created Successfully</h1>
    <p><b>Application ID:</b> {application_id}</p>
    <p><b>Application Token:</b> {application_token}</p>
    <p><b>Expiry Date:</b> {expiry_date.strftime("%Y-%m-%d")}</p>
    <a href="/admin-ui">Back to Dashboard</a>
    """

# -----------------------------
# AUTHENTICATION LOGS - ADMIN UI
# -----------------------------

@app.route("/admin-ui/auth-logs")
def admin_ui_auth_logs():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT application_id, endpoint, request_time, status, reason, ip_address
        FROM authentication_logs
        ORDER BY request_time DESC
    """)

    logs = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "auth_logs.html",
        logs=logs
    )

@app.route("/admin-ui/update-status", methods=["POST"])
def admin_ui_update_status():

    application_id = request.form.get("application_id")
    is_active = request.form.get("is_active") == "true"

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE applications
        SET is_active = %s
        WHERE application_id = %s
    """, (is_active, application_id))

    connection.commit()
    cursor.close()
    connection.close()

    return admin_ui_applications()


@app.route("/admin-ui/update-expiry", methods=["POST"])
def admin_ui_update_expiry():

    application_id = request.form.get("application_id")
    expiry_date = request.form.get("expiry_date")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE applications
        SET expiry_date = %s
        WHERE application_id = %s
    """, (expiry_date, application_id))

    connection.commit()
    cursor.close()
    connection.close()

    return admin_ui_applications()

@app.route("/admin-ui/shipments")
def admin_ui_shipments():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.shipment_id,
            s.requestid,
            s.service,
            s.validation_status,
            s.validation_reason,
            s.state,
            s.return_code,
            s.created_at,

            sender.full_name AS sender_name,
            sender.email AS sender_email,

            receiver.full_name AS receiver_name,
            receiver.email AS receiver_email,

            from_addr.country AS from_country,
            to_addr.country AS to_country,

            CASE
                WHEN sl.label_id IS NOT NULL THEN 'uploaded'
                ELSE 'pending'
            END AS label_status

        FROM shipments s

        JOIN customers sender
            ON s.sender_customer_id = sender.customer_id

        JOIN customers receiver
            ON s.receiver_customer_id = receiver.customer_id

        JOIN addresses from_addr
            ON s.from_address_id = from_addr.address_id

        JOIN addresses to_addr
            ON s.to_address_id = to_addr.address_id

        LEFT JOIN shipment_labels sl
            ON s.shipment_id = sl.shipment_id

        ORDER BY s.shipment_id DESC
    """)

    shipments = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "shipments.html",
        shipments=shipments
    )
@app.route("/admin-ui/upload-label", methods=["GET", "POST"])
def admin_ui_upload_label():

    if request.method == "GET":
        shipment_id = request.args.get("shipment_id")
        return render_template(
            "upload_label.html",
            shipment_id=shipment_id
        )

    shipment_id = request.form.get("shipment_id")
    label_file = request.files.get("label_file")

    if not shipment_id or not label_file:
        return "Shipment ID and PDF file are required"

    if not label_file.filename.lower().endswith(".pdf"):
        return "Only PDF files are allowed"

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT c.email
        FROM shipments s
        JOIN customers c
            ON s.receiver_customer_id = c.customer_id
        WHERE s.shipment_id = %s
    """, (shipment_id,))

    receiver = cursor.fetchone()

    if not receiver or not receiver[0]:
        cursor.close()
        connection.close()
        return "Receiver email not found for this shipment"

    customer_email = receiver[0]

    upload_folder = "uploads"
    os.makedirs(upload_folder, exist_ok=True)

    filename = secure_filename(label_file.filename)
    file_path = os.path.join(upload_folder, filename)

    label_file.save(file_path)

    cursor.execute("""
        INSERT INTO shipment_labels
        (shipment_id, file_name, file_path, emailed_to_customer)
        VALUES (%s, %s, %s, %s)
    """, (
        shipment_id,
        filename,
        file_path,
        False
    ))

    cursor.execute("""
        UPDATE shipments
        SET state = 'label_uploaded'
        WHERE shipment_id = %s
    """, (shipment_id,))

    connection.commit()

    try:
        send_label_notification(
            app,
            customer_email,
            shipment_id,
            file_path
        )

        cursor.execute("""
            UPDATE shipment_labels
            SET emailed_to_customer = TRUE
            WHERE shipment_id = %s
            ORDER BY label_id DESC
            LIMIT 1
        """, (shipment_id,))

        connection.commit()

    except Exception as e:
        print("Label email failed:", e)

    cursor.close()
    connection.close()

    return admin_ui_shipments()

@app.route("/admin-ui/create-shipment", methods=["GET", "POST"])
def admin_ui_create_shipment():

    if request.method == "GET":
        return render_template("create_shipment.html")

    sender_name = request.form.get("sender_name")
    sender_email = request.form.get("sender_email")
    sender_phone_code = request.form.get("sender_phone_code")
    sender_phone = request.form.get("sender_phone")

    receiver_name = request.form.get("receiver_name")
    receiver_email = request.form.get("receiver_email")
    receiver_phone_code = request.form.get("receiver_phone_code")
    receiver_phone = request.form.get("receiver_phone")

    from_address = request.form.get("from_address")
    from_city = request.form.get("from_city")
    from_state = request.form.get("from_state")
    from_country = request.form.get("from_country")
    from_country_code = request.form.get("from_country_code")
    from_postal_code = request.form.get("from_postal_code")

    to_address = request.form.get("to_address")
    to_city = request.form.get("to_city")
    to_state = request.form.get("to_state")
    to_country = request.form.get("to_country")
    to_country_code = request.form.get("to_country_code")
    to_postal_code = request.form.get("to_postal_code")

    service = request.form.get("service")

    def validate_country_rules(country, country_code, phone_code, phone_number, postal_code, user_type):

        if country == "India":

            if country_code != "IN":
                return f"{user_type} country code must be IN"

            if phone_code != "+91":
                return f"{user_type} India phone code must be +91"

            if not phone_number.isdigit() or len(phone_number) != 10:
                return f"{user_type} India phone number must be 10 digits"

            if not postal_code.isdigit() or len(postal_code) != 6:
                return f"{user_type} India postal code must be 6 digits"

        elif country == "USA":

            if country_code != "US":
                return f"{user_type} country code must be US"

            if phone_code != "+1":
                return f"{user_type} USA phone code must be +1"

            if not phone_number.isdigit() or len(phone_number) != 10:
                return f"{user_type} USA phone number must be 10 digits"

            if not postal_code.isdigit() or len(postal_code) != 5:
                return f"{user_type} USA postal code must be 5 digits"

        else:
            return f"{user_type} country must be either India or USA"

        return None

    sender_error = validate_country_rules(
        from_country,
        from_country_code,
        sender_phone_code,
        sender_phone,
        from_postal_code,
        "Sender"
    )

    if sender_error:
        return sender_error

    receiver_error = validate_country_rules(
        to_country,
        to_country_code,
        receiver_phone_code,
        receiver_phone,
        to_postal_code,
        "Receiver"
    )

    if receiver_error:
        return receiver_error

    requestid = str(uuid.uuid4())

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO customers(full_name, phone_number, email)
        VALUES (%s, %s, %s)
    """, (
        sender_name,
        sender_phone_code + " " + sender_phone,
        sender_email
    ))

    sender_customer_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO customers(full_name, phone_number, email)
        VALUES (%s, %s, %s)
    """, (
        receiver_name,
        receiver_phone_code + " " + receiver_phone,
        receiver_email
    ))

    receiver_customer_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO addresses(
            address_line,
            city,
            state,
            country,
            country_code,
            postal_code
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        from_address,
        from_city,
        from_state,
        from_country,
        from_country_code,
        from_postal_code
    ))

    from_address_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO addresses(
            address_line,
            city,
            state,
            country,
            country_code,
            postal_code
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        to_address,
        to_city,
        to_state,
        to_country,
        to_country_code,
        to_postal_code
    ))

    to_address_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO shipments(
            requestid,
            sender_customer_id,
            receiver_customer_id,
            from_address_id,
            to_address_id,
            service,
            validation_status,
            validation_reason,
            state,
            return_code
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        requestid,
        sender_customer_id,
        receiver_customer_id,
        from_address_id,
        to_address_id,
        service,
        "valid",
        "No issues",
        "initiated",
        200
    ))

    shipment_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO shipment_tracking(
            shipment_id,
            current_status
        )
        VALUES (%s, %s)
    """, (
        shipment_id,
        "initiated"
    ))

    connection.commit()

    cursor.close()
    connection.close()

    return admin_ui_shipments()
@app.route("/admin-ui/applications")
def admin_ui_applications():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            application_id,
            application_name,
            user_email,
            expiry_date,
            is_active
        FROM applications
        ORDER BY created_at DESC
    """)

    applications = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "applications.html",
        applications=applications
    )
# -----------------------------
# RUN APP MANAGER
# -----------------------------
if __name__ == "__main__":
    app.run(
        debug=True,
        port=5001
    )