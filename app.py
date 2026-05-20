from flask import Flask, request, jsonify
import re
import uuid
import json
from datetime import datetime
from db import get_db_connection

app = Flask(__name__)

@app.route("/validate", methods=["POST"])
def validate_text():

    data = request.get_json()
    requestid = str(uuid.uuid4())
    now = datetime.now()

    if not data or "text" not in data:
        response_json = {
            "status": "invalid",
            "reason": "Text input missing"
        }
        return_code = 400
        input_text = None

    else:
        input_text = data["text"]

        if not isinstance(input_text, str):
            response_json = {
                "status": "invalid",
                "reason": "Input must be a string"
            }
            return_code = 400

        elif input_text.strip() == "":
            response_json = {
                "status": "invalid",
                "reason": "Input cannot be empty"
            }
            return_code = 400

        elif re.search(r"[^a-zA-Z0-9\s]", input_text):
            response_json = {
                "status": "invalid",
                "reason": "Special characters found"
            }
            return_code = 400

        else:
            response_json = {
                "status": "valid",
                "requestid": requestid
            }
            return_code = 200

    connection = get_db_connection()
    cursor = connection.cursor()

    sql = """
    INSERT INTO docship_query
    (datetime, requestid, input_text, return_code, return_json)
    VALUES (%s, %s, %s, %s, %s)
    """

    values = (
        now,
        requestid,
        input_text,
        return_code,
        json.dumps(response_json)
    )

    cursor.execute(sql, values)
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify(response_json), return_code


if __name__ == "__main__":
    app.run(debug=True)
    