import re

from werkzeug.exceptions import BadRequest
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app_manager import check_application_auth

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per hour"]
)

app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024


def is_valid_phone(phone):
    return re.fullmatch(r"[0-9]{8,15}", phone) is not None


def is_valid_email(email):
    return re.fullmatch(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) is not None


def is_safe_text(value):
    return re.fullmatch(r"[a-zA-Z0-9\s,.-]+", value) is not None


@app.route("/validate", methods=["POST"])
def validate_text():
    try:
        data = request.get_json()

        if not data or "text" not in data:
            return jsonify({
                "status": "invalid",
                "reason": "Text input missing"
            }), 400

        text = data["text"]

        if not isinstance(text, str):
            return jsonify({
                "status": "invalid",
                "reason": "Text must be a string"
            }), 400

        if len(text.strip()) == 0:
            return jsonify({
                "status": "invalid",
                "reason": "Empty input not allowed"
            }), 400

        if len(text) > 1000:
            return jsonify({
                "status": "invalid",
                "reason": "Input too large"
            }), 400

        if re.search(r"[^a-zA-Z0-9 ]", text):
            return jsonify({
                "status": "invalid",
                "reason": "Special characters found"
            }), 400

        return jsonify({
            "status": "valid"
        }), 200

    except BadRequest:
        return jsonify({
            "status": "invalid",
            "reason": "Invalid JSON"
        }), 400


@app.route("/generate-label", methods=["POST"])
@limiter.limit("10 per minute")
def generate_label():

    data = request.get_json()

    if not data:
        return jsonify({
            "status": "invalid",
            "reason": "Request body missing"
        }), 400

    application_id = data.get("application_id")
    application_token = data.get("application_token")

    application = check_application_auth(
        application_id,
        application_token,
        "/generate-label"
    )

    if not application:
        return jsonify({
            "status": "invalid",
            "reason": "authentication failed"
        }), 401

    required_fields = [
        "from_name",
        "from_address",
        "from_phone",
        "to_name",
        "to_address",
        "to_phone",
        "email"
    ]

    for field in required_fields:
        if not data.get(field):
            return jsonify({
                "status": "invalid",
                "reason": f"{field} is required"
            }), 400

    if not is_valid_phone(data.get("from_phone")):
        return jsonify({
            "status": "invalid",
            "reason": "Invalid sender phone number"
        }), 400

    if not is_valid_phone(data.get("to_phone")):
        return jsonify({
            "status": "invalid",
            "reason": "Invalid recipient phone number"
        }), 400

    if not is_valid_email(data.get("email")):
        return jsonify({
            "status": "invalid",
            "reason": "Invalid email format"
        }), 400

    for field in ["from_name", "from_address", "to_name", "to_address"]:
        if not is_safe_text(data.get(field)):
            return jsonify({
                "status": "invalid",
                "reason": f"Invalid characters in {field}"
            }), 400

    return jsonify({
        "status": "valid",
        "message": "label generated successfully"
    }), 200


if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000
    )