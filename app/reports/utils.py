from dotenv import load_dotenv
import os
import tweepy
from . import models as myModels
import pandas as pd
from textblob import TextBlob
from nltk.sentiment.vader import SentimentIntensityAnalyzer

load_dotenv()

CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
headers = {"Authorization": "Bearer {}".format(BEARER_TOKEN)}


def get_api():
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)
    return api


def get_header():
    return headers


def get_query(keyword, language):
    query = keyword

    if language != 'all':
        query = query + " lang:" + language

    return query


def get_tweets_via_tweepy(report, keyword, language, start_date, end_date):
    api = get_api()
    count = 20
    query = get_query(keyword, language)


    total_tweet_count_report = 0;
    limit = count
    i = 0
    for t in tweepy.Cursor(api.search, q=query, count=count,
                           tweet_mode='extended', since=start_date,
                           until=end_date).items():

        if t.lang == language:
            tweet = myModels.Tweet.objects.create(report=report, tweet_id=t.id, creation_date=t.created_at,
                                                  tweet_text=t.full_text, lang=t.lang,
                                                  retweet_count=t.retweet_count,
                                                  like_count=t.favorite_count)
            total_tweet_count_report = total_tweet_count_report + 1
            print("----------------------------------")
            print("----------------------------------")
            print(t)
            print("----------------------------------")
            print("----------------------------------")

            if hasattr(t, "entities"):
                if t.entities.__contains__("hashtags"):
                    for hash in t.entities["hashtags"]:
                        if 'tag' in hash:
                            myModels.Hashtag.objects.create(tweet=tweet,
                                                            tag=hash.tag)

            if hasattr(t, "context_annotations"):
                for c in t.context_annotations:
                    if 'domain' in c and 'entity' in c and 'description' in c.domain:
                        myModels.ContextAnnotation.objects.create(tweet=tweet,
                                                                  domain_id=c.domain.id,
                                                                  domain_name=c.domain.name,
                                                                  domain_desc=c.domain.description,
                                                                  entity_id=c.entity.id,
                                                                  entity_name=c.entity.name)

        i += 1
        if i >= limit:
            break
        else:
            pass

    report.tweet_count = total_tweet_count_report
    report.save(update_fields=['tweet_count'])


def get_sentiment(text):
    analysis = TextBlob(text)
    score = SentimentIntensityAnalyzer().polarity_scores(text)
    neg = score['neg']
    pos = score['pos']
    sentiment = 'neutral'

    if neg > pos:
        sentiment = 'negative'
    elif pos > neg:
        sentiment = 'positive'

    return sentiment
