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

@app.route("/signup", methods=["POST"])
def signup():

    data = request.get_json()

    application_name = data.get("application_name")
    user_email = data.get("user_email")

    application_id = str(uuid.uuid4())
    application_token = secrets.token_urlsafe(32)

    hashed_token = generate_password_hash(application_token)

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