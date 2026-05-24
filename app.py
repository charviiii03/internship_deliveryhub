from flask import Flask, request, jsonify
import uuid
import json
from datetime import datetime
from db import get_db_connection

app = Flask(__name__)

@app.route("/generate-label", methods=["POST"])
def generate_label():

    data = request.get_json()
    requestid = str(uuid.uuid4())
    now = datetime.now()

    required_fields = [
        "from_name",
        "from_address",
        "from_country_code",
        "from_phone",
        "to_name",
        "to_address",
        "to_country_code",
        "to_phone",
        "service"
    ]

    for field in required_fields:
        if not data or field not in data or str(data[field]).strip() == "":
            response_json = {
                "status": "invalid",
                "reason": f"{field} is missing"
            }
            return_code = 400
            break
    else:
        valid_country_codes = ["+1", "+91"]

        if data.get("from_country_code") not in valid_country_codes:
            response_json = {
                "status": "invalid",
                "reason": "invalid from country code"
            }
            return_code = 400

        elif data.get("to_country_code") not in valid_country_codes:
            response_json = {
                "status": "invalid",
                "reason": "invalid to country code"
            }
            return_code = 400

        else:
            response_json = {
                "status": "valid",
                "requestid": requestid,
                "from_country_code": data["from_country_code"],
                "to_country_code": data["to_country_code"],
                "service": data["service"]
            }
            return_code = 200

    connection = get_db_connection()
    cursor = connection.cursor()

    sql = """
    INSERT INTO shipment_requests
    (datetime, requestid, from_name, from_address, from_phone,
    to_name, to_address, to_phone, service, return_code, return_json)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        now,
        requestid,
        data.get("from_name") if data else None,
        data.get("from_address") if data else None,
        data.get("from_phone") if data else None,
        data.get("to_name") if data else None,
        data.get("to_address") if data else None,
        data.get("to_phone") if data else None,
        data.get("service") if data else None,
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