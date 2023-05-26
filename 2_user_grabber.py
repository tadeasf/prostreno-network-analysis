import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User
from config import BEARER_TOKEN, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
import time

# Set up the database engine and session
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
Session = sessionmaker(bind=engine)
session = Session()

# Define the URL and headers for the Twitter API request
url = "https://api.twitter.com/2/users"
headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json",
}

# Fetch all users from the database
users = session.query(User).all()

# For each user, fetch their data from the Twitter API
for user in users:
    params = {
        "ids": user.id,
        "user.fields": "description,location,public_metrics,created_at",
    }
    response = requests.get(url, headers=headers, params=params)
    # If the status code is 429, wait for a minute before making another request
    if response.status_code == 429:
        print("Rate limit reached. Waiting for 60 seconds.")
        time.sleep(60)
        continue

    # If the status code is not 200, print the error and break the loop
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")
        break
    data = response.json()

    # Update the user data in the database
    if "data" in data:
        for user_data in data["data"]:
            user.description = user_data.get("description")
            user.location = user_data.get("location")
            user.followers_count = user_data["public_metrics"]["followers_count"]
            user.following_count = user_data["public_metrics"]["following_count"]
            user.tweet_count = user_data["public_metrics"]["tweet_count"]
            user.created_at = user_data["created_at"]

    # Wait for a second before making another request
    time.sleep(0.5)

# Commit the changes and close the session
session.commit()
session.close()
