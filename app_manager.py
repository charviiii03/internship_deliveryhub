# generates unique ids
import uuid

# -----------------------------
# EMAIL NOTIFICATION MODULE
# -----------------------------
# Used to send application
# credentials to applicants

from notifications import (
    mail,
    send_onboarding_email,
    send_renewal_email,
    send_inactive_email
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

from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    send_file
)

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
        send_onboarding_email(
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

    cursor = connection.cursor(
        dictionary=True
    )

    # Fetch application details
    # for notification email

    cursor.execute("""
        SELECT
            user_email
        FROM applications
        WHERE application_id = %s
    """, (
        application_id,
    ))

    application = cursor.fetchone()

    cursor.execute("""
        UPDATE applications
        SET is_active = %s
        WHERE application_id = %s
    """, (
        is_active,
        application_id
    ))

    connection.commit()

    # Send inactive notification
    # only when application
    # is disabled

    if (
        application
        and not is_active
    ):

        try:

            send_inactive_email(
                app,
                application["user_email"],
                application_id
            )

        except Exception as e:

            print(
                "Inactive email failed:",
                e
            )

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
    ).strip()

    new_expiry_date = data.get(
        "expiry_date"
    )

    connection = get_db_connection()

    if not connection:

        return jsonify({
            "status": "error",
            "reason": "database unavailable"
        }), 500

    cursor = connection.cursor(
        dictionary=True
    )

    # Fetch application details
    # for renewal notification

    cursor.execute("""
        SELECT
            user_email
        FROM applications
        WHERE application_id = %s
    """, (
        application_id,
    ))

    application = cursor.fetchone()

    cursor.execute("""
        UPDATE applications
        SET expiry_date = %s
        WHERE application_id = %s
    """, (
        new_expiry_date,
        application_id
    ))

    connection.commit()

    # Send renewal email

    if application:
        print("APPLICATION =", application)
        print("APPLICATION TYPE =", type(application))

        try:
            print("ATTEMPTING TO SEND RENEWAL EMAIL")

            send_renewal_email(
                app,
                application["user_email"],
                application_id,
                new_expiry_date
            )

        except Exception as e:

            print(
                "Renewal email failed:",
                e
            )

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
        send_onboarding_email(
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
@app.route("/admin-ui/customer/<int:customer_id>")
def get_customer(customer_id):

    connection = get_db_connection()

    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            customer_id,
            full_name,
            email,
            phone_number
        FROM customers
        WHERE customer_id = %s
    """, (customer_id,))

    customer = cursor.fetchone()

    cursor.close()
    connection.close()

    if customer:
        return jsonify(customer)

    return jsonify({
        "error": "Customer not found"
    }), 404

@app.route("/admin-ui/create-shipment", methods=["GET", "POST"])
def admin_ui_create_shipment():

    if request.method == "GET":
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, application_name
            FROM applications
            WHERE is_active = TRUE
            ORDER BY application_name
        """)

        applications = cursor.fetchall()
        print(applications)
        cursor.execute("""
            SELECT
                customer_id,
                full_name,
                email,
                phone_number
            FROM customers
            ORDER BY full_name
        """)

        customers = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "create_shipment.html",
            applications=applications,
            customers=customers
        )
        

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
    application_id = request.form.get("application_id")

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
           address_line1,
            address_line2,
            city,
            state_name,
            country,
            country_code,
            postal_code
        )
        VALUES (%s, %s, %s, %s, %s, %s,%s)
    """, (
        from_address,
        None,
        from_city,
        from_state,
        from_country,
        from_country_code,
        from_postal_code
    ))

    from_address_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO addresses(
            address_line1,
            address_line2,
            city,
            state_name,
            country,
            country_code,
            postal_code
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        to_address,
        None,
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
            application_id,
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
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
    """, (
        requestid,
        application_id,
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


@app.route("/admin-ui/view-label/<int:shipment_id>")
def view_label(shipment_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT file_path, file_name
        FROM shipment_labels
        WHERE shipment_id = %s
        ORDER BY label_id DESC
        LIMIT 1
    """, (shipment_id,))

    label = cursor.fetchone()

    cursor.close()
    connection.close()

    if not label:
        return "No label uploaded for this shipment"

    file_path = label["file_path"]

    if not os.path.exists(file_path):
        return "Label file not found on server"

    return send_file(
        file_path,
        mimetype="application/pdf",
        as_attachment=False
    )

@app.route("/admin-ui/create-shipment-from-text", methods=["GET", "POST"])
def create_shipment_from_text():

    if request.method == "GET":
        return render_template("create_shipment_from_text.html")

    import re

    shipment_text = request.form.get("shipment_text")
    service = request.form.get("service")

    if not shipment_text:
        return "Shipment text is required"

    try:
        sender_part = shipment_text.split("Receiver:")[0].replace("Sender:", "").strip()
        receiver_part = shipment_text.split("Receiver:")[1].strip()

        def extract_details(part):
            lines = [line.strip() for line in part.split("\n") if line.strip()]

            name = lines[0]

            phone_match = re.search(r"Ph:\s*(\+\d+)\s*(\d+)", part)
            phone_code = phone_match.group(1)
            phone = phone_match.group(2)

            email_match = re.search(
                r"(?:gmail|email|mail)\s*:\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})",
                part,
                re.IGNORECASE
            )

            email = email_match.group(1) if email_match else None

            postal_match = re.search(r"\b(\d{5,6})\b", part)
            postal_code = postal_match.group(1)

            address_lines = []
            for line in lines[1:]:
                if not line.lower().startswith("ph:") and not line.lower().startswith(("gmail:", "email:", "mail:")):
                    address_lines.append(line)

            full_address = ", ".join(address_lines)

            if phone_code == "+1":
                country = "USA"
                country_code = "US"
            elif phone_code == "+91":
                country = "India"
                country_code = "IN"
            else:
                country = ""
                country_code = ""

            city = ""
            state = ""

            if country == "USA":
                for line in address_lines:
                    if postal_code in line:
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 2:
                            city = parts[0]
                            state = parts[1]

            if country == "India":
                for line in address_lines:
                    if postal_code in line:
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 2:
                            state = parts[-3] if len(parts) >= 3 else ""
                            city = parts[-2]

            return {
                "name": name,
                "email": email,
                "phone_code": phone_code,
                "phone": phone,
                "address1": full_address,
                "address2": "",
                "city": city,
                "state": state,
                "country": country,
                "country_code": country_code,
                "postal_code": postal_code
            }

        sender = extract_details(sender_part)
        receiver = extract_details(receiver_part)

        sender_email = sender["email"] or f"sender_{uuid.uuid4().hex[:8]}@example.com"
        receiver_email = receiver["email"] or f"receiver_{uuid.uuid4().hex[:8]}@example.com"

        requestid = str(uuid.uuid4())

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO customers(full_name, phone_number, email)
            VALUES (%s, %s, %s)
        """, (
            sender["name"],
            sender["phone_code"] + " " + sender["phone"],
            sender_email
        ))

        sender_customer_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO customers(full_name, phone_number, email)
            VALUES (%s, %s, %s)
        """, (
            receiver["name"],
            receiver["phone_code"] + " " + receiver["phone"],
            receiver_email
        ))

        receiver_customer_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO addresses(
                address_line1,
                address_line2,
                city,
                state_name,
                country,
                country_code,
                postal_code
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            sender["address1"],
            sender["address2"],
            sender["city"],
            sender["state"],
            sender["country"],
            sender["country_code"],
            sender["postal_code"]
        ))

        from_address_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO addresses(
                address_line1,
                address_line2,
                city,
                state_name,
                country,
                country_code,
                postal_code
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            receiver["address1"],
            receiver["address2"],
            receiver["city"],
            receiver["state"],
            receiver["country"],
            receiver["country_code"],
            receiver["postal_code"]
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
            "Created from text message",
            "initiated",
            200
        ))

        shipment_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO shipment_tracking(shipment_id, current_status)
            VALUES (%s, %s)
        """, (
            shipment_id,
            "initiated"
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return admin_ui_shipments()

    except Exception as e:
        return f"Could not create shipment from text: {str(e)}"
    
@app.route("/admin-ui/edit-shipment/<int:shipment_id>", methods=["GET", "POST"])
def edit_shipment(shipment_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == "GET":
        cursor.execute("""
            SELECT
                s.shipment_id,
                sender.customer_id AS sender_customer_id,
                sender.full_name AS sender_name,
                sender.email AS sender_email,
                sender.phone_number AS sender_phone,
                receiver.customer_id AS receiver_customer_id,
                receiver.full_name AS receiver_name,
                receiver.email AS receiver_email,
                receiver.phone_number AS receiver_phone,
                s.service
            FROM shipments s
            JOIN customers sender ON s.sender_customer_id = sender.customer_id
            JOIN customers receiver ON s.receiver_customer_id = receiver.customer_id
            WHERE s.shipment_id = %s
        """, (shipment_id,))

        shipment = cursor.fetchone()

        cursor.close()
        connection.close()

        if not shipment:
            return "Shipment not found"

        return render_template("edit_shipment.html", shipment=shipment)

    sender_name = request.form.get("sender_name")
    sender_email = request.form.get("sender_email")
    sender_phone = request.form.get("sender_phone")

    receiver_name = request.form.get("receiver_name")
    receiver_email = request.form.get("receiver_email")
    receiver_phone = request.form.get("receiver_phone")

    service = request.form.get("service")

    try:
        cursor.execute("""
            SELECT sender_customer_id, receiver_customer_id
            FROM shipments
            WHERE shipment_id = %s
        """, (shipment_id,))

        ids = cursor.fetchone()

        cursor.execute("""
            UPDATE customers
            SET full_name = %s, email = %s, phone_number = %s
            WHERE customer_id = %s
        """, (sender_name, sender_email, sender_phone, ids["sender_customer_id"]))

        cursor.execute("""
            UPDATE customers
            SET full_name = %s, email = %s, phone_number = %s
            WHERE customer_id = %s
        """, (receiver_name, receiver_email, receiver_phone, ids["receiver_customer_id"]))

        cursor.execute("""
            UPDATE shipments
            SET service = %s
            WHERE shipment_id = %s
        """, (service, shipment_id))

        connection.commit()

    except Exception as e:
        connection.rollback()
        return f"Shipment update failed: {str(e)}"

    finally:
        cursor.close()
        connection.close()

    return admin_ui_shipments()

@app.route("/admin-ui/delete-shipment/<int:shipment_id>", methods=["POST"])
def delete_shipment(shipment_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Delete uploaded label records first
        cursor.execute("""
            DELETE FROM shipment_labels
            WHERE shipment_id = %s
        """, (shipment_id,))

        # Delete tracking records
        cursor.execute("""
            DELETE FROM shipment_tracking
            WHERE shipment_id = %s
        """, (shipment_id,))

        # Get related customer/address ids
        cursor.execute("""
            SELECT
                sender_customer_id,
                receiver_customer_id,
                from_address_id,
                to_address_id
            FROM shipments
            WHERE shipment_id = %s
        """, (shipment_id,))

        shipment = cursor.fetchone()

        if not shipment:
            return "Shipment not found"

        # Delete shipment
        cursor.execute("""
            DELETE FROM shipments
            WHERE shipment_id = %s
        """, (shipment_id,))

        # Delete related addresses
        cursor.execute("""
            DELETE FROM addresses
            WHERE address_id IN (%s, %s)
        """, (
            shipment["from_address_id"],
            shipment["to_address_id"]
        ))

        # Delete related customers
        cursor.execute("""
            DELETE FROM customers
            WHERE customer_id IN (%s, %s)
        """, (
            shipment["sender_customer_id"],
            shipment["receiver_customer_id"]
        ))

        connection.commit()

    except Exception as e:
        connection.rollback()
        return f"Shipment deletion failed: {str(e)}"

    finally:
        cursor.close()
        connection.close()

    return admin_ui_shipments()

# -----------------------------
# RUN APP MANAGER
# -----------------------------
if __name__ == "__main__":
    app.run(
        debug=True,
        port=5001
    )