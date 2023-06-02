from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from models import Base, User, Tweet, Topic, TweetTopic, UserTopic
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_NAME

# Define the database connection URL
database_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Create the SQLAlchemy engine
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

# Create the new tables
Base.metadata.create_all(
    engine, tables=[Topic.__table__, TweetTopic.__table__, UserTopic.__table__]
)

# Fetch all unique topics from tweets
stmt = session.query(Tweet.topic).distinct()
result = session.execute(stmt)
all_topics = set()
for i, row in enumerate(result):
    try:
        topics = [topic.strip() for topic in row[0].split(",")]
        for topic in topics:
            if topic:
                all_topics.add(topic)
    except AttributeError:
        pass

    # Print progress every 100 rows
    if i > 0 and i % 100 == 0:
        print(f"Processed {i} rows")

# Populate the 'topics' table with unique topics
for i, topic in enumerate(all_topics):
    topic_obj = session.query(Topic).filter(Topic.topic == topic).first()
    if not topic_obj:
        try:
            session.add(Topic(topic=topic))
        except IntegrityError:
            # Handle potential race condition if another process/thread added the topic concurrently
            session.rollback()

    # Print progress every 100 topics
    if i > 0 and i % 100 == 0:
        print(f"Processed {i} topics")

session.commit()

# For each tweet, assign each topic to the tweet
stmt = session.query(Tweet.id, Tweet.topic)
result = session.execute(stmt)
tweet_topics = []
topics_cache = {}

for i, row in enumerate(result):
    try:
        if row.topic:
            topics = [topic.strip() for topic in row.topic.split(",")]
            for topic in topics:
                if topic:
                    topic_id = topics_cache.get(topic)
                    if topic_id is None:
                        topic_obj = (
                            session.query(Topic.id).filter(Topic.topic == topic).first()
                        )
                        if topic_obj:
                            topic_id = topic_obj.id
                            topics_cache[topic] = topic_id
                    if topic_id:
                        tweet_topics.append({"tweet_id": row.id, "topic_id": topic_id})
    except AttributeError:
        pass

    # Print progress every 100 rows
    if i > 0 and i % 100 == 0:
        print(f"Processed {i} rows")

# Bulk insert the tweet topics
if tweet_topics:
    session.bulk_insert_mappings(TweetTopic, tweet_topics)
    session.commit()

# For each user, compute the weight of each topic they interacted with
stmt = text(
    """
    SELECT
        users.id AS user_id,
        topics.id AS topic_id,
        COUNT(DISTINCT tweets.id) AS tweet_count
    FROM
        users
    JOIN
        tweets ON users.id = tweets.author_id
    JOIN
        tweet_topics ON tweets.id = tweet_topics.tweet_id
    JOIN
        topics ON tweet_topics.topic_id = topics.id
    GROUP BY
        users.id, topics.id
"""
)
result = session.execute(stmt)
user_topics = []
for i, row in enumerate(result):
    try:
        tweet_count = row.tweet_count

        # Assign the weight based on the number of times the user tweeted about the topic
        weight = tweet_count

        user_topics.append(
            {"user_id": row.user_id, "topic_id": row.topic_id, "weight": weight}
        )
    except AttributeError:
        pass

    # Print progress every 100 rows
    if i > 0 and i % 100 == 0:
        print(f"Processed {i} rows")

# Bulk insert the user topics
if user_topics:
    session.bulk_insert_mappings(UserTopic, user_topics)
    session.commit()


session.close()
