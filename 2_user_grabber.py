import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User
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

# Define the URL for the Twitter API request
url = "https://api.twitter.com/2/users"

# Fetch all users from the database with NULL in the specified fields
users = session.query(User).filter(User.created_at.is_(None)).all()

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

# For each user, fetch their data from the Twitter API and update the database
for i, user in enumerate(users, start=1):
    params = {
        "ids": user.id,
        "user.fields": "description,location,public_metrics,created_at",
    }
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

    # Get the user data from the JSON response
    data = response.json()

    # Update the user data in the database
    if "data" in data:
        user_data = data["data"][0]
        user.description = user_data.get("description")
        user.location = user_data.get("location")
        user.followers_count = user_data["public_metrics"]["followers_count"]
        user.following_count = user_data["public_metrics"]["following_count"]
        user.tweet_count = user_data["public_metrics"]["tweet_count"]
        user.created_at = user_data["created_at"]

        # Reset the timeout counter after successful data retrieval and processing
        current_timeout = 0

        try:
            print(f"Processed user {i} of {len(users)}")
        except Exception as e:
            print(e)

    # Calculate elapsed time and estimated time remaining
    elapsed_time = time.time() - start_time
    remaining_users = len(users) - i
    estimated_time_remaining = (elapsed_time / i) * remaining_users
    # convert time to minutes and round to 2 decimal places
    estimated_time_remaining = round(estimated_time_remaining / 60, 2)

    print(
        f"Processed user {i} of {len(users)}. "
        f"Estimated time remaining: {estimated_time_remaining} minutes."
    )

    # Wait for a second before making another request
    time.sleep(0.1)

# Commit the changes and close the session
try:
    session.commit()
except Exception as e:
    print(e)
session.close()
