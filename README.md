# DeliveryHub — Admin Portal

A Flask-based platform for secure application onboarding, shipment lifecycle management, and audit-ready authentication logging.

---

## Tech Stack

- **Backend** — Python, Flask
- **Database** — MySQL 8.0
- **Email** — Flask-Mail (Gmail SMTP)
- **PDF Extraction** — pdfplumber
- **Frontend** — Bootstrap 5, Inter font, Font Awesome
- **Containerisation** — Docker, Docker Compose
- **Testing** — pytest

---

## Project Structure

```
deliveryhub/
├── app_manager.py              # Main Flask app — admin UI + JSON API
├── docshipp.py                 # Shipment validation & creation API
├── db.py                       # MySQL connection helper
├── notifications.py            # Email notification service
├── pdf_extractor.py            # FedEx label PDF extraction module
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env                        # Environment variables (not committed)
├── sql/
│   ├── schema.sql              # Database schema
│   └── seed_test.sql           # Test seed data
├── templates/
│   ├── admin_dashboard.html
│   ├── applications.html
│   ├── auth_logs.html
│   ├── create_application.html
│   ├── create_shipment.html
│   ├── create_shipment_from_text.html
│   ├── create_shipment_from_pdf.html   # NEW — PDF extraction UI
│   ├── application_created.html        # NEW — one-time credential display
│   ├── edit_shipment.html
│   ├── shipments.html
│   ├── upload_label.html
│   └── email_templates/
│       ├── onboarding_email.md
│       ├── renewal_email.md
│       ├── inactive_email.md
│       └── business_report_email.md
└── uploads/                    # Uploaded PDF labels (auto-created)
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/internship_deliveryhub.git
cd internship_deliveryhub
```

### 2. Create `.env` file

```env
APP_ENV=dev

DB_HOST=db
DB_USER=root
DB_PASSWORD=root
DB_NAME=deliveryhub_dev

MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password

COMPANY_NAME=DeliveryHub
COMPANY_WEBSITE=http://localhost:5001
COMPANY_PHONE=+1-800-000-0000
SUPPORT_EMAIL=support@deliveryhub.com
```

### 3. Run with Docker

```bash
docker compose up --build
```

### 4. Access the admin portal

```
http://localhost:5001/admin-ui
```

---

## Admin Portal Pages

| URL | Description |
|-----|-------------|
| `/admin-ui` | Dashboard — stats overview |
| `/admin-ui/applications` | Manage client applications |
| `/admin-ui/create-application` | Onboard a new client |
| `/admin-ui/auth-logs` | Authentication audit trail |
| `/admin-ui/shipments` | All shipment requests |
| `/admin-ui/create-shipment` | Create shipment manually |
| `/admin-ui/create-shipment-from-text` | Create from pasted text |
| `/admin-ui/create-shipment-from-pdf` | **NEW** — Create from FedEx label PDF |
| `/admin-ui/upload-label` | Upload PDF label to shipment |
| `/admin-ui/edit-shipment/<id>` | Edit shipment service type |
| `/admin-ui/view-label/<id>` | View uploaded label PDF |

---

## JSON API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/admin/create-application` | Create application (returns token once) |
| GET  | `/admin/applications` | List all applications |
| PUT  | `/admin/update-status` | Enable / disable application |
| PUT  | `/admin/update-expiry` | Update application expiry date |
| GET  | `/admin/auth-logs` | View authentication logs |
| POST | `/validate-auth` | Validate application ID + token |
| POST | `/signin` | Sign in with application credentials |
| POST | `/validate` | Validate text input (docshipp) |
| POST | `/generate-label` | Create shipment via API |
| POST | `/admin-ui/extract-label` | **NEW** — Extract fields from PDF label |

---

## Bugs Fixed

| # | File | Bug |
|---|------|-----|
| 1 | `docshipp.py` | `"to_phone"` string literal instead of `data["to_phone"]` — receiver phone was always saved as the text "to_phone" |
| 2 | `app_manager.py` | Receiver address INSERT had 7 columns but only 6 placeholders — crashed every shipment creation |
| 3 | `app_manager.py` | `SELECT id` should be `SELECT application_id` in create-shipment GET handler |
| 4 | `app_manager.py` | Integration test was mocking `send_application_credentials` which doesn't exist — should be `send_onboarding_email` |
| 5 | `notifications.py` | `send_report_email` read from `app.config` keys that were never set — now uses module-level env vars |
| 6 | `create_shipment.html` | `app.id` used in dropdown — should be `app.application_id` |
| 7 | `create_shipment.html` | `customers` variable used in template but never passed from backend |
| 8 | `inactive_email.md` | `inactive_reason` was hardcoded text instead of `{{ inactive_reason }}` template variable |
| 9 | `shipments.html` | Links to `/view-label/` and `/edit-shipment/` routes that didn't exist in backend |
| 10 | `seed_test.sql` | `customers` INSERT missing required `email` column |
| 11 | `seed_test.sql` | `address_line` column used but schema defines `address_line1` |

---

## New Features Added

- **Application → Shipment linking** — `application_id` column added to `shipments` table; every shipment is now assigned to an application
- **DeliveryHub default application** — seeded as the system default, pre-selected in all shipment forms
- **Service type dropdown** — shipment service changed from free text to predefined options (Express, Economy, Priority, etc.)
- **Shipment confirmation email** — sender receives an email after shipment is created
- **PDF label extraction** — upload any FedEx international label PDF; all sender/receiver fields are extracted and pre-filled automatically
- **`/view-label/<id>` route** — admin can view uploaded label PDFs directly from the shipments table
- **`/edit-shipment/<id>` route** — admin can edit shipment service type
- **`application_created.html`** — proper one-time credential display page replacing raw HTML string
- **Live search** on applications, auth logs, and shipments tables
- **Auth log filter** — filter by Success / Failure status

---

## Testing

```bash
pytest test_app.py test_auth.py test_integration_workflow.py -v
```

---

## Security

- Application tokens are hashed with bcrypt before storage — plaintext never persists in the database
- Tokens are shown only once on creation
- Every API auth attempt is logged with timestamp, status, reason, and IP address
- Expired or inactive applications are rejected at every endpoint
- PDF label upload validates `.pdf` extension before saving
