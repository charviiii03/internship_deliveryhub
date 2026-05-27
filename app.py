# generates unique ids
import uuid

# generates secure random tokens
import secrets

# used for date and time operations
from datetime import datetime, timedelta

# used to hash passwords/tokens securely
from werkzeug.security import generate_password_hash, check_password_hash

from flask import Flask, request, jsonify
from db import get_db_connection

app = Flask(__name__)


# common function to check application authentication
def check_application_auth(application_id, application_token):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    sql = """
    SELECT * FROM applications
    WHERE application_id = %s
    AND expiry_date >= CURDATE()
    AND is_active = TRUE
    """

    cursor.execute(sql, (application_id,))
    application = cursor.fetchone()

    cursor.close()
    connection.close()

    if not application:
        return None

    if not check_password_hash(application["application_token"], application_token):
        return None

    return application

#Checks: application ID, application token, expiry date
@app.route("/generate-label", methods=["POST"])
def generate_label():

    data = request.get_json()

    application_id = data.get("application_id") if data else None
    application_token = data.get("application_token") if data else None

    application = check_application_auth(application_id, application_token)

    # if application == None, no matching application was found if not application:
    if not application:
        return jsonify({
            "status": "invalid",
            "reason": "authentication failed"
        }), 401

    return jsonify({
        "status": "valid",
        "message": "label generated successfully"
    }), 200

#Returns valid/invalid application
@app.route("/validate-auth", methods=["POST"])
def validate_auth():
    # get request data
    data = request.get_json()

    # get authentication values from request
    application_id = data.get("application_id") if data else None
    application_token = data.get("application_token") if data else None

    if not application_id or not application_token:
        return jsonify({
            "status": "invalid",
            "reason": "application id or token missing"
        }), 400

    application = check_application_auth(application_id, application_token)

    if application:
        return jsonify({
            "status": "valid",
            "message": "valid application"
        }), 200

    return jsonify({
        "status": "invalid",
        "reason": "invalid or expired application"
    }), 401

@app.route("/admin/create-application")
def signup():

    data = request.get_json()

    application_name = data.get("application_name")
    user_email = data.get("user_email")

    application_id = str(uuid.uuid4())
    application_token = secrets.token_urlsafe(32)

    hashed_token = generate_password_hash(application_token)
    # this converts token into encrypted/hashed form, 
    # original token is protected even if database leaks 

    expiry_date = datetime.now() + timedelta(days=90)

    connection = get_db_connection()
    cursor = connection.cursor()

    sql = """
    INSERT INTO applications
    (application_id, application_token, application_name, user_email, expiry_date)
    VALUES (%s, %s, %s, %s, %s)
    """

    values = (
        application_id,
        hashed_token,
        application_name,
        user_email,
        expiry_date
    )

    cursor.execute(sql, values)
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({
        "status": "success",
        "message": "application created successfully",
        "application_id": application_id,
        "application_token": application_token,
        "expiry_date": expiry_date.strftime("%Y-%m-%d")
    }), 201

@app.route("/admin/applications", methods=["GET"])
def view_applications():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT application_id, application_name, user_email, expiry_date, is_active
        FROM applications
    """)

    applications = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({
        "status": "success",
        "applications": applications
    }), 200

@app.route("/admin/update-status", methods=["PUT"])
def update_status():

    data = request.get_json()

    application_id = data.get("application_id")
    is_active = data.get("is_active")

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

    return jsonify({
        "status": "success",
        "message": "application status updated"
    }), 200

@app.route("/admin/auth-logs", methods=["GET"])
def view_auth_logs():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT application_id, request_time, status, reason, ip_address
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


@app.route("/admin/update-expiry", methods=["PUT"])
def update_expiry():

    data = request.get_json()

    application_id = data.get("application_id")
    new_expiry_date = data.get("expiry_date")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE applications
        SET expiry_date = %s
        WHERE application_id = %s
    """, (new_expiry_date, application_id))

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({
        "status": "success",
        "message": "expiry date updated"
    }), 200

@app.route("/signin", methods=["POST"])
def signin():

    data = request.get_json()

    application_id = data.get("application_id")
    application_token = data.get("application_token")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    sql = """
    SELECT * FROM applications
    WHERE application_id = %s
    AND expiry_date >= CURDATE()
    AND is_active = TRUE
    """

    cursor.execute(sql, (application_id,))
    application = cursor.fetchone()

    cursor.close()
    connection.close()

    if not application:
        return jsonify({
            "status": "invalid",
            "reason": "application not found or expired"
        }), 401

    if not check_password_hash(application["application_token"], application_token):
        return jsonify({
            "status": "invalid",
            "reason": "invalid token"
        }), 401

    return jsonify({
        "status": "valid",
        "message": "signin successful"
    }), 200

#run flask server only when this file is executed directly
if __name__ == "__main__":
    app.run(debug=True)