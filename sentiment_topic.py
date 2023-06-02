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
total_tweets = len(tweets)
processed_tweets = 0

# Prepare corpus for topic modeling
texts = []

# Custom preprocessors
CUSTOM_FILTERS = [
    lambda x: x.lower(),
    strip_tags,
    strip_punctuation,
    strip_numeric,
    remove_stopwords,
    strip_short,
]

# Translation progress tracking
print("Translation Progress:")
start_time = time.time()
for tweet in tweets:
    try:
        # Check if translation already exists
        if tweet.text_en_transl:
            translated_text = tweet.text_en_transl
        else:
            # Translate tweet text to English using DeepL API
            try:
                translated_text = ts.translate_text(
                    query_text=tweet.text,
                    from_language="cs",
                    to_language="en",
                    translator="deepl",
                )
            except Exception:
                # If DeepL fails, use Bing for translation
                try:
                    translated_text = ts.translate_text(
                        query_text=tweet.text,
                        from_language="cs",
                        to_language="en",
                        translator="bing",
                    )
                except Exception:
                    # If Bing also fails, use Google for translation
                    translated_text = ts.translate_text(
                        query_text=tweet.text,
                        from_language="cs",
                        to_language="en",
                        translator="google",
                    )

            # Save the translated text in the database
            tweet.text_en_transl = translated_text
            # Add preprocessed text to corpus for topic modeling
            preprocessed_text = " ".join(
                preprocess_string(translated_text, CUSTOM_FILTERS)
            )
            texts.append(preprocessed_text)
        # Perform sentiment analysis
        sentiment = analyzer.polarity_scores(translated_text)
        tweet.sentiment_analysis = sentiment["compound"]

        # Preprocess the translated text for topic modeling
        words = simple_preprocess(
            translated_text, deacc=True
        )  # deacc=True removes punctuations
        words = [lemmatizer.lemmatize(word) for word in words if word not in STOPWORDS]

        # Add preprocessed text to corpus for topic modeling
        texts.append(words)

        processed_tweets += 1
        remaining_tweets = total_tweets - processed_tweets
        elapsed_time = time.time() - start_time
        time_per_tweet = elapsed_time / processed_tweets
        remaining_time = remaining_tweets * time_per_tweet

        print(
            f"Processed tweets: {processed_tweets}/{total_tweets}, Remaining tweets: {remaining_tweets}, Estimated remaining time: {remaining_time:.2f} seconds"
        )
    except Exception as e:
        print(f"An error occurred for tweet ID {tweet.id}: {e}")

# Update the database with sentiment analysis results
session.commit()

# Perform topic modeling using BERTopic
try:
    # Initialize BERTopic
    topic_model = BERTopic(language="english")

    # Perform topic modeling
    topics, _ = topic_model.fit_transform(texts)

    # Topic recognition progress tracking
    print("Topic Recognition Progress:")
    start_time = time.time()
    for i, tweet in enumerate(tweets):
        try:
            # Assign the topic with the highest probability
            topic_id = topics[i]
            # Get the top 5 words contributing to this topic
            topic_words = topic_model.get_topic(topic_id, top_n=5)
            if topic_words:
                # Convert the topic words to a string and assign it to the tweet
                tweet.topic = ", ".join([word for word, _ in topic_words])

            processed_tweets += 1
            remaining_tweets = total_tweets - processed_tweets
            elapsed_time = time.time() - start_time
            time_per_tweet = elapsed_time / (i + 1)
            remaining_time = remaining_tweets * time_per_tweet

            print(
                f"Processed tweets: {processed_tweets}/{total_tweets}, Remaining tweets: {remaining_tweets}, Estimated remaining time: {remaining_time:.2f} seconds"
            )
        except Exception as e:
            print(
                f"An error occurred while assigning topic for tweet ID {tweet.id}: {e}"
            )

    # Update the database with topic assignments
    session.commit()
except Exception as e:
    print(f"An error occurred during topic modeling: {e}")
