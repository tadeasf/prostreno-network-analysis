import time
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Tweet, User
from config import BEARER_TOKEN, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

# Set up the database engine and session
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
Session = sessionmaker(bind=engine)
session = Session()

# Create the tables in the database
Base.metadata.create_all(engine)

# Define the URL and headers for the Twitter API request
url = "https://api.twitter.com/2/tweets/search/all"
headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json",
}

# Define the time periods to fetch tweets for
time_periods = [
    ("2023-04-01T00:00:00Z", "2023-05-26T00:00:00Z"),
]

# Define the query to search for tweets containing any of the specified keywords
query = "prostřeno OR prostreno OR Prostřeno OR Prostreno OR #prostřeno OR #prostreno OR #Prostřeno OR #Prostreno"

# For each time period, fetch tweets matching the query
for i, (start_time, end_time) in enumerate(time_periods, start=1):
    start_time_period = time.time()
    next_token = None
    while True:
        params = {
            "query": query,
            "start_time": start_time,
            "end_time": end_time,
            "tweet.fields": "created_at,author_id,conversation_id,entities,public_metrics",
            "expansions": "author_id",
            "user.fields": "username,public_metrics",
            "max_results": 500,
            "pagination_token": next_token,
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

        # For each tweet, store it in the database
        if "data" in data:
            for tweet in data["data"]:
                user = next(
                    (
                        u
                        for u in data["includes"]["users"]
                        if u["id"] == tweet["author_id"]
                    ),
                    None,
                )

                # Check if the user already exists in the database
                existing_user = (
                    session.query(User).filter_by(id=tweet["author_id"]).first()
                )
                if not existing_user:
                    # Create a new User object and store it in the database
                    new_user = User(
                        id=tweet["author_id"],
                        username=user["username"] if user else None,
                    )
                    session.add(new_user)
                    session.commit()  # Commit the new User object

                new_tweet = Tweet(
                    id=tweet["id"],
                    text=tweet["text"],
                    created_at=tweet["created_at"],
                    author_id=tweet["author_id"],
                    author_username=user["username"] if user else None,
                    conversation_id=tweet["conversation_id"],
                    retweet_count=tweet["public_metrics"]["retweet_count"],
                    reply_count=tweet["public_metrics"]["reply_count"],
                    like_count=tweet["public_metrics"]["like_count"],
                    quote_count=tweet["public_metrics"]["quote_count"],
                )
                session.add(new_tweet)

        # If there's a next_token in the response, use it in the next request
        if "meta" in data and "next_token" in data["meta"]:
            next_token = data["meta"]["next_token"]
        else:
            break

        # Wait for 1 seconds before making another request
        time.sleep(1)

    end_time_period = time.time()
    elapsed_time_period = end_time_period - start_time_period
    remaining_time_periods = len(time_periods) - i
    estimated_remaining_time = remaining_time_periods * elapsed_time_period

    print(
        f"Finished time period {i} of {len(time_periods)}. "
        f"Estimated time remaining: {estimated_remaining_time} seconds."
    )

# Commit the changes and close the session
session.commit()
session.close()
