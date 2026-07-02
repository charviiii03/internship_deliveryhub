# app_manager.py
# Core admin backend — application management, auth, shipments, labels

import uuid
import os
import re
import secrets
from datetime import datetime, timedelta

import pdfplumber
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from db import get_db_connection
from notifications import (
    mail,
    send_onboarding_email,
    send_renewal_email,
    send_inactive_email,
    send_label_notification,
    send_shipment_confirmation_email,
)

load_dotenv()

app = Flask(__name__)

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
app.config["MAIL_SERVER"]   = "smtp.gmail.com"
app.config["MAIL_PORT"]     = 587
app.config["MAIL_USE_TLS"]  = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["UPLOAD_FOLDER"] = "uploads"

mail.init_app(app)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def log_auth_attempt(application_id, endpoint, status,
                     reason=None, ip_address=None, request_details=None):
    conn = get_db_connection()
    if not conn:
        return
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO authentication_logs
           (application_id, endpoint, status, reason, ip_address, request_details)
           VALUES (%s,%s,%s,%s,%s,%s)""",
        (application_id, endpoint, status, reason, ip_address, request_details)
    )
    conn.commit()
    cur.close()
    conn.close()


def check_application_auth(application_id, application_token, endpoint):
    ip_address      = request.remote_addr
    request_details = f"method={request.method}, path={request.path}"

    if not application_id or not application_token:
        log_auth_attempt(application_id or "unknown", endpoint, "failure",
                         "application id or token missing", ip_address, request_details)
        return None

    conn = get_db_connection()
    if not conn:
        return None

    cur = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT * FROM applications
           WHERE application_id = %s
             AND expiry_date >= CURDATE()
             AND is_active = TRUE""",
        (application_id,)
    )
    application = cur.fetchone()
    cur.close()
    conn.close()

    if not application:
        log_auth_attempt(application_id, endpoint, "failure",
                         "application not found, expired, or inactive", ip_address, request_details)
        return None

    if not check_password_hash(application["application_token"], application_token):
        log_auth_attempt(application_id, endpoint, "failure",
                         "invalid token", ip_address, request_details)
        return None

    log_auth_attempt(application_id, endpoint, "success",
                     None, ip_address, request_details)
    return application


# --------------------------------------------------
# JSON API — AUTH
# --------------------------------------------------

@app.route("/validate-auth", methods=["POST"])
def validate_auth():
    data              = request.get_json()
    application_id    = data.get("application_id")    if data else None
    application_token = data.get("application_token") if data else None

    application = check_application_auth(application_id, application_token, "/validate-auth")
    if application:
        return jsonify({"status": "valid", "message": "valid application"}), 200
    return jsonify({"status": "invalid", "reason": "invalid or expired application"}), 401


@app.route("/signin", methods=["POST"])
def signin():
    data              = request.get_json()
    application_id    = data.get("application_id")
    application_token = data.get("application_token")

    application = check_application_auth(application_id, application_token, "/signin")
    if not application:
        return jsonify({"status": "invalid",
                        "reason": "application not found, expired, inactive, or token invalid"}), 401
    return jsonify({"status": "valid", "message": "signin successful"}), 200


# --------------------------------------------------
# JSON API — APPLICATIONS
# --------------------------------------------------

@app.route("/admin/create-application", methods=["POST"])
def signup():
    data             = request.get_json()
    application_name = data.get("application_name")
    user_email       = data.get("user_email")

    application_id    = str(uuid.uuid4())
    application_token = secrets.token_urlsafe(32)
    hashed_token      = generate_password_hash(application_token)
    expiry_date       = datetime.now() + timedelta(days=90)

    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "reason": "database unavailable"}), 500

    cur = conn.cursor()
    cur.execute(
        """INSERT INTO applications
           (application_id, application_token, application_name, user_email, expiry_date)
           VALUES (%s,%s,%s,%s,%s)""",
        (application_id, hashed_token, application_name, user_email, expiry_date)
    )
    conn.commit()
    cur.close()
    conn.close()

    try:
        send_onboarding_email(app, user_email, application_id,
                              application_token, expiry_date.strftime("%Y-%m-%d"))
    except Exception as e:
        print("Email sending failed:", e)

    return jsonify({
        "status":            "success",
        "message":           "application created successfully",
        "application_id":    application_id,
        "application_token": application_token,
        "expiry_date":       expiry_date.strftime("%Y-%m-%d"),
    }), 201


