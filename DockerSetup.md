# Docker Setup and Deployment Guide

This project is fully containerized using Docker and Docker Compose, allowing any developer to set up and run the entire application without manually installing MySQL or configuring dependencies.

---

## Prerequisites

Install the following software:

- Docker Desktop
- Docker Compose

Verify installation:

```bash
docker --version
docker compose version
```

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/internship_deliveryhub.git

cd internship_deliveryhub
```

---

## Step 2: Configure Environment Variables

Create a `.env` file in the project root directory.

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

Replace the email credentials with your own SMTP credentials.

---

## Step 3: Build and Start Containers

Run the following command:

```bash
docker compose up --build
```

This command will:

- Build the Flask application image
- Pull the MySQL 8.0 image
- Create the required containers
- Configure networking between services
- Start the application and database

---

## Step 4: Verify Running Containers

Check that both containers are running:

```bash
docker ps
```

Expected containers:

```text
deliveryhub_app_manager
deliveryhub_db
```

---

## Step 5: Access the Admin Portal

Open the application in a browser:

```text
http://localhost:5001/admin-ui
```

Available modules:

```text
/admin-ui
/admin-ui/applications
/admin-ui/auth-logs
/admin-ui/shipments
/admin-ui/create-shipment
/admin-ui/upload-label
```

---

## Step 6: Monitor Logs

View logs for all services:

```bash
docker compose logs -f
```

View application logs:

```bash
docker compose logs -f app_manager
```

View database logs:

```bash
docker compose logs -f db
```

---

## Step 7: Stop the Application

```bash
docker compose down
```

---

## Step 8: Restart the Application

```bash
docker compose up -d
```

---

## Step 9: Rebuild After Code Changes

```bash
docker compose down

docker compose up --build
```

---

## Docker Deployment Architecture

```text
Developer
    |
    v
Docker Compose
    |
    +------------------+
    |                  |
    v                  v
Flask Application    MySQL Database
(App Manager)        (deliveryhub_db)
    |
    v
Admin Management Portal
```

---

## Troubleshooting

### Check Running Containers

```bash
docker ps
```

### Check All Containers (Including Stopped)

```bash
docker ps -a
```

### View Container Logs

```bash
docker compose logs -f
```

### Remove All Containers and Rebuild

```bash
docker compose down

docker compose up --build
```

### Remove Containers, Networks, and Volumes

```bash
docker compose down -v
```

---
