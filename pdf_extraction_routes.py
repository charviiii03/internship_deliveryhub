
# --------------------------------------------------
# ADMIN UI — CREATE SHIPMENT FROM PDF LABEL
# Add these routes to app_manager.py
# --------------------------------------------------

@app.route("/admin-ui/create-shipment-from-pdf", methods=["GET"])
def admin_ui_create_shipment_from_pdf():
    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT application_id, application_name FROM applications
           WHERE is_active = TRUE
           ORDER BY FIELD(application_name, 'DeliveryHub') DESC, application_name"""
    )
    applications = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("create_shipment_from_pdf.html", applications=applications)


@app.route("/admin-ui/extract-label", methods=["POST"])
def admin_ui_extract_label():
    """
    Accepts a PDF upload, runs pdf_extractor, returns JSON of extracted fields.
    The frontend then pre-fills the shipment form with the result.
    """
    from pdf_extractor import extract_label_fields

    label_file = request.files.get("label_pdf")

    if not label_file:
        return jsonify({"status": "error", "reason": "No PDF file received"}), 400

    if not label_file.filename.lower().endswith(".pdf"):
        return jsonify({"status": "error", "reason": "Only PDF files are accepted"}), 400

    # Save to a temp location for extraction
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    temp_filename = secure_filename(label_file.filename)
    temp_path     = os.path.join(app.config["UPLOAD_FOLDER"], "tmp_" + temp_filename)
    label_file.save(temp_path)

    try:
        fields = extract_label_fields(temp_path)
        return jsonify({"status": "success", "fields": fields}), 200
    except Exception as e:
        return jsonify({"status": "error", "reason": str(e)}), 500
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