@app.route("/admin/applications", methods=["GET"])
def view_applications():
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "reason": "database unavailable"}), 500
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT application_id, application_name, user_email, expiry_date, is_active FROM applications")
    applications = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({"status": "success", "applications": applications}), 200


@app.route("/admin/update-status", methods=["PUT"])
def update_status():
    data           = request.get_json()
    application_id = data.get("application_id")
    is_active      = data.get("is_active")

    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "reason": "database unavailable"}), 500

    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT user_email FROM applications WHERE application_id = %s", (application_id,))
    application = cur.fetchone()

    cur.execute("UPDATE applications SET is_active = %s WHERE application_id = %s",
                (is_active, application_id))
    conn.commit()

    if application and not is_active:
        try:
            send_inactive_email(app, application["user_email"], application_id)
        except Exception as e:
            print("Inactive email failed:", e)

    cur.close()
    conn.close()
    return jsonify({"status": "success", "message": "application status updated"}), 200


@app.route("/admin/update-expiry", methods=["PUT"])
def update_expiry():
    data            = request.get_json()
    application_id  = data.get("application_id").strip()
    new_expiry_date = data.get("expiry_date")

    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "reason": "database unavailable"}), 500

    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT user_email FROM applications WHERE application_id = %s", (application_id,))
    application = cur.fetchone()

    cur.execute("UPDATE applications SET expiry_date = %s WHERE application_id = %s",
                (new_expiry_date, application_id))
    conn.commit()

    if application:
        try:
            send_renewal_email(app, application["user_email"], application_id, new_expiry_date)
        except Exception as e:
            print("Renewal email failed:", e)

    cur.close()
    conn.close()
    return jsonify({"status": "success", "message": "expiry date updated"}), 200


@app.route("/admin/auth-logs", methods=["GET"])
def view_auth_logs():
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "reason": "database unavailable"}), 500
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT application_id, endpoint, request_time, status, reason,
                  ip_address, request_details
           FROM authentication_logs ORDER BY request_time DESC"""
    )
    logs = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({"status": "success", "logs": logs}), 200


# --------------------------------------------------
# ADMIN UI — DASHBOARD
# --------------------------------------------------

@app.route("/admin-ui")
def admin_dashboard():
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) AS count FROM applications")
    total_applications = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) AS count FROM authentication_logs WHERE status = 'success'")
    valid_auth = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) AS count FROM authentication_logs WHERE status = 'failure'")
    invalid_auth = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) AS count FROM shipments")
    total_shipments = cur.fetchone()["count"]

    cur.close()
    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_applications=total_applications,
        valid_auth=valid_auth,
        invalid_auth=invalid_auth,
        total_shipments=total_shipments,
    )


# --------------------------------------------------
# ADMIN UI — APPLICATIONS
# --------------------------------------------------

@app.route("/admin-ui/applications")
def admin_ui_applications():
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT application_id, application_name, user_email, expiry_date, is_active
           FROM applications ORDER BY created_at DESC"""
    )
    applications = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("applications.html", applications=applications)


@app.route("/admin-ui/create-application", methods=["GET", "POST"])
def admin_ui_create_application():
    if request.method == "GET":
        return render_template("create_application.html")

    application_name  = request.form.get("application_name")
    user_email        = request.form.get("user_email")
    application_id    = str(uuid.uuid4())
    application_token = secrets.token_urlsafe(32)
    hashed_token      = generate_password_hash(application_token)
    expiry_date       = datetime.now() + timedelta(days=90)

    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(
        """INSERT INTO applications
           (application_id, application_token, application_name, user_email, expiry_date)
           VALUES (%s,%s,%s,%s,%s)""",
        (application_id, hashed_token, application_name, user_email, expiry_date)
    )
    conn.commit()
    cur.close()
    conn.close()

    try:
        send_onboarding_email(app, user_email, application_id,
                              application_token, expiry_date.strftime("%Y-%m-%d"))
    except Exception as e:
        print("Email sending failed:", e)

    return render_template(
        "application_created.html",
        application_id=application_id,
        application_token=application_token,
        expiry_date=expiry_date.strftime("%Y-%m-%d"),
    )


