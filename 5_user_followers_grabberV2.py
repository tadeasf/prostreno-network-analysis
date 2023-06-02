import tweepy
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

# Initialize client with the first bearer token
client = tweepy.Client(
    bearer_token=bearer_tokens[current_token],
    wait_on_rate_limit=True,
)

# For each user, fetch their followers from the Twitter API
for i, user in enumerate(users, start=1):
    try:
        followers = client.get_users_followers(user.id)

        # For each follower, store it in the database
        for follower_data in followers.data:
            follower = Follower(
                follower_id=follower_data.id,
                user_id=user.id,
            )
            session.add(follower)

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

    except Exception as e:
        if "Rate limit exceeded" in str(e):
            print(f"Rate limit reached with current token. Switching tokens.")
            current_token = (current_token + 1) % len(bearer_tokens)

            # Update the client with the new token
            client = tweepy.Client(
                bearer_token=bearer_tokens[current_token],
                wait_on_rate_limit=True,
            )
        else:
            print(f"An error occurred: {e}")

    # Commit the changes after processing each user
    session.commit()

# Close the session
session.close()
