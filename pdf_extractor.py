# pdf_extractor.py
# Parses FedEx-style international shipping label PDFs (US <-> India).

import re
import pdfplumber


def _clean(v):
    return " ".join(str(v).split()).strip()


def extract_label_fields(pdf_path: str) -> dict:
    """Extract sender/receiver fields from a FedEx shipping label PDF."""

    raw = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                raw.extend(t.splitlines())

    lines = [_clean(l) for l in raw if _clean(l)]
    full  = " ".join(lines)

    result = {
        "from_name":         "",
        "from_phone":        "",
        "from_address1":     "",
        "from_city":         "",
        "from_state":        "",
        "from_country":      "USA",
        "from_country_code": "US",
        "from_zip":          "",
        "to_name":           "",
        "to_phone":          "",
        "to_address1":       "",
        "to_city":           "",
        "to_state":          "",
        "to_country":        "India",
        "to_country_code":   "IN",
        "to_postal":         "",
        "service":           "US_TO_INDIA_DOCUMENT_EXPRESS",
        "tracking_number":   "",
        "ship_date":         "",
        "reference":         "",
    }

    india_states = {
        "AP","AR","AS","BR","CG","GA","GJ","HR","HP","JH","KA","KL",
        "MP","MH","MN","ML","MZ","NL","OD","PB","RJ","SK","TN","TS",
        "TR","UP","UK","WB"
    }

    us_states = {
        "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID",
        "IL","IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS",
        "MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK",
        "OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"
    }

    # ── 1. Tracking number ──
    trk = re.search(r"\b(\d{4})\s+(\d{4})\s+(\d{4})\b", full)
    if trk:
        result["tracking_number"] = trk.group(1) + trk.group(2) + trk.group(3)

    # ── 2. Ship date ──
    sd = re.search(r"SHIP\s+DATE:\s*(\S+)", full, re.IGNORECASE)
    if sd:
        result["ship_date"] = sd.group(1)

    # ── 3. Reference ──
    for i, l in enumerate(lines):
        if re.fullmatch(r"REF:", l, re.IGNORECASE) and i + 1 < len(lines):
            if re.fullmatch(r"\d{8,}", lines[i + 1]):
                result["reference"] = lines[i + 1]
            break

    # ── 4. Receiver phone (INV: line) ──
    inv = re.search(r"INV:\s*(\d{10})", full, re.IGNORECASE)
    if inv:
        result["to_phone"] = inv.group(1)

    # ── 5. Receiver city / state / PIN ──
    for i, l in enumerate(lines):
        if re.fullmatch(r"[A-Z]{2}", l) and l in india_states:
            if i + 1 < len(lines) and re.fullmatch(r"\d{6}", lines[i + 1]):
                result["to_state"]  = l
                result["to_postal"] = lines[i + 1]
                if i > 0:
                    result["to_city"] = lines[i - 1]
                break

    # ── 6. Receiver name ──
    # Sits between address block and the "TO" keyword that precedes SIGN:
    sign_idx = next((i for i, l in enumerate(lines) if l == "SIGN:"), None)
    to_before_sign = None
    if sign_idx:
        for i in range(sign_idx - 1, max(0, sign_idx - 5), -1):
            if lines[i] == "TO":
                to_before_sign = i
                break

    if to_before_sign is not None:
        name_parts = []
        for l in reversed(lines[max(0, to_before_sign - 5):to_before_sign]):
            if (re.fullmatch(r"[A-Z][A-Z\s\.]*", l)
                    and 1 <= len(l.split()) <= 3
                    and len(l) <= 20
                    and not re.search(
                        r"COURIER|CHURCH|FLOOR|GROUND|SAROJINI|EXPRESS|MILLIENIUM", l, re.IGNORECASE)):
                name_parts.insert(0, l)
            else:
                break
        result["to_name"] = " ".join(name_parts)

    # ── 7. Receiver address ──
    addr_start = next((i for i, l in enumerate(lines) if re.match(r"\d+-\d+", l)), None)
    if addr_start is not None:
        name_count = len(result["to_name"].split()) if result["to_name"] else 0
        end = (to_before_sign - name_count) if to_before_sign else addr_start + 6
        result["to_address1"] = " ".join(lines[addr_start:end])

    # ── 8. Sender name (after SIGN:) ──
    if sign_idx is not None:
        np = []
        for l in lines[sign_idx + 1:sign_idx + 6]:
            if re.search(r"^NO$|^EEI$|LATHROP|BILL|DIMS|30\.", l, re.IGNORECASE):
                break
            if re.fullmatch(r"[A-Z]+", l):
                np.append(l)
        result["from_name"] = " ".join(np)

    # ── 9. Sender phone (ORIGIN ID line) ──
    origin_idx = next((i for i, l in enumerate(lines) if l.startswith("ORIGIN")), None)
    if origin_idx is not None:
        snippet = " ".join(lines[origin_idx:origin_idx + 5])
        ph = re.search(r"\((\d{3})\)\s*(\d{3})-(\d{4})", snippet)
        if ph:
            result["from_phone"] = ph.group(1) + ph.group(2) + ph.group(3)

    # ── 10. Sender city / state / ZIP ──
    # Most reliable: city line ends with a comma (e.g. "LATHROP,")
    city_idx = next(
        (i for i, l in enumerate(lines)
         if l.endswith(",") and re.fullmatch(r"[A-Z]+,", l) and i > (sign_idx or 0)),
        None
    )
    if city_idx is not None:
        result["from_city"] = lines[city_idx].rstrip(",")
        for l in lines[city_idx + 1:city_idx + 5]:
            if re.fullmatch(r"[A-Z]{2}", l) and l in us_states and not result["from_state"]:
                result["from_state"] = l
            elif re.fullmatch(r"\d{5}", l) and not result["from_zip"]:
                result["from_zip"] = l

        # ── 11. Sender street address (appears AFTER zip block) ──
        # Only exclude clear non-address tokens; do NOT exclude US state codes
        # since many overlap with street suffixes (CT, IN, OR, etc.)
        excl = {
            "US","IN","BILL","SENDER","DIMS","ACTWGT","CAD","ORIGIN",
            "SIGN","NO","EEI","SHIP","DATE","ETD","EOD","LB","AA","IP",
        } | india_states

        from_zip_val = result["from_zip"]
        for i, l in enumerate(lines[city_idx + 4: city_idx + 18], start=city_idx + 4):
            if re.fullmatch(r"\d{3,6}", l) and l != from_zip_val:
                addr_parts = [l]
                for l2 in lines[i + 1:i + 4]:
                    if re.fullmatch(r"[A-Z]{2,10}", l2) and l2 not in excl:
                        addr_parts.append(l2)
                    else:
                        break
                result["from_address1"] = " ".join(addr_parts)
                break

    # ── 12. Service type ──
    if re.search(r"PRIORITY", full, re.IGNORECASE):
        result["service"] = "US_TO_INDIA_PARCEL_PRIORITY"
    elif re.search(r"PARCEL|PKG|PACKAGE", full, re.IGNORECASE):
        result["service"] = "US_TO_INDIA_PARCEL_EXPRESS"
    else:
        result["service"] = "US_TO_INDIA_DOCUMENT_EXPRESS"

    return result


if __name__ == "__main__":
    import json, sys
    path = sys.argv[1] if len(sys.argv) > 1 else "label.pdf"
    print(json.dumps(extract_label_fields(path), indent=2))
