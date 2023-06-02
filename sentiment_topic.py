import time
import translators as ts
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from gensim.utils import simple_preprocess
from gensim.parsing.preprocessing import STOPWORDS
from nltk.stem import WordNetLemmatizer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Tweet, Base
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
from bertopic import BERTopic
from gensim.parsing.preprocessing import (
    preprocess_string,
    strip_tags,
    strip_punctuation,
    strip_numeric,
    remove_stopwords,
    strip_short,
)
from concurrent.futures import ThreadPoolExecutor
import re

# Initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# Connect to the database
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Fetch all tweets
tweets = session.query(Tweet).all()
# Fetch tweets where translation didn't fail
tweets = session.query(Tweet).filter(Tweet.text_en_transl != "translation failed").all()

# Prepare corpus for topic modeling
texts = []


# Preprocessing functions
def remove_rt(text):
    """Remove the retweet symbol 'RT'."""
    return re.sub(r"\bRT\b", "", text)


def remove_links(text):
    """Remove hyperlinks from the text."""
    return re.sub(r"http\S+|www.\S+", "", text)


def remove_common_words(text):
    """Remove overly common words."""
    common_words = {"the", "a", "an", "and", "of", "is", "it", "that", "but", "this"}
    return " ".join([word for word in text.split() if word not in common_words])


# Update Custom preprocessors
CUSTOM_FILTERS = [
    lambda x: x.lower(),
    strip_tags,
    strip_punctuation,
    strip_numeric,
    remove_stopwords,
    strip_short,
    remove_rt,
    remove_links,
    remove_common_words,
]
# Translation phase
print("Translation Phase:")
for tweet in session.query(Tweet).filter(Tweet.text_en_transl.is_(None)).all():
    try:
        translated_text = ts.translate_text(
            query_text=tweet.text,
            from_language="cs",
            to_language="en",
            translator="deepl",
        )
        tweet.text_en_transl = translated_text
    except Exception:
        print(f"An error occurred during translation for tweet ID {tweet.id}")
        tweet.text_en_transl = "translation failed"

session.commit()

# Sentiment Analysis Phase
print("Sentiment Analysis Phase:")
for tweet in (
    session.query(Tweet)
    .filter(
        Tweet.sentiment_analysis.is_(None), Tweet.text_en_transl != "translation failed"
    )
    .all()
):
    try:
        sentiment = analyzer.polarity_scores(tweet.text_en_transl)
        tweet.sentiment_analysis = sentiment["compound"]
    except Exception:
        print(f"An error occurred during sentiment analysis for tweet ID {tweet.id}")

session.commit()

# Preprocess text for topic modeling
for tweet in (
    session.query(Tweet).filter(Tweet.text_en_transl != "translation failed").all()
):
    try:
        # Update this block to use custom filters
        preprocessed_text = preprocess_string(tweet.text_en_transl, CUSTOM_FILTERS)
        words = simple_preprocess(" ".join(preprocessed_text), deacc=True)
        words = [lemmatizer.lemmatize(word) for word in words if word not in STOPWORDS]
        # Join words into a sentence and append
        texts.append(" ".join(words))
    except Exception:
        print(f"An error occurred during preprocessing for tweet ID {tweet.id}")


# Topic Modeling Phase
print("Topic Modeling Phase:")
try:
    topic_model = BERTopic(language="english")
    topics, _ = topic_model.fit_transform(texts)

    # Assign topics
    def assign_topic(tweet, topic_id):
        try:
            topic_words = topic_model.get_topic(topic_id)
            if topic_words:
                tweet.topic = ", ".join([word[0] for word in topic_words])
        except Exception:
            print(
                f"An error occurred while assigning topic for tweet ID {tweet.id}. Error is: {e}"
            )

    with ThreadPoolExecutor(max_workers=10) as executor:
        for tweet, topic_id in zip(tweets, topics):
            executor.submit(assign_topic, tweet, topic_id)

except Exception as e:
    print(f"An error occurred during topic modeling: {e}")

session.commit()
