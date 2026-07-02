# 📦 DeliveryHub API

> **Flask-based Shipment Validation & Admin Management Platform**

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flask](https://img.shields.io/badge/Flask-Web%20API-black)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![Pytest](https://img.shields.io/badge/Tested%20with-Pytest-yellow)
![License](https://img.shields.io/badge/License-Educational-green)
![Status](https://img.shields.io/badge/Status-Active-success)

A secure, containerized backend service for validating shipments,
authenticating client applications, and managing shipment operations
through a full-featured Admin Portal.

------------------------------------------------------------------------

## 📑 Table of Contents

- [Overview](#overview)
- [Key Highlights](#key-highlights)
- [Features](#features)
- [What I Built](#what-i-built)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Database Setup](#database-setup)
  - [Environment Configuration](#environment-configuration)
  - [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [Authentication System](#authentication-system)
- [Admin Portal](#admin-portal)
- [Shipment Label Workflow](#shipment-label-workflow)
- [Notification Service](#notification-service)
- [Authentication Logs](#authentication-logs)
- [Docker Deployment](#docker-deployment)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [Security Features](#security-features)
- [Security Considerations](#security-considerations)
- [Error Handling & Status Codes](#error-handling--status-codes)
- [Project Structure](#project-structure)
- [Challenges Faced](#challenges-faced)
- [Learning Outcomes](#learning-outcomes)
- [Roadmap / Future Improvements](#roadmap--future-improvements)
- [Contributing](#contributing)
- [FAQ](#faq)
- [License](#license)
- [Contact](#contact)

------------------------------------------------------------------------

## Overview

**DeliveryHub** is a Flask-based backend microservice and Admin
Management Portal that validates shipment requests, authenticates
third-party client applications, manages shipment labels, and gives
administrators a centralized dashboard for monitoring platform
activity.

The system integrates **Flask, MySQL (MariaDB compatible), Docker,
email notifications, and Pytest** to deliver a secure, scalable
shipment management platform suitable for real-world logistics use
cases.

------------------------------------------------------------------------

## Key Highlights

| | |
|---|---|
| 🔐 **Secure by default** | Hashed tokens, audit logging, admin-only routes |
| 🐳 **Fully containerized** | One command spins up API + DB via Docker Compose |
| 📬 **Automated notifications** | Credentials & shipment updates emailed automatically |
| 🧪 **Test-covered** | Pytest suite across dev/test/prod environments |
| 🗂️ **Multi-environment ready** | Isolated `dev`, `test`, and `prod` databases |
| 📊 **Admin dashboard** | Manage applications, shipments, labels, and logs from one UI |

------------------------------------------------------------------------

## Features

- Shipment validation API
- Shipment label generation & replacement
- Third-party application authentication
- Secure token hashing (Werkzeug)
- Application onboarding with auto-generated credentials
- Authentication attempt logging (success/failure + IP)
- Docker & Docker Compose deployment
- Multi-environment database support (dev/test/prod)
- Automated testing with Pytest
- Email notification service (Flask-Mail)
- Admin dashboard with shipment & application management
- Label upload with PDF validation
- Environment-variable-based configuration
- One-command database setup automation

------------------------------------------------------------------------

## What I Built

- REST APIs for shipment validation
- Secure application authentication layer
- Admin portal for day-to-day operational management
- Shipment creation and label lifecycle management
- Authentication monitoring dashboard with filters
- Email notification service for credentials & shipment updates
- Dockerized deployment for consistent environments
- MySQL-backed persistence layer with normalized schema
- Automated testing support with sample seed data

------------------------------------------------------------------------

## Architecture

```text
                 Client Applications
                         |
                         v
                Flask API / Admin Portal
                   |              |
                   |              +------> Notification Service (Flask-Mail)
                   |
                   v
               MySQL Database
              (dev / test / prod)
```

**Request flow example — Shipment Validation:**

```text
Client App --(application_id + token)--> /api/validate
                                             |
                                    Verify token hash
                                             |
                                  Check active/expired status
                                             |
                                    Log attempt (success/fail)
                                             |
                              Return validation result (JSON)
```

------------------------------------------------------------------------

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Framework | Flask |
| Database | MySQL / MariaDB |
| ORM / Access | SQL (via `db.py`) |
| Templating | Jinja2 + Bootstrap |
| Email | Flask-Mail |
| Testing | Pytest |
| Deployment | Docker & Docker Compose |
| Auth | Werkzeug password/token hashing |

------------------------------------------------------------------------

## Getting Started

### Prerequisites

Make sure you have the following installed before you begin:

- Python **3.10+**
- pip (Python package manager)
- Docker & Docker Compose (recommended for easiest setup)
- MySQL 8.0+ / MariaDB (if running without Docker)
- A Gmail (or SMTP) account for the notification service

### Installation

```bash
git clone https://github.com/<your-username>/internship_deliveryhub.git
cd internship_deliveryhub

python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Database Setup

```bash
./setup_db.sh
```

This script creates:

- `deliveryhub_dev`
- `deliveryhub_test`
- `deliveryhub_prod`

along with all required tables and sample seed data.

> 💡 **Tip:** Re-run `setup_db.sh --reset` (if implemented) to wipe and
> rebuild tables during development.

### Environment Configuration

Create a `.env` file in the project root:

```env
APP_ENV=dev

DB_HOST=db
DB_USER=root
DB_PASSWORD=root
DB_NAME=deliveryhub_dev

MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password

SECRET_KEY=change_this_to_a_random_secret
TOKEN_EXPIRY_DAYS=30
```

> ⚠️ **Never commit your `.env` file.** Add it to `.gitignore` and use
> `.env.example` as a template for collaborators.

### Running the Application

**Locally:**

```bash
python app.py
```

**With Docker (recommended):**

```bash
docker compose up --build
```

The API will be available at `http://localhost:5000` and the Admin
Portal at `http://localhost:5000/admin` (adjust to your actual routes).

------------------------------------------------------------------------

## API Reference

> Replace endpoint paths below with your actual route names if they differ.

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/applications` | Register a new client application | Admin |
| `POST` | `/api/validate` | Validate `application_id` + `application_token` | No |
| `POST` | `/api/shipments` | Create a new shipment | App Token |
| `GET` | `/api/shipments/<id>` | Retrieve shipment details | App Token |
| `POST` | `/api/shipments/<id>/label` | Upload/replace a shipment label (PDF) | Admin |
| `GET` | `/api/shipments/<id>/label` | Download the current shipment label | App Token |
| `GET` | `/api/logs` | View authentication logs | Admin |

**Example — Validate Application**

```bash
curl -X POST http://localhost:5000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"application_id": "APP123", "application_token": "your_token"}'
```

**Example Response:**

```json
{
  "status": "success",
  "message": "Application authenticated successfully",
  "expires_at": "2026-12-01T00:00:00Z"
}
```

------------------------------------------------------------------------

## Authentication System

Every client application authenticates using:

- `application_id`
- `application_token`

**How it works:**

1. Tokens are hashed using **Werkzeug** password hashing before storage — plaintext tokens are never persisted.
2. On each request, the incoming token is verified against the stored hash.
3. Expired or inactive applications are automatically rejected.
4. Every attempt (success or failure) is written to the authentication log with a timestamp and IP address.

------------------------------------------------------------------------

## Admin Portal

The Admin UI provides:

- 📊 Dashboard (overview of applications, shipments, and activity)
- 🗂️ Applications management (create, activate/deactivate, revoke)
- 📜 Authentication Logs (filter by app, status, date)
- 🚚 Shipment Management
- ➕ Shipment Creation
- 📎 Shipment Label Upload
- 🧾 Invoice Generator

------------------------------------------------------------------------

## Shipment Label Workflow

```text
Shipment Created
        |
        v
Admin Uploads PDF
        |
        v
Label Saved (secure filename)
        |
        v
Shipment Record Updated
        |
        v
Email Sent to Receiver
```

**Features:**

- PDF-only uploads with server-side validation
- Automatic shipment association
- View uploaded labels
- Replace existing labels without breaking history
- Receiver email lookup
- Label status tracking (pending / uploaded / sent)

------------------------------------------------------------------------

## Notification Service

Automatically emails newly generated application credentials to the
registered address upon application creation, and notifies receivers
when a shipment label is issued.

**Application creation email includes:**

- Application ID
- Application Token
- Expiry Date

**Shipment label email includes:**

- Shipment ID / Tracking Number
- Label download link
- Estimated delivery info (if available)

------------------------------------------------------------------------

## Authentication Logs

Every authentication request stores:

| Field | Description |
|---|---|
| Application ID | Which app attempted authentication |
| Status | Success / Failure |
| Failure Reason | Invalid token, expired, inactive, etc. |
| Timestamp | When the attempt occurred |
| IP Address | Origin of the request |

Useful for **auditing, anomaly detection, and security monitoring**.

------------------------------------------------------------------------

## Docker Deployment

```bash
# Build and start containers
docker compose up --build

# Start in detached mode
docker compose up -d

# Stop and remove containers
docker compose down

# View running containers
docker ps

# Tail logs
docker compose logs -f
```

------------------------------------------------------------------------

## Database Schema

Core tables:

- `customers`
- `addresses`
- `shipments`
- `shipment_tracking`
- `shipment_labels`
- `applications`
- `authentication_logs`

**Simplified ER overview:**

```text
customers ──< addresses
customers ──< shipments ──< shipment_tracking
shipments ──< shipment_labels
applications ──< authentication_logs
```

------------------------------------------------------------------------

## Testing

Run the automated test suite with Pytest:

```bash
pytest -v
```

Run against a specific environment:

```bash
APP_ENV=test pytest -v
```

Generate a coverage report (if `pytest-cov` is installed):

```bash
pytest --cov=. --cov-report=term-missing
```

------------------------------------------------------------------------

## Security Features

- Password & token hashing (Werkzeug)
- Token expiry validation
- Active/inactive application controls
- Server-side input validation
- Full authentication audit trail
- Environment-variable-based secrets
- Docker container isolation

------------------------------------------------------------------------

## Security Considerations

- No plaintext token storage — ever
- SMTP credentials stored only in environment variables
- Admin-only management operations, gated by role checks
- Secure filename generation for uploaded labels
- Full authentication audit trail for forensic review
- Containerized deployment to limit blast radius
- Recommended: enable HTTPS in production (see Roadmap)

------------------------------------------------------------------------

## Error Handling & Status Codes

| Code | Meaning |
|---|---|
| `200` | Request successful |
| `201` | Resource created |
| `400` | Invalid request payload |
| `401` | Invalid or missing credentials |
| `403` | Authenticated but not authorized |
| `404` | Resource not found |
| `409` | Conflict (e.g., duplicate application) |
| `422` | Validation error (e.g., non-PDF upload) |
| `500` | Internal server error |

------------------------------------------------------------------------

## Project Structure

```text
internship_deliveryhub/
│
├── app_manager.py        # Core Flask app & route registration
├── db.py                 # Database connection & query helpers
├── notifications.py      # Email notification logic
├── Dockerfile             
├── docker-compose.yml     
├── requirements.txt
├── setup_db.sh            # Database bootstrap script
├── .env.example            
├── templates/             # Jinja2 templates for Admin Portal
├── uploads/                # Uploaded shipment labels
├── tests/                  # Pytest test suite
└── README.md
```

------------------------------------------------------------------------

## Challenges Faced

- Designing a normalized MySQL schema for shipments, labels, and auth logs
- Implementing secure, hash-based authentication end to end
- Supporting multiple isolated environments (dev/test/prod)
- Docker/Compose networking between the app and database
- Building a reliable email notification workflow
- Managing the full shipment label lifecycle (upload → replace → track)
- Building a usable Admin UI on top of Flask + Jinja2
- Debugging intermittent API/database interaction issues

------------------------------------------------------------------------

## Learning Outcomes

This project strengthened my understanding of:

- Flask application design & REST API development
- Relational database modeling in SQL
- Authentication & authorization patterns
- Docker & Docker Compose for reproducible environments
- Email integration in backend systems
- Backend debugging and root-cause analysis
- Admin dashboard / internal tooling development
- Secure software development practices

------------------------------------------------------------------------

## Roadmap / Future Improvements

- [ ] JWT-based authentication
- [ ] Role-Based Access Control (RBAC)
- [ ] HTTPS + Nginx reverse proxy
- [ ] API rate limiting
- [ ] Shipment tracking timeline (live status updates)
- [ ] Analytics dashboard with charts
- [ ] WhatsApp notification channel
- [ ] Kubernetes deployment manifests
- [ ] OpenAPI / Swagger documentation
- [ ] CI/CD pipeline (GitHub Actions)

------------------------------------------------------------------------

## Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

Please make sure tests pass (`pytest -v`) before submitting a PR.

------------------------------------------------------------------------

## FAQ

**Q: Can I use PostgreSQL instead of MySQL?**
A: Not out of the box — the queries in `db.py` target MySQL/MariaDB syntax. Migrating would require adapting the data-access layer.

**Q: How do I reset a forgotten admin password?**
A: Update the corresponding record directly in the `applications`/admin table, or re-run the seed script if in a dev environment.

**Q: Why was my label upload rejected?**
A: Only PDF files are accepted for shipment labels; other formats return a `422` validation error.

------------------------------------------------------------------------

## License

This project is intended for **educational, internship, and portfolio
purposes**.

------------------------------------------------------------------------

## Contact

For questions, suggestions, or collaboration opportunities, feel free
to open an issue or reach out via GitHub.

------------------------------------------------------------------------

**DeliveryHub** — a production-style backend project demonstrating
secure application onboarding, shipment validation, authentication,
shipment label management, email notifications, Docker deployment,
and a modern Flask-based Admin Management Portal. It showcases backend
engineering, database design, authentication, containerization, and
full-stack administrative workflows in a single project.