# Internship DeliveryHub

A simple Flask API that validates text input.

The API:
- returns valid if the text has no special characters
- returns invalid if special characters are present

---

# API Endpoint

POST /validate

---

# Example Valid Input

Valid because it contains only letters, numbers, and spaces.

```json
{
  "text": "Hello World 123"
}
```

Example response:

```json
{
  "status": "valid"
}
```


# Example Invalid Input

Invalid because it contains a special character (`@`).

```json
{
  "text": "Hello@World"
}
```

Example response:

```json
{
  "status": "invalid",
  "reason": "Special characters found"
}
```

---

# Project Setup

## 1. Activate virtual environment

```bash
source .venv/bin/activate
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Run Flask app

```bash
python app.py
```

---

# Testing the API

## Valid Input Test

```bash
curl -X POST http://127.0.0.1:5000/validate \
-H "Content-Type: application/json" \
-d '{"text":"Hello123"}'
```

## Invalid Input Test

```bash
curl -X POST http://127.0.0.1:5000/validate \
-H "Content-Type: application/json" \
-d '{"text":"Hello@123"}'
```

---

# Run Automated Tests

Stop the Flask server first using:

```text
Control + C
```

Then run:

```bash
pytest
```