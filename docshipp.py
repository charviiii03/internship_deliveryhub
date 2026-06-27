import re

import uuid

from db import get_db_connection

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

        # -----------------------------
        # SQL INJECTION CHECK
        # -----------------------------
        sql_keywords = [
            "DROP",
            "DELETE",
            "TRUNCATE",
            "ALTER",
            "INSERT",
            "UPDATE"
        ]

        for keyword in sql_keywords:
            if keyword in text.upper():
                return jsonify({
                    "status": "invalid",
                    "reason": "Potential SQL injection detected"
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

    if not data:
        return jsonify({
            "status": "invalid",
            "reason": "No data received"
        }), 400

    # -----------------------------
    # REQUIRED FIELDS
    # -----------------------------

    required_fields = {
        "from_name": "Sender name",
        "from_phone": "Sender phone number",
        "from_address1": "Sender address",
        "from_country": "Sender country",
        "from_state": "Sender state",
        "from_city": "Sender city",
        "from_zip": "Sender ZIP code",

        "to_name": "Receiver name",
        "to_phone": "Receiver phone number",
        "to_address1": "Receiver address",
        "to_country": "Receiver country",
        "to_state": "Receiver state",
        "to_city": "Receiver city",
        "to_postal": "Receiver postal code",

        "email": "Customer email"
    }

    for field, label in required_fields.items():

        if not str(data.get(field, "")).strip():

            return jsonify({
                "status": "invalid",
                "reason": f"{label} is required"
            }), 400

    # -----------------------------
    # EMAIL VALIDATION
    # -----------------------------

    email = str(data.get("email")).strip()

    if not re.fullmatch(
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
        email
    ):

        return jsonify({
            "status": "invalid",
            "reason": "Invalid email address"
        }), 400

    # -----------------------------
    # PHONE VALIDATION
    # -----------------------------

    from_phone = re.sub(
        r"\D",
        "",
        str(data.get("from_phone"))
    )

    to_phone = re.sub(
        r"\D",
        "",
        str(data.get("to_phone"))
    )

    if len(from_phone) != 10:

        return jsonify({
            "status": "invalid",
            "reason": "Invalid sender phone number"
        }), 400

    if len(to_phone) != 10:

        return jsonify({
            "status": "invalid",
            "reason": "Invalid receiver phone number"
        }), 400

    # -----------------------------
    # ZIP / PIN VALIDATION
    # -----------------------------

    from_country = str(
        data.get("from_country")
    ).upper()

    if from_country == "US":

        if not re.fullmatch(
            r"\d{5}",
            str(data.get("from_zip"))
        ):

            return jsonify({
                "status": "invalid",
                "reason": "Sender ZIP code must be exactly 5 digits"
            }), 400

    to_country = str(
        data.get("to_country")
    ).upper()

    if to_country == "IN":

        if not re.fullmatch(
            r"\d{6}",
            str(data.get("to_postal"))
        ):

            return jsonify({
                "status": "invalid",
                "reason": "Receiver PIN code must be exactly 6 digits"
            }), 400

    # -----------------------------
    # DATABASE CONNECTION
    # -----------------------------

    conn = get_db_connection()

    if not conn:

        return jsonify({
            "status": "error",
            "reason": "Database connection failed"
        }), 500

    cursor = conn.cursor()

    try:

        # -----------------------------
        # SENDER CUSTOMER
        # -----------------------------

        cursor.execute(
            """
            INSERT INTO customers(
                full_name,
                phone_number
            )
            VALUES(%s,%s)
            """,
            (
                data["from_name"],
                data["from_phone"]
            )
        )

        sender_customer_id = cursor.lastrowid

        # -----------------------------
        # RECEIVER CUSTOMER
        # -----------------------------

        cursor.execute(
            """
            INSERT INTO customers(
                full_name,
                phone_number
            )
            VALUES(%s,%s)
            """,
            (
                data["to_name"],
                "to_phone"
            )
        )

        receiver_customer_id = cursor.lastrowid

        # -----------------------------
        # SENDER ADDRESS
        # -----------------------------

        sender_address = data["from_address1"]

        if data.get("from_address2"):
            sender_address += ", " + data["from_address2"]

        cursor.execute(
            """
            INSERT INTO addresses(
                address_line,
                city,
                state,
                country,
                postal_code
            )
            VALUES(%s,%s,%s,%s,%s)
            """,
            (
                sender_address,
                data["from_city"],
                data["from_state"],
                data["from_country"],
                data["from_zip"]
            )
        )

        from_address_id = cursor.lastrowid

        # -----------------------------
        # RECEIVER ADDRESS
        # -----------------------------

        receiver_address = data["to_address1"]

        if data.get("to_address2"):
            receiver_address += ", " + data["to_address2"]

        cursor.execute(
            """
            INSERT INTO addresses(
                address_line,
                city,
                state,
                country,
                postal_code
            )
            VALUES(%s,%s,%s,%s,%s)
            """,
            (
                receiver_address,
                data["to_city"],
                data["to_state"],
                data["to_country"],
                data["to_postal"]
            )
        )

        to_address_id = cursor.lastrowid

        # -----------------------------
        # SHIPMENT
        # -----------------------------

        request_id = str(uuid.uuid4())[:12]

        cursor.execute(
            """
            INSERT INTO shipments(
                requestid,
                sender_customer_id,
                receiver_customer_id,
                from_address_id,
                to_address_id,
                service,
                validation_status,
                state
            )
            VALUES(
                %s,%s,%s,%s,%s,%s,%s,%s
            )
            """,
            (
                request_id,
                sender_customer_id,
                receiver_customer_id,
                from_address_id,
                to_address_id,
                data.get("service", "Express"),
                "valid",
                "initiated"
            )
        )

        shipment_id = cursor.lastrowid

        conn.commit()

        return jsonify({
            "status": "valid",
            "shipment_id": shipment_id,
            "request_id": request_id,
            "message": "Shipment created successfully"
        }), 200

    except Exception as e:

        conn.rollback()

        return jsonify({
            "status": "error",
            "reason": str(e)
        }), 500

    finally:

        cursor.close()
        conn.close()
# -----------------------------
# RUN DOCSHIPP SERVICE
# -----------------------------
if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000
    )