import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Tweet
from config import BEARER_TOKEN, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
import time

# Set up the database engine and session
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
Session = sessionmaker(bind=engine)
session = Session()

# Define the URL and headers for the Twitter API request
headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json",
}

# Fetch all users from the database
users = session.query(User).all()

# For each user, fetch their tweets from the Twitter API
for user in users:
    url = f"https://api.twitter.com/2/users/{user.id}/tweets"
    params = {
        "tweet.fields": "created_at,public_metrics",
        "max_results": 100,
    }
    while True:
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

        # For each tweet, store it in the database
        if "data" in data:
            for tweet_data in data["data"]:
                tweet = Tweet(
                    id=tweet_data["id"],
                    text=tweet_data["text"],
                    created_at=tweet_data["created_at"],
                    user_id=user.id,
                )
                session.add(tweet)

        # If there's a next_token in the response, use it in the next request
        if "meta" in data and "next_token" in data["meta"]:
            params["pagination_token"] = data["meta"]["next_token"]
        else:
            break

        # Wait for a second before making another request
        time.sleep(0.5)

# Commit the changes and close the session
session.commit()
session.close()