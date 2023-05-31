import tweepy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from models import User, Tweet, Base
from config import (
    API_KEY,
    API_SECRET,
    BEARER_TOKEN,
    API_KEY2,
    API_SECRET2,
    BEARER_TOKEN2,
    API_KEY3,
    API_SECRET3,
    BEARER_TOKEN3,
    DB_HOST,
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
)
import time

# Create a new session
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
Session = sessionmaker(bind=engine)
session = Session()

# Set up Tweepy with the API keys
auth = tweepy.AppAuthHandler(API_KEY, API_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)


# Function to download tweets
def download_tweets(user_id):
    try:
        tweets = api.user_timeline(user_id=user_id, count=200)
        for tweet in tweets:
            new_tweet = Tweet(
                id=tweet.id_str,
                text=tweet.text,
                created_at=tweet.created_at,
                author_id=tweet.author.id_str,
                author_username=tweet.author.screen_name,
                conversation_id=tweet.in_reply_to_status_id_str,
                retweet_count=tweet.retweet_count,
                like_count=tweet.favorite_count,
            )
            session.add(new_tweet)
        session.commit()
        print(f"Downloaded tweets for user {user_id}")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Failed to add tweets to database for user {user_id}: {e}")
    except Exception as e:
        print(f"Failed to get tweets for user {user_id}: {e}")


# Get all users
users = session.query(User).all()

# Download tweets for all users
start_time = time.time()
for i, user in enumerate(users):
    download_tweets(user.id)
    elapsed_time = time.time() - start_time
    remaining_time = elapsed_time / (i + 1) * (len(users) - i - 1)
    print(f"Progress: {i+1}/{len(users)}, Time remaining: {remaining_time} seconds")

print("Finished downloading tweets")
