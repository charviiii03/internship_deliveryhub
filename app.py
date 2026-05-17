from flask import Flask, request, jsonify
import re

app = Flask(__name__)

@app.route("/validate", methods=["POST"])
def validate_text():

    data = request.get_json()

    if not data or "text" not in data:
        return jsonify({
            "status": "invalid",
            "reason": "Text input missing"
        }), 400

    text = data["text"]

    if re.search(r"[^a-zA-Z0-9\s]", text):
        return jsonify({
            "status": "invalid",
            "reason": "Special characters found"
        }), 400

    return jsonify({
        "status": "valid"
    }), 200


if __name__ == "__main__":
    app.run(debug=True)

    