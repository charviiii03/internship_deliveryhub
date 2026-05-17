# Internship DeliveryHub

A simple Flask API that validates text input.

The API returns:
- valid status for normal text
- invalid status if special characters are present

## API Endpoint

POST /validate

##Example Valid Input
it is valid if no special characters say, it can contain spaces, numbers, characters 
```json
{
  "text": "Hello World 123"
}

##Example invalid input 
//invalid if there are special characters - @
{
  "text": "Hello@World"
}

to do this: installing dependencies etc
1) activate virtual environment: source .venv/bin/activate
2) pip install -r requirements.txt
3) run flask app: python app.py/python3 app.py 

in new terminal:
- to test valid input: 
//curl -X POST http://127.0.0.1:5000/validate \-H "Content-Type: application/json" \ -d '{"text":"Hello123"}'

- to test invalid input:
//curl -X POST http://127.0.0.1:5000/validate \-H "Content-Type: application/json" \ -d '{"text":"Hello@123"}'

previous terminal: control + c
pytest
