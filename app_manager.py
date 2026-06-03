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

app.config["MAIL_USERNAME"] = "parcelmybox3@gmail.com"
app.config["MAIL_PASSWORD"] = "knqx pquf jhap ncqi"

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
    return render_template("admin_dashboard.html")

# -------------------------------
# VIEW APPLICATIONS - ADMIN UI 
# -------------------------------

@app.route("/admin-ui/applications")
def admin_ui_applications():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT application_id, application_name, user_email, expiry_date, is_active
        FROM applications
    """)

    applications = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "applications.html",
        applications=applications
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
            shipment_id,
            requestid,
            service,
            validation_status,
            validation_reason,
            state,
            return_code
        FROM shipments
        ORDER BY shipment_id DESC
    """)

    shipments = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "shipments.html",
        shipments=shipments
    )

# -----------------------------
# RUN APP MANAGER
# -----------------------------
if __name__ == "__main__":
    app.run(
        debug=True,
        port=5001
    )