@app.route("/admin-ui/update-status", methods=["POST"])
def admin_ui_update_status():
    application_id = request.form.get("application_id")
    is_active      = request.form.get("is_active") == "true"

    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)

    cur.execute("SELECT user_email FROM applications WHERE application_id = %s", (application_id,))
    application = cur.fetchone()

    cur.execute("UPDATE applications SET is_active = %s WHERE application_id = %s",
                (is_active, application_id))
    conn.commit()

    if application and not is_active:
        try:
            send_inactive_email(app, application["user_email"], application_id)
        except Exception as e:
            print("Inactive email failed:", e)

    cur.close()
    conn.close()
    return redirect(url_for("admin_ui_applications"))


@app.route("/admin-ui/update-expiry", methods=["POST"])
def admin_ui_update_expiry():
    application_id = request.form.get("application_id")
    expiry_date    = request.form.get("expiry_date")

    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)

    cur.execute("SELECT user_email FROM applications WHERE application_id = %s", (application_id,))
    application = cur.fetchone()

    cur.execute("UPDATE applications SET expiry_date = %s WHERE application_id = %s",
                (expiry_date, application_id))
    conn.commit()

    if application:
        try:
            send_renewal_email(app, application["user_email"], application_id, expiry_date)
        except Exception as e:
            print("Renewal email failed:", e)

    cur.close()
    conn.close()
    return redirect(url_for("admin_ui_applications"))


# --------------------------------------------------
# ADMIN UI — AUTH LOGS
# --------------------------------------------------

@app.route("/admin-ui/auth-logs")
def admin_ui_auth_logs():
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT application_id, endpoint, request_time, status, reason, ip_address
           FROM authentication_logs ORDER BY request_time DESC"""
    )
    logs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("auth_logs.html", logs=logs)


# --------------------------------------------------
# ADMIN UI — SHIPMENTS
# --------------------------------------------------

def _get_all_shipments():
    """Shared query used by multiple routes."""
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT
               s.shipment_id,
               s.requestid,
               s.application_id,
               s.service,
               s.validation_status,
               s.validation_reason,
               s.state,
               s.tracking_number,
               s.return_code,
               s.created_at,
               s.tracking_number,
               sender.full_name  AS sender_name,
               sender.email      AS sender_email,
               receiver.full_name AS receiver_name,
               receiver.email    AS receiver_email,
               from_addr.country AS from_country,
               to_addr.country   AS to_country,
               CASE WHEN sl.label_id IS NOT NULL THEN 'uploaded' ELSE 'pending' END AS label_status,
               sl.file_path      AS label_file_path
           FROM shipments s
           JOIN customers sender   ON s.sender_customer_id   = sender.customer_id
           JOIN customers receiver ON s.receiver_customer_id = receiver.customer_id
           JOIN addresses from_addr ON s.from_address_id     = from_addr.address_id
           JOIN addresses to_addr   ON s.to_address_id       = to_addr.address_id
           LEFT JOIN shipment_labels sl
    ON sl.label_id = (
        SELECT MAX(sl2.label_id)
        FROM shipment_labels sl2
        WHERE sl2.shipment_id = s.shipment_id
    )
           ORDER BY s.shipment_id DESC"""
    )
    shipments = cur.fetchall()
    cur.close()
    conn.close()
    return shipments


@app.route("/admin-ui/shipments")
def admin_ui_shipments():
    return render_template("shipments.html", shipments=_get_all_shipments())


