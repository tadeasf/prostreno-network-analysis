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

# Create the tables in the database
Base.metadata.create_all(engine)

# Define the URL and headers for the Twitter API request
headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json",
}

# Fetch all users from the database
users = session.query(User).all()
total_users = len(users)

# For each user, fetch their tweets from the Twitter API
for i, user in enumerate(users, start=1):
    start_time = time.time()
    url = f"https://api.twitter.com/2/users/{user.id}/tweets"
    params = {
        "tweet.fields": "created_at,public_metrics",
        "max_results": 100,
    }
    while True:
        response = requests.get(url, headers=headers, params=params)
        # If the status code is 429, wait for 15 minutes before making another request
        if response.status_code == 429:
            print("Rate limit reached. Waiting for 15 minutes.")
            time.sleep(900)  # 15 minutes
            continue

        # If the status code is not 200, print the error and break the loop
        if response.status_code != 200:
            print(f"Error: {response.status_code}, {response.text}")
            break
        data = response.json()

        # For each tweet, store it in the database
        if "data" in data:
            for tweet_data in data["data"]:
                # Check if the tweet already exists in the database
                existing_tweet = session.query(Tweet).get(tweet_data["id"])
                if existing_tweet is None:
                    # Check if the required fields are present in the tweet data
                    if all(
                        field in tweet_data for field in ["id", "text", "created_at"]
                    ):
                        tweet = Tweet(
                            id=tweet_data["id"],
                            text=tweet_data["text"],
                            created_at=tweet_data["created_at"],
                            author_id=user.id,
                        )
                        session.add(tweet)
                    else:
                        print(f"Missing required field(s) in tweet {tweet_data['id']}.")
                else:
                    # just continue if the tweet already exists
                    continue

        # If there's a next_token in the response, use it in the next request
        if "meta" in data and "next_token" in data["meta"]:
            params["pagination_token"] = data["meta"]["next_token"]
        else:
            break

        # Wait for a second before making another request
        time.sleep(1)

    # Commit the changes for each user
    session.commit()

    # Print progress
    elapsed_time = time.time() - start_time
    remaining_users = total_users - i
    estimated_time = elapsed_time * remaining_users
    print(
        f"Processed user {user.id} ({i}/{total_users}). Estimated time remaining: {estimated_time/60:.2f} minutes."
    )

# Close the session
session.close()
