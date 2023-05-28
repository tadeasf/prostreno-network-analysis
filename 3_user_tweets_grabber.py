import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Tweet
from config import (
    BEARER_TOKEN,
    BEARER_TOKEN2,
    BEARER_TOKEN3,
    DB_HOST,
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
)
import time

# Set up the database engine and session
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
Session = sessionmaker(bind=engine)
session = Session()

# Create the tables in the database
Base.metadata.create_all(engine)

# Fetch all users from the database
users = session.query(User).all()
total_users = len(users)

# Put all the bearer tokens in a list
bearer_tokens = [BEARER_TOKEN, BEARER_TOKEN2, BEARER_TOKEN3]

# Initialize a counter to keep track of the current token
current_token = 0

# Define your escalating timeout durations (in seconds)
timeouts = [5, 10, 30, 60, 5 * 60, 10 * 60, 15 * 60]

# Initialize a counter for the current timeout
current_timeout = 0

# For each user, fetch their tweets from the Twitter API
for i, user in enumerate(users, start=1):
    start_time = time.time()
    url = f"https://api.twitter.com/2/users/{user.id}/tweets"
    params = {
        "tweet.fields": "created_at,public_metrics",
        "max_results": 100,
    }
    while True:
        headers = {
            "Authorization": f"Bearer {bearer_tokens[current_token]}",
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers, params=params)

        # If the status code is 429, switch the token
        if response.status_code == 429:
            print(
                f"Rate limit reached. Switching tokens, committing changes, and escalating timeout: {timeouts[current_timeout]} seconds"
            )
            try:
                session.commit()
            except Exception as e:
                print(e)
            current_token = (current_token + 1) % len(bearer_tokens)

            # Use the current timeout, then increment the timeout counter (unless it's already at the end of the list)
            time.sleep(timeouts[current_timeout])
            if current_timeout < len(timeouts) - 1:
                current_timeout += 1

            continue

        # If the status code is not 200, print the error and break the loop
        if response.status_code != 200:
            print(f"Error: {response.status_code}, {response.text}")
            break
        data = response.json()

        # For each tweet, store it in the database
        # Reset the timeout counter after successful data retrieval and processing
        current_timeout = 0
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
        time.sleep(0.1)

    # Commit the changes for each user
    print(f"Committing changes for user {user.id}.")

    # Print progress
    elapsed_time = time.time() - start_time
    remaining_users = total_users - i
    estimated_time = elapsed_time * remaining_users
    print(
        f"Processed user {user.id} ({i}/{total_users}). Estimated time remaining: {estimated_time/60:.2f} minutes."
    )

# Close the session
try:
    session.commit()
except Exception as e:
    print(e)
session.close()
