from app_manager import app


# ----------------------------------
# VALIDATE-AUTH TESTS
# ----------------------------------

def test_validate_auth_missing_credentials():
    client = app.test_client()
    response = client.post("/validate-auth", json={})
    assert response.status_code == 401
    assert response.get_json()["status"] == "invalid"


def test_validate_auth_missing_application_id():
    client = app.test_client()
    response = client.post("/validate-auth", json={"application_token": "dummy-token"})
    assert response.status_code == 401
    assert response.get_json()["status"] == "invalid"


def test_validate_auth_missing_application_token():
    client = app.test_client()
    response = client.post("/validate-auth", json={"application_id": "dummy-id"})
    assert response.status_code == 401
    assert response.get_json()["status"] == "invalid"


def test_validate_auth_invalid_credentials():
    client = app.test_client()
    response = client.post(
        "/validate-auth",
        json={"application_id": "fake-id", "application_token": "fake-token"}
    )
    assert response.status_code == 401
    assert response.get_json()["status"] == "invalid"


# ----------------------------------
# SIGNIN TESTS
# ----------------------------------

def test_signin_missing_credentials():
    client = app.test_client()
    response = client.post("/signin", json={})
    assert response.status_code == 401
    assert response.get_json()["status"] == "invalid"


def test_signin_invalid_token():
    client = app.test_client()
    response = client.post(
        "/signin",
        json={"application_id": "fake-id", "application_token": "wrong-token"}
    )
    assert response.status_code == 401
    assert response.get_json()["status"] == "invalid"


# ----------------------------------
# ADMIN CREATE APPLICATION TEST
# ----------------------------------

def test_create_application():
    client = app.test_client()
    response = client.post(
        "/admin/create-application",
        json={"application_name": "pytest_app", "user_email": "test@example.com"}
    )
    assert response.status_code == 201
    assert response.get_json()["status"] == "success"


# ----------------------------------
# INTEGRATION TEST
# ----------------------------------

def test_application_workflow():
    client = app.test_client()

    create_response = client.post(
        "/admin/create-application",
        json={"application_name": "integration_test", "user_email": "test@example.com"}
    )
    assert create_response.status_code == 201

    data = create_response.get_json()

    validate_response = client.post(
        "/validate-auth",
        json={
            "application_id":    data["application_id"],
            "application_token": data["application_token"],
        }
    )
    assert validate_response.status_code == 200
    assert validate_response.get_json()["status"] == "valid"
