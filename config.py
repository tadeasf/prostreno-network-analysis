from dotenv import load_dotenv
import os

load_dotenv()

# Get the API key from the .env file
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")

# Get the database credentials from the .env file
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
