from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


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
    created_at = Column(DateTime)
    author_id = Column(String, ForeignKey("users.id"))
    author_username = Column(String)
    conversation_id = Column(String)
    retweet_count = Column(Integer)
    reply_count = Column(Integer)
    like_count = Column(Integer)
    quote_count = Column(Integer)

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
