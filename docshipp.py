import re

from werkzeug.exceptions import BadRequest

from flask import Flask, request, jsonify

from app_manager import check_application_auth

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024


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

    except Exception as e:

        return jsonify({
            "status": "error",
            "reason": str(e)
        }), 500


@app.route("/generate-label", methods=["POST"])
def generate_label():

    data = request.get_json()

    application_id = data.get("application_id") if data else None
    application_token = data.get("application_token") if data else None

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

    return jsonify({
        "status": "valid",
        "message": "label generated successfully"
    }), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)