@app.route("/admin-ui/create-shipment", methods=["GET", "POST"])
def admin_ui_create_shipment():

    if request.method == "GET":
        conn = get_db_connection()
        cur  = conn.cursor(dictionary=True)

        # FIX Bug 3: use application_id not id
        cur.execute("""
    SELECT
        application_id,
        application_name,
        user_email,
        phone_number
    FROM applications
    WHERE is_active = TRUE
    ORDER BY application_name
""")
        applications = cur.fetchall()

        cur.execute("SELECT customer_id, full_name, email, phone_number FROM customers ORDER BY full_name")
        customers = cur.fetchall()

        cur.close()
        conn.close()

        return render_template(
            "create_shipment.html",
            applications=applications,
            customers=customers
        )

    # POST — collect form data
    sender_name        = request.form.get("sender_name")
    sender_email       = request.form.get("sender_email")
    sender_phone_code  = request.form.get("sender_phone_code")
    sender_phone       = request.form.get("sender_phone")

    receiver_name      = request.form.get("receiver_name")
    receiver_email     = request.form.get("receiver_email")
    receiver_phone_code = request.form.get("receiver_phone_code")
    receiver_phone     = request.form.get("receiver_phone")

    from_address       = request.form.get("from_address")
    from_city          = request.form.get("from_city")
    from_state         = request.form.get("from_state")
    from_country       = request.form.get("from_country")
    from_country_code  = request.form.get("from_country_code")
    from_postal_code   = request.form.get("from_postal_code")

    to_address         = request.form.get("to_address")
    to_city            = request.form.get("to_city")
    to_state           = request.form.get("to_state")
    to_country         = request.form.get("to_country")
    to_country_code    = request.form.get("to_country_code")
    to_postal_code     = request.form.get("to_postal_code")

    service            = request.form.get("service")
    application_id     = request.form.get("application_id")

    # NEW: tracking number, populated by the "Create Shipment from PDF" flow
    # (will be empty/None for shipments created via the manual form)
    tracking_number     = request.form.get("tracking_number") or None

    # Validation
    def validate_country_rules(country, country_code, phone_code, phone, postal, label):
        if country == "India":
            if country_code != "IN":
                return f"{label} country code must be IN"
            if phone_code != "+91":
                return f"{label} India phone code must be +91"
            if not phone.isdigit() or len(phone) != 10:
                return f"{label} India phone number must be 10 digits"
            if not postal.isdigit() or len(postal) != 6:
                return f"{label} India postal code must be 6 digits"
        elif country == "USA":
            if country_code != "US":
                return f"{label} country code must be US"
            if phone_code != "+1":
                return f"{label} USA phone code must be +1"
            if not phone.isdigit() or len(phone) != 10:
                return f"{label} USA phone number must be 10 digits"
            if not postal.isdigit() or len(postal) != 5:
                return f"{label} USA postal code must be 5 digits"
        else:
            return f"{label} country must be either India or USA"
        return None

    err = validate_country_rules(from_country, from_country_code, sender_phone_code,
                                 sender_phone, from_postal_code, "Sender")
    if err:
        return err

    err = validate_country_rules(to_country, to_country_code, receiver_phone_code,
                                 receiver_phone, to_postal_code, "Receiver")
    if err:
        return err

    requestid = str(uuid.uuid4())

    conn = get_db_connection()
    cur  = conn.cursor()

    # Sender customer
    cur.execute(
        "INSERT INTO customers(full_name, phone_number, email) VALUES(%s,%s,%s)",
        (sender_name, sender_phone_code + " " + sender_phone, sender_email)
    )
    sender_customer_id = cur.lastrowid

    # Receiver customer
    cur.execute(
        "INSERT INTO customers(full_name, phone_number, email) VALUES(%s,%s,%s)",
        (receiver_name, receiver_phone_code + " " + receiver_phone, receiver_email)
    )
    receiver_customer_id = cur.lastrowid

    # Sender address
    cur.execute(
        """INSERT INTO addresses(address_line1, address_line2, city, state_name, country, country_code, postal_code)
           VALUES(%s,%s,%s,%s,%s,%s,%s)""",
        (from_address, None, from_city, from_state, from_country, from_country_code, from_postal_code)
    )
    from_address_id = cur.lastrowid

    # FIX Bug 2: receiver address had 7 columns but only 6 placeholders — now correct
    cur.execute(
        """INSERT INTO addresses(address_line1, address_line2, city, state_name, country, country_code, postal_code)
           VALUES(%s,%s,%s,%s,%s,%s,%s)""",
        (to_address, None, to_city, to_state, to_country, to_country_code, to_postal_code)
    )
    to_address_id = cur.lastrowid

    # Shipment — now includes application_id and tracking_number
    cur.execute(
        """INSERT INTO shipments(
               requestid, application_id,
               sender_customer_id, receiver_customer_id,
               from_address_id, to_address_id,
               service, validation_status, validation_reason, state, return_code,
               tracking_number
           ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (requestid, application_id,
         sender_customer_id, receiver_customer_id,
         from_address_id, to_address_id,
         service, "valid", "No issues", "initiated", 200,
         tracking_number)
    )
    shipment_id = cur.lastrowid

    cur.execute(
        "INSERT INTO shipment_tracking(shipment_id, current_status) VALUES(%s,%s)",
        (shipment_id, "initiated")
    )
    conn.commit()
    cur.close()
    conn.close()

    # NEW: send confirmation email to sender
    try:
        send_shipment_confirmation_email(
            app, sender_email, shipment_id, requestid,
            service, sender_name, receiver_name
        )
    except Exception as e:
        print("Shipment confirmation email failed:", e)

    return redirect(url_for("admin_ui_shipments"))


@app.route("/admin-ui/edit-shipment/<int:shipment_id>", methods=["GET", "POST"])
def admin_ui_edit_shipment(shipment_id):
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)

    if request.method == "GET":
        cur.execute(
            """SELECT s.shipment_id, s.service,
                      s.sender_customer_id,
                      s.receiver_customer_id,
                      sender.full_name      AS sender_name,
                      sender.email          AS sender_email,
                      sender.phone_number   AS sender_phone,
                      receiver.full_name    AS receiver_name,
                      receiver.email        AS receiver_email,
                      receiver.phone_number AS receiver_phone
               FROM shipments s
               JOIN customers sender    ON s.sender_customer_id   = sender.customer_id
               JOIN customers receiver  ON s.receiver_customer_id = receiver.customer_id
               WHERE s.shipment_id = %s""",
            (shipment_id,)
        )
        shipment = cur.fetchone()
        cur.close()
        conn.close()

        if not shipment:
            return "Shipment not found", 404

        return render_template("edit_shipment.html", shipment=shipment)

    # POST — update customer records + service
    sender_name    = request.form.get("sender_name")
    sender_email   = request.form.get("sender_email")
    sender_phone   = request.form.get("sender_phone")
    receiver_name  = request.form.get("receiver_name")
    receiver_email = request.form.get("receiver_email")
    receiver_phone = request.form.get("receiver_phone")
    service        = request.form.get("service")

    # Get customer IDs from shipment
    cur.execute(
        "SELECT sender_customer_id, receiver_customer_id FROM shipments WHERE shipment_id = %s",
        (shipment_id,)
    )
    ids = cur.fetchone()

    # Update sender customer
    cur.execute(
        "UPDATE customers SET full_name=%s, email=%s, phone_number=%s WHERE customer_id=%s",
        (sender_name, sender_email, sender_phone, ids["sender_customer_id"])
    )

    # Update receiver customer
    cur.execute(
        "UPDATE customers SET full_name=%s, email=%s, phone_number=%s WHERE customer_id=%s",
        (receiver_name, receiver_email, receiver_phone, ids["receiver_customer_id"])
    )

    # Update shipment service
    cur.execute(
        "UPDATE shipments SET service=%s WHERE shipment_id=%s",
        (service, shipment_id)
    )

    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("admin_ui_shipments"))

# --------------------------------------------------
# ADMIN UI — LABEL UPLOAD & VIEW
# --------------------------------------------------

@app.route("/admin-ui/upload-label", methods=["GET", "POST"])
def admin_ui_upload_label():
    if request.method == "GET":
        shipment_id = request.args.get("shipment_id")
        return render_template("upload_label.html", shipment_id=shipment_id)

    shipment_id = request.form.get("shipment_id")
    label_file = request.files.get("label_file")

    if not shipment_id or not label_file:
        return "Shipment ID and PDF file are required", 400

    if not label_file.filename.lower().endswith(".pdf"):
        return "Only PDF files are allowed", 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT c.email
        FROM shipments s
        JOIN customers c ON s.receiver_customer_id = c.customer_id
        WHERE s.shipment_id = %s
        """,
        (shipment_id,)
    )
    receiver = cur.fetchone()

    if not receiver or not receiver[0]:
        cur.close()
        conn.close()
        return "Receiver email not found for this shipment", 404

    customer_email = receiver[0]

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    filename = secure_filename(label_file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    label_file.save(file_path)

    tracking_number = None

    try:
        tracking_number = extract_tracking_number_from_pdf(file_path)
    except Exception as e:
        print("Tracking number extraction failed:", e)

    cur.execute(
        """
        INSERT INTO shipment_labels
        (shipment_id, file_name, file_path, emailed_to_customer)
        VALUES (%s, %s, %s, %s)
        """,
        (shipment_id, filename, file_path, False)
    )

    cur.execute(
        """
        UPDATE shipments
        SET state = 'label_uploaded',
            tracking_number = %s
        WHERE shipment_id = %s
        """,
        (tracking_number, shipment_id)
    )

    conn.commit()

    try:
        send_label_notification(app, customer_email, shipment_id, file_path)

        cur.execute(
            """
            UPDATE shipment_labels
            SET emailed_to_customer = TRUE
            WHERE shipment_id = %s
            ORDER BY label_id DESC
            LIMIT 1
            """,
            (shipment_id,)
        )

        conn.commit()

    except Exception as e:
        print("Label email failed:", e)

    cur.close()
    conn.close()

    return redirect(url_for("admin_ui_shipments"))

# FIX Bug 9: /view-label route was missing — now added
@app.route("/admin-ui/view-label/<int:shipment_id>")
def admin_ui_view_label(shipment_id):
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT file_name, file_path FROM shipment_labels WHERE shipment_id = %s ORDER BY label_id DESC LIMIT 1",
        (shipment_id,)
    )
    label = cur.fetchone()
    cur.close()
    conn.close()

    if not label:
        return "Label not found", 404

    directory = os.path.dirname(os.path.abspath(label["file_path"]))
    return send_from_directory(directory, label["file_name"], as_attachment=False)


