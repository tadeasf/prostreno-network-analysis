from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.schema import MetaData
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

Base = declarative_base()
metadata = MetaData()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String)
    description = Column(String)
    location = Column(String)
    followers_count = Column(Integer)
    following_count = Column(Integer)
    tweet_count = Column(Integer)
    created_at = Column(DateTime)

    tweets = relationship("Tweet", back_populates="user")
    following = relationship("Following", back_populates="user")
    followers = relationship("Follower", back_populates="user")


class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(String, primary_key=True)
    text = Column(String)
    text_en_transl = Column(String)  # new field
    created_at = Column(DateTime)
    author_id = Column(String, ForeignKey("users.id"))
    author_username = Column(String)
    conversation_id = Column(String)
    retweet_count = Column(Integer)
    reply_count = Column(Integer)
    like_count = Column(Integer)
    quote_count = Column(Integer)
    sentiment_analysis = Column(Float)  # new field
    topic = Column(String)  # new field

    user = relationship("User", back_populates="tweets")


class Following(Base):
    __tablename__ = "following"

    id = Column(Integer, primary_key=True, autoincrement=True)
    following_id = Column(String)
    user_id = Column(String, ForeignKey("users.id"))

    user = relationship("User", back_populates="following")


class Follower(Base):
    __tablename__ = "followers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    follower_id = Column(String)
    user_id = Column(String, ForeignKey("users.id"))

    user = relationship("User", back_populates="followers")


# Function to modify all schemas
def modify_all_schemas(database_url):
    # Create the SQLAlchemy engine
    engine = create_engine(database_url)

    # Reflect existing database schema
    metadata.reflect(bind=engine)

    # Create all pending tables and columns
    Base.metadata.create_all(engine, tables=[metadata.tables["tweets"]])

    # Close the engine connection
    engine.dispose()


# Example usage
if __name__ == "__main__":
    # Define the database connection URL
    database_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

    # Modify all schemas
    modify_all_schemas(database_url)
