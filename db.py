import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables from .env file
# Example:
# DB_HOST=localhost
# DB_USER=root
# DB_PASSWORD=1234
# DB_NAME=shipment_db

load_dotenv()

def get_db_connection():
    #if database connects successfully
    try: 
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )

        if connection.is_connected():
            print("Database connected successfully")

        return connection
    #catching any mysql errors 
    # if password is wrong / DB is off / connection fails
    except Error as e:
        print("Error while connecting to MySQL:", e) #error message
        return None