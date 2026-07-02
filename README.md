# DeliveryHub API

## Overview

DeliveryHub is a Flask-based microservice that validates shipment requests and manages third-party application access through secure authentication and authorization mechanisms.

The project includes:

- Input validation APIs
- Shipment label request processing
- MariaDB database integration
- Application authentication
- Admin management APIs
- Authentication logging
- Automated testing using Pytest

---

## Features

- Text validation API
- Shipment label generation API
- MariaDB database integration
- Application-based authentication
- Secure token hashing
- Application expiry validation
- Admin application onboarding
- Application status management
- Authentication logging
- Multi-environment database support
- Automated testing using Pytest
- Database setup automation
- Error handling and validation
- Email notification service
- Automated credential delivery
- Environment variable configuration

---

## Project Architecture

```text
Client
   |
   v
Flask API Service
   |
   +-------> Notification Service
   |
   v
MariaDB Database
```

### Communication Flow

```text
Client ---> Flask API

Flask API ---> Validation Logic

Flask API ---> MariaDB

MariaDB ---> Flask API

Flask API ---> JSON Response

Flask API ---> Client
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/your-username/internship_deliveryhub.git

cd internship_deliveryhub
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Database Setup

Run:

```bash
./setup_db.sh
```

This script:

- Creates development database
- Creates test database
- Creates production database
- Creates required tables
- Loads sample test data

---

## Environment Configuration

The application supports multiple environments.

```bash
APP_ENV=dev
APP_ENV=test
APP_ENV=production
```

Supported Databases:

| Environment | Database |
|------------|----------|
| Development | deliveryhub_dev |
| Testing | deliveryhub_test |
| Production | deliveryhub_prod |

---

## Running the Application

Start Flask server:

```bash
python app.py
```

Server runs at:

```text
http://127.0.0.1:5000
```

---

# API Endpoints

## Validate Text

### Endpoint

```http
POST /validate
```

### Request

```json
{
    "text": "Hello123"
}
```

### Success Response

```json
{
    "status": "valid"
}
```

### Invalid Response

```json
{
    "status": "invalid",
    "reason": "Special characters found"
}
```

---

## Generate Shipment Label

### Endpoint

```http
POST /generate-label
```

### Required Fields

```json
{
    "from_name": "Sender Name",
    "from_address": "Sender Address",
    "from_phone": "1234567890",
    "to_name": "Receiver Name",
    "to_address": "Receiver Address",
    "to_phone": "0987654321",
    "service": "FedEx Envelope International Priority"
}
```

### Success Response

```json
{
    "status": "valid"
}
```

### Invalid Response

```json
{
    "status": "invalid",
    "reason": "Required field missing"
}
```

---

# Authentication System

Every application must authenticate before accessing protected APIs.

Authentication uses:

- application_id
- application_token

Similar to a username/password system.

---

## Applications Table

Stores:

| Column | Description |
|----------|-------------|
| application_id | Unique application identifier |
| application_token | Hashed application token |
| application_name | Name of application |
| user_email | Owner email |
| expiry_date | Expiry date |
| is_active | Active/Inactive status |

---

## Secure Token Storage

Application tokens are never stored in plain text.

Tokens are hashed using:

```python
generate_password_hash()
```

Verification uses:

```python
check_password_hash()
```

This prevents token exposure even if the database is compromised.

---

## Sign In

### Endpoint

```http
POST /signin
```

### Request

```json
{
    "application_id": "your_application_id",
    "application_token": "your_application_token"
}
```

### Success Response

```json
{
    "status": "valid",
    "message": "signin successful"
}
```

### Failure Response

```json
{
    "status": "invalid",
    "reason": "invalid token"
}
```

---

## Expiry Validation

Applications are valid only when:

```text
expiry_date >= current_date
```

Expired applications automatically fail authentication.

---

# Admin APIs

## Create Application

### Endpoint

```http
POST /admin/create-application
```

### Purpose

- Create new application
- Generate application ID
- Generate secure token
- Set default expiry period
- Store application details

Generated using:

```python
uuid.uuid4()
secrets.token_urlsafe()
```

---

## View Applications

### Endpoint

```http
GET /admin/applications
```

### Returns

- application_id
- application_name
- user_email
- expiry_date
- is_active

Example Response:

```json
{
    "status": "success",
    "applications": [...]
}
```

---

## Update Expiry Date

### Endpoint

```http
PUT /admin/update-expiry
```

### Purpose

- Extend validity
- Renew applications
- Modify expiry dates

---

## Update Application Status

### Endpoint

```http
PUT /admin/update-status
```

### Purpose

- Activate application
- Deactivate application

Authentication fails when:

```text
is_active = false
```

even if credentials are correct.

---
---

# Notification Service

## Purpose

Automatically notify application owners when a new application is created through the App Manager system.

The notification service sends application credentials to the registered email address after successful application creation.

---

## Trigger Event

### Endpoint

```http
POST /admin/create-application
```

### Notification Flow

```text
Admin
   |
   v