# --------------------------------------------------
# ADMIN UI — CUSTOMER LOOKUP
# --------------------------------------------------

@app.route("/admin-ui/customer/<int:customer_id>")
def get_customer(customer_id):
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT customer_id, full_name, email, phone_number FROM customers WHERE customer_id = %s",
        (customer_id,)
    )
    customer = cur.fetchone()
    cur.close()
    conn.close()

    if customer:
        return jsonify(customer)
    return jsonify({"error": "Customer not found"}), 404


# --------------------------------------------------
# ADMIN UI — CREATE SHIPMENT FROM PDF LABEL
# --------------------------------------------------



@app.route("/admin-ui/extract-label", methods=["POST"])
def extract_label():
    if "label_pdf" not in request.files:
        return jsonify({"status": "error", "reason": "No file uploaded"}), 400

    file = request.files["label_pdf"]

    try:
        with pdfplumber.open(file) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        return jsonify({"status": "error", "reason": f"Could not parse PDF: {e}"}), 400

    if not text.strip():
        return jsonify({"status": "error", "reason": "No extractable text found in PDF"}), 400

    fields = extract_fedex_fields(text)

    return jsonify({"status": "success", "fields": fields})


def extract_tracking_number(text):
    """
    Robustly find a FedEx tracking number in extracted PDF text.
    Handles 12, 14, and 15-digit FedEx tracking numbers, with or without
    spaces, and works whether or not a "Tracking Number:" / "TRK#" label
    is present nearby. Returns None if nothing plausible is found —
    callers must treat that as "not available" and never fail on it.
    """
    if not text:
        return None

    # 1) Highest confidence: explicit "Tracking Number:" or "TRK#" label
    #    followed by a run of digits/spaces.
    labeled_match = re.search(
        r"(?:Tracking\s*Number|TRK#?)\s*[:\-]?\s*([\d\s]{10,20})",
        text,
        re.IGNORECASE
    )
    if labeled_match:
        candidate = re.sub(r"\s+", "", labeled_match.group(1))
        if 12 <= len(candidate) <= 15:
            return candidate

    # 2) Fallback: bare 4-4-4 grouped 12-digit number (common FedEx Express format)
    grouped_match = re.search(r"\b(\d{4}\s\d{4}\s\d{4})\b", text)
    if grouped_match:
        return grouped_match.group(1).replace(" ", "")

    # 3) Fallback: bare contiguous 15, 14, then 12-digit sequences
    for length in (15, 14, 12):
        bare_match = re.search(r"(?<!\d)(\d{%d})(?!\d)" % length, text)
        if bare_match:
            return bare_match.group(1)

    return None


