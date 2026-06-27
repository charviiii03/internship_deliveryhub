from docshipp import app

def test_valid_text():

    client = app.test_client() #creates a fake client/user 
    #send the post request 
    response = client.post(
        "/validate",
        json={"text": "Hello123"}
    )
    #sends data json format to validate using post 

    assert response.status_code == 200
    assert response.get_json()["status"] == "valid"


def test_invalid_text():

    client = app.test_client()
    response = client.post(
        "/validate",
        json={"text": "Hello@123"}
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "invalid"
    
# Check if the API can handle large inputs safely

def test_large_payload():

    client = app.test_client()

    response = client.post(
        "/validate",
        json={"text": "Never Gonna Give You Up! Never Gonna Let You down"*10000}  # A very large string of 10,000 characters
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "invalid"
    
# Check if the API can handle empty input
def test_empty_input():

    client = app.test_client()

    response = client.post(
        "/validate",
        json={"text": ""} #Empty input. Is it valid or invalid?
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "invalid"
    
#Check if the API can handle an invalid input type
def test_invalid_input_type():

    client = app.test_client()

    response = client.post(
        "/validate",
        json={"text": 3.141592653} #Input is an float, not a string. We can also test null, boolean, array, object, etc.
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "invalid"
    
# Check if the api can handle various inputs like accented characters, invisible Unicode, homoglyphs
def test_various_inputs():

    client = app.test_client()

    response = client.post(
        "/validate",
        json={"text": "admіn says Héllö Wörld! 👋🏼"} 
        #Input contains accented characters and emojis.
        # The i in admin is a homoglyph
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "invalid"
    
# Check if the API can handle SQL injection attempts
def test_sql_injection():

    client = app.test_client()

    response = client.post(
        "/validate",
        json={"text": "DROP TABLE users"}
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "invalid"