Create Application
   |
   v
Generate Application ID
   |
   v
Generate Application Token
   |
   v
Store Application Details
   |
   v
Send Email Notification
   |
   v
Application Owner
```

---

## Email Contents

The notification email contains:

- Application ID
- Application Token
- Expiry Date

Example:

```text
Application ID:
03e27fea-a515-4319-b0b1-f1ef4482453c

Application Token:
xxxxxxxxxxxxxxxxxxxxxxxx

Expiry Date:
2026-08-30
```

---

## Notification Module

Notification functionality is implemented in a dedicated module:

```text
notifications.py
```

This module is responsible for:

- Building email messages
- Sending application credentials
- Managing email delivery operations

---

## Email Configuration

SMTP settings are configured through environment variables.

```env
MAIL_USERNAME=<sender_email>
MAIL_PASSWORD=<app_password>
```

Benefits:

- Improved security
- Credentials not stored in source code
- Easier deployment across environments

---

## Libraries Used

```text
Flask-Mail
python-dotenv
```

---

## Future Notification Enhancements

Planned improvements:

- WhatsApp notifications
- Shipment request notifications
- Application expiry reminders
- Notification retry mechanism
- Admin alert notifications

---

# Authentication Logs

Authentication events are stored in:

```text
authentication_logs
```

Stored Information:

| Field | Description |
|---------|-------------|
| application_id | Application making request |
| request_time | Authentication timestamp |
| status | Success / Failure |
| reason | Failure reason |
| ip_address | Request IP |

Purpose:

- Security monitoring
- Audit trails
- Failed login tracking
- Troubleshooting

---

# Automated Testing

## Run Tests

Stop Flask server first:

```bash
CTRL + C
```

Run tests:

```bash
pytest
```

---

## Test Cases

### Valid Input

```json
{
    "text": "Hello123"
}
```

Expected:

```json
{
    "status": "valid"
}
```

---

### Invalid Input

```json
{
    "text": "Hello@123"
}
```

Expected:

```json
{
    "status": "invalid"
}
```

---

# Error Handling

Database operations include exception handling.

Example:

```python
try:
    connection = get_db_connection()
except Exception as e:
    print(e)
```

Benefits:

- Prevents crashes
- Improves reliability
- Provides meaningful error messages

---
# DeliveryHub – Admin Management Portal

## Overview

The Admin Management Portal is a web-based administration console developed for managing applications, authentication logs, shipment requests, shipment labels, and overall system monitoring.

The portal provides administrators with a centralized dashboard to monitor platform activity, onboard applications, track shipments, and manage authentication access.

---

# Admin Dashboard

The Admin Dashboard provides a centralized view of the entire system.

### Features

- Total Applications
- Valid Authentication Requests
- Invalid Authentication Requests
- Total Shipments
- Recent Activity Feed
- Quick Actions Navigation
- Shipment Summary Statistics

### Access

```text
http://localhost:5001/admin-ui
```

---

# Admin UI Features

## 1. Applications Management

### Endpoint

```text
/admin-ui/applications
```

### Capabilities

- View all registered applications
- Search applications
- View application status
- Monitor expiry dates
- Create new applications

---

## 2. Authentication Logs

### Endpoint

```text
/admin-ui/auth-logs
```

### Capabilities

- View authentication attempts
- Monitor successful logins
- Monitor failed logins
- Audit application access
- View source IP addresses

---

## 3. Shipment Management

### Endpoint

```text
/ admin-ui/shipments
```

### Capabilities

- View shipment requests
- Monitor shipment status
- Track shipment lifecycle
- View sender and receiver information
- View shipment validation results

---

## 4. Create Shipment

### Endpoint

```text
/admin-ui/create-shipment
```

### Capabilities

- Create shipment requests directly from Admin UI
- Validate sender information
- Validate receiver information
- Support India and USA shipment rules
- Automatically create shipment tracking records

### Validation Rules

#### India

| Field | Validation |
|---------|------------|
| Country Code | IN |
| Phone Code | +91 |
| Phone Length | 10 Digits |
| Postal Code | 6 Digits |

#### USA

| Field | Validation |
|---------|------------|
| Country Code | US |
| Phone Code | +1 |
| Phone Length | 10 Digits |
| Postal Code | 5 Digits |

---

## 5. Upload Label

### Endpoint

```text
/admin-ui/upload-label
```

### Capabilities

- Upload shipment labels
- Store uploaded label files
- Associate labels with shipment requests

---

# Docker Deployment

The project is fully containerized using Docker and Docker Compose.

---

## Services

### App Manager

**Container**

```text
deliveryhub_app_manager
```

### Responsibilities

- Flask API
- Admin Portal
- Application Management
- Shipment Processing
- Notification Service

---

### Database

**Container**

```text
deliveryhub_db
```

**Image**

```text
mysql:8.0
```

### Responsibilities

- Store applications
- Store shipments
- Store authentication logs
- Store shipment tracking information

---

# Docker Architecture

```text
+----------------------+
|    Admin Portal      |
|     Flask API        |
+----------+-----------+
           |
           v
