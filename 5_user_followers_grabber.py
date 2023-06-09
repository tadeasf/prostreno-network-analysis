import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Follower
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

# Initialize the start time
start_time = time.time()

# Put all the bearer tokens in a list
bearer_tokens = [BEARER_TOKEN, BEARER_TOKEN2, BEARER_TOKEN3]

# Initialize a counter to keep track of the current token
current_token = 0

# Define your escalating timeout durations (in seconds)
timeouts = [5, 10, 30, 60, 5 * 60, 10 * 60, 15 * 60]

# Initialize a counter for the current timeout
current_timeout = 0

# For each user, fetch their followers from the Twitter API
for i, user in enumerate(users, start=1):
    url = f"https://api.twitter.com/2/users/{user.id}/followers"
    params = {
        "max_results": 100,
    }
    while True:
        # Use the current token for the request
        headers = {
            "Authorization": f"Bearer {bearer_tokens[current_token]}",
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers, params=params)
        # If the status code is 429, switch to the next token
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

        data = response.json()

        # For each follower, store it in the database
        # Reset the timeout counter after successful data retrieval and processing
        current_timeout = 0
        if "data" in data:
            for follower_data in data["data"]:
                follower = Follower(
                    follower_id=follower_data["id"],
                    user_id=user.id,
                )
                session.add(follower)

        # If there's a next_token in the response, use it in the next request
        if "meta" in data and "next_token" in data["meta"]:
            params["pagination_token"] = data["meta"]["next_token"]
        else:
            break

        # Calculate elapsed time and estimated time remaining
        elapsed_time = time.time() - start_time
        remaining_users = len(users) - i
        estimated_time_remaining = (elapsed_time / i) * remaining_users
        # convert seconds into hours, minutes, and seconds
        hours = int(estimated_time_remaining / 3600)
        minutes = int((estimated_time_remaining % 3600) / 60)
        seconds = int(estimated_time_remaining % 60)
        estimated_time_remaining = (
            f"{hours} hours, {minutes} minutes, {seconds} seconds"
        )

        print(
            f"Processed user {i} of {len(users)}. "
            f"Estimated time remaining: {estimated_time_remaining} seconds."
        )

        # Wait for a second before making another request
        time.sleep(0.1)

# Commit the changes and close the session
try:
    session.commit()
except Exception as e:
    print(e)
session.close()
