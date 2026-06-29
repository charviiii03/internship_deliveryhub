# db.py
# Database connection helper.
# Reads credentials from .env file.
#
# Required .env keys:
#   DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """
    Returns a MySQL connection, or None if connection fails.
    Always call cursor.close() and connection.close() after use.
    """
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            connection_timeout=10,
        )

        if connection.is_connected():
            return connection

    except Error as e:
        print(f"[DB] Connection failed: {e}")

    return None
