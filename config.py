from dotenv import load_dotenv
import os

load_dotenv()

# Get the API key from the .env file
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
API_KEY2 = os.getenv("API_KEY2")
API_SECRET2 = os.getenv("API_SECRET2")
BEARER_TOKEN2 = os.getenv("BEARER_TOKEN2")
API_KEY3 = os.getenv("API_KEY3")
API_SECRET3 = os.getenv("API_SECRET3")
BEARER_TOKEN3 = os.getenv("BEARER_TOKEN3")
# Get the database credentials from the .env file
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
# Get Neo4j credentials from the .env file
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
# Get DeepL credentials from the .env file
DEEPL_API = os.getenv("DEEPL_API")
