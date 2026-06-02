
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

# Security Enhancements

Implemented:

- Application authentication
- Password hashing
- Expiry validation
- Active/Inactive controls
- Authentication logging
- Input validation

Planned:

- JWT Authentication
- HTTPS/TLS via Nginx
- Rate Limiting
- Docker Deployment
- Production Monitoring

---

# Future Improvements

- Dockerization
- Docker Compose setup
- HTTPS using Nginx
- JWT Authorization
- Rate Limiting
- Advanced Input Validation
- Linux Deployment Scripts
- Production Deployment
- Monitoring Dashboard

---

# Scripts

### Database Setup

```bash
./setup_db.sh
```

### Future Scripts

```bash
install.sh

start.sh
```

---

# Tech Stack

- Python
- Flask
- MariaDB
- MySQL Connector
- Pytest
- Docker (Planned)
- Linux
- Flask-Mail
- python-dotenv