def extract_fedex_fields(text: str) -> dict:
    fields = {}

    # Tracking number — now uses the shared, more robust extractor
    fields["tracking_number"] = extract_tracking_number(text)

    # Reference number
    ref_match = re.search(r"REF[:\s]+(\S+)", text, re.IGNORECASE)
    fields["reference"] = ref_match.group(1) if ref_match else None

    # Ship date
    date_match = re.search(r"SHIP DATE[:\s]+([0-9]{1,2}[A-Z]{3}[0-9]{2})", text, re.IGNORECASE)
    fields["ship_date"] = date_match.group(1) if date_match else None

    # --- Sender (FROM / ORIGIN side) ---
    origin_phone = re.search(r"\((\d{3})\)\s?(\d{3})-(\d{4})", text)
    fields["from_phone"] = "".join(origin_phone.groups()) if origin_phone else None

    origin_zip = re.search(r"([A-Z]{2}\s?\d{5})\s+US", text)
    if origin_zip:
        fields["from_zip"] = re.search(r"\d{5}", origin_zip.group(1)).group(0)
        fields["from_state"] = re.search(r"[A-Z]{2}", origin_zip.group(1)).group(0)

    # --- Receiver (TO side) — adjust based on your label layout ---
    to_name_match = re.search(r"TO\s+([A-Z\s]+?)\n", text)
    fields["to_name"] = to_name_match.group(1).strip() if to_name_match else None

    # Add more parsing rules here as you encounter more label variants
    fields["service"] = "US_TO_INDIA_PARCEL_EXPRESS"  # default/fallback, refine based on label text

    return fields


