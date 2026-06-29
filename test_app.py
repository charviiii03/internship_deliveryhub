from docshipp import app


def test_valid_text():
    client = app.test_client()
    response = client.post("/validate", json={"text": "Hello123"})
    assert response.status_code == 200
    assert response.get_json()["status"] == "valid"


def test_invalid_text():
    client = app.test_client()
    response = client.post("/validate", json={"text": "Hello@123"})
    assert response.status_code == 400
    assert response.get_json()["status"] == "invalid"


def test_large_payload():
    client = app.test_client()
    response = client.post(
        "/validate",
        json={"text": "Never Gonna Give You Up Never Gonna Let You down" * 10000}
    )
    assert response.status_code == 400
    assert response.get_json()["status"] == "invalid"


def test_empty_input():
    client = app.test_client()
    response = client.post("/validate", json={"text": ""})
    assert response.status_code == 400
    assert response.get_json()["status"] == "invalid"


def test_invalid_input_type():
    client = app.test_client()
    response = client.post("/validate", json={"text": 3.141592653})
    assert response.status_code == 400
    assert response.get_json()["status"] == "invalid"


def test_various_inputs():
    client = app.test_client()
    response = client.post(
        "/validate",
        json={"text": "admіn says Héllö Wörld! 👋🏼"}
    )
    assert response.status_code == 400
    assert response.get_json()["status"] == "invalid"


def test_sql_injection():
    client = app.test_client()
    response = client.post("/validate", json={"text": "DROP TABLE users"})
    assert response.status_code == 400
    assert response.get_json()["status"] == "invalid"