+----------------------+
|    MySQL Database    |
|   deliveryhub_dev    |
+----------------------+
```

---

# Running with Docker

## Build Containers

```bash
docker compose up --build
```

## Run in Background

```bash
docker compose up -d
```

## Stop Containers

```bash
docker compose down
```

## View Running Containers

```bash
docker ps
```

## View Logs

```bash
docker compose logs -f
```

---

# Docker Environment Variables

Example:

```env
APP_ENV=dev

DB_HOST=db
DB_USER=root
DB_PASSWORD=root
DB_NAME=deliveryhub_dev

MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
```

---

# Project Structure

```text
internship_deliveryhub
│
├── app_manager.py
├── db.py
├── notifications.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
│
├── sql
│   ├── schema.sql
│   └── seed_test.sql
│
├── templates
│   ├── admin_dashboard.html
│   ├── applications.html
│   ├── auth_logs.html
│   ├── shipments.html
│   ├── create_application.html
│   ├── create_shipment.html
│   └── upload_label.html
│
├── static
│   └── logo.jpeg
│
├── uploads
│
└── tests
    ├── test_app.py
    └── test_integration.py
```

---

# Database Schema

## customers

Stores sender and receiver details.

### Fields

- customer_id
- full_name
- phone_number
- email

---

## addresses

Stores shipment address information.

### Fields

- address_id
- address_line1
- address_line2
- city
- state_name
- country
- country_code
- postal_code

---

## shipments

Stores shipment requests.

### Fields

- shipment_id
- requestid
- sender_customer_id
- receiver_customer_id
- from_address_id
- to_address_id
- service
- validation_status
- validation_reason
- state
- return_code
- return_json

---

## shipment_tracking

Stores shipment tracking updates.

### Fields

- tracking_id
- shipment_id
- current_status
- updated_time

---

## applications

Stores onboarded client applications.

### Fields

- application_id
- application_token
- application_name
- user_email
- expiry_date
- is_active
- created_at

---

## authentication_logs

Stores application authentication activity.

### Fields

- application_id
- request_time
- status
- reason
- ip_address

---

# Security Features

The following security mechanisms have been implemented:

- Application Authentication
- Token Hashing
- Password Hashing
- Expiry Validation
- Active/Inactive Controls
- Authentication Logging
- Input Validation
- Email-Based Credential Delivery
- Environment Variable Configuration
- Docker Container Isolation

---

# Future Improvements

Planned enhancements for future releases:

- JWT Authentication
- Role-Based Access Control (RBAC)
- HTTPS with Nginx
- Rate Limiting
- Shipment Status Workflow Automation
- Advanced Dashboard Analytics
- WhatsApp Notifications
- Application Expiry Reminders
- Production Monitoring
- Kubernetes Deployment

---

# Key Technologies

- Python
- Flask
- MySQL 8.0
- Docker
- Docker Compose
- HTML
- Bootstrap
- Jinja2 Templates
- SMTP Email Service
- Pytest

---

# Summary

DeliveryHub Admin Management Portal provides a complete administrative interface for:

- Application Onboarding
- Authentication Monitoring
- Shipment Creation & Tracking
- Shipment Label Management
- Email Notification Services
- Secure Application Access Control

The system is fully containerized using Docker, integrated with MySQL, secured through token-based authentication mechanisms, and designed for future scalability through Kubernetes and production-grade monitoring solutions.