@app.route("/admin-ui/create-shipment-from-text", methods=["GET", "POST"])
def create_shipment_from_text():

    if request.method == "GET":
        return render_template("create_shipment_from_text.html")

    shipment_text = request.form.get("shipment_text")
    service = request.form.get("service", "Express International")

    if not shipment_text:
        return "Shipment text is required", 400

    try:
        sender_part = shipment_text.split("Receiver:")[0].replace("Sender:", "").strip()
        receiver_part = shipment_text.split("Receiver:")[1].strip()

        def extract_details(part, person_type):
            lines = [line.strip() for line in part.split("\n") if line.strip()]

            name = lines[0]

            phone_match = re.search(r"Ph:\s*(\+\d+)\s*(\d+)", part)
            phone_code = phone_match.group(1) if phone_match else ""
            phone = phone_match.group(2) if phone_match else ""

            email_match = re.search(
                r"(?:email|gmail|mail)\s*:\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})",
                part,
                re.IGNORECASE
            )

            if email_match:
                email = email_match.group(1)
            else:
                email = f"{person_type}_{uuid.uuid4().hex[:8]}@example.com"

            postal_match = re.search(r"\b(\d{5,6})\b", part)
            postal_code = postal_match.group(1) if postal_match else ""

            address_lines = []
            for line in lines[1:]:
                if not line.lower().startswith("ph:") and "@" not in line:
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

            for line in address_lines:
                if postal_code and postal_code in line:
                    parts = [p.strip() for p in line.split(",")]

                    if country == "USA" and len(parts) >= 2:
                        city = parts[0]
                        state = parts[1]

                    elif country == "India" and len(parts) >= 2:
                        city = parts[-2]
                        state = parts[-3] if len(parts) >= 3 else ""

            return {
                "name": name,
                "email": email,
                "phone_code": phone_code,
                "phone": phone,
                "address": full_address,
                "city": city,
                "state": state,
                "country": country,
                "country_code": country_code,
                "postal_code": postal_code
            }

        sender = extract_details(sender_part, "sender")
        receiver = extract_details(receiver_part, "receiver")

        requestid = str(uuid.uuid4())

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO customers(full_name, phone_number, email)
            VALUES (%s, %s, %s)
        """, (
            sender["name"],
            sender["phone_code"] + " " + sender["phone"],
            sender["email"]
        ))
        sender_customer_id = cur.lastrowid

        cur.execute("""
            INSERT INTO customers(full_name, phone_number, email)
            VALUES (%s, %s, %s)
        """, (
            receiver["name"],
            receiver["phone_code"] + " " + receiver["phone"],
            receiver["email"]
        ))
        receiver_customer_id = cur.lastrowid

        cur.execute("""
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
            sender["address"],
            None,
            sender["city"],
            sender["state"],
            sender["country"],
            sender["country_code"],
            sender["postal_code"]
        ))
        from_address_id = cur.lastrowid

        cur.execute("""
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
            receiver["address"],
            None,
            receiver["city"],
            receiver["state"],
            receiver["country"],
            receiver["country_code"],
            receiver["postal_code"]
        ))
        to_address_id = cur.lastrowid

        cur.execute("""
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

        shipment_id = cur.lastrowid

        cur.execute("""
            INSERT INTO shipment_tracking(shipment_id, current_status)
            VALUES (%s, %s)
        """, (
            shipment_id,
            "initiated"
        ))

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("admin_ui_shipments"))

    except Exception as e:
        return f"Could not create shipment from text: {str(e)}", 500

def extract_tracking_number_from_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    # Prefer number before "IP EOD" in FedEx label
    match = re.search(r"\b(\d{4}\s+\d{4}\s+\d{4})\s+IP\s+EOD\b", text)

    if match:
        return match.group(1).replace(" ", "")

    return None

# --------------------------------------------------
# ADMIN UI — INVOICE GENERATOR
# Paste this into app_manager.py before:
#   if __name__ == "__main__":
# --------------------------------------------------

@app.route("/admin-ui/invoice-generator")
def admin_ui_invoice_generator():
    return render_template("invoice_generator.html")


@app.route("/admin-ui/invoice-generator/<int:shipment_id>")
def admin_ui_invoice_from_shipment(shipment_id):
    """
    Opens the invoice generator pre-filled from an existing shipment.
    """
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT s.shipment_id, s.requestid, s.service, s.tracking_number,
                  sender.full_name    AS sender_name,
                  sender.email        AS sender_email,
                  sender.phone_number AS sender_phone,
                  receiver.full_name  AS receiver_name,
                  receiver.email      AS receiver_email,
                  receiver.phone_number AS receiver_phone,
                  fa.address_line1    AS from_address,
                  fa.city             AS from_city,
                  fa.state_name       AS from_state,
                  fa.postal_code      AS from_postal,
                  fa.country          AS from_country,
                  ta.address_line1    AS to_address,
                  ta.city             AS to_city,
                  ta.state_name       AS to_state,
                  ta.postal_code      AS to_postal,
                  ta.country          AS to_country
           FROM shipments s
           JOIN customers sender    ON s.sender_customer_id   = sender.customer_id
           JOIN customers receiver  ON s.receiver_customer_id = receiver.customer_id
           JOIN addresses fa        ON s.from_address_id      = fa.address_id
           JOIN addresses ta        ON s.to_address_id        = ta.address_id
           WHERE s.shipment_id = %s""",
        (shipment_id,)
    )
    shipment = cur.fetchone()
    cur.close()
    conn.close()

    if not shipment:
        return "Shipment not found", 404

    return render_template("invoice_generator.html", shipment=shipment)
# --------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5001)