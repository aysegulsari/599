from dotenv import load_dotenv
import os
import tweepy
from . import models as myModels
from . import helper
import pandas as pd
from textblob import TextBlob
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import requests
import re

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


def get_tweets_via_tweepy(report, keyword, language, start_date, end_date, count):
    api = get_api()
    query = get_query(keyword, language)
    limit = int(count)
    i = 0
    data = []

    for t in tweepy.Cursor(api.search, q=query, count=count,
                           tweet_mode='extended', since=start_date,
                           until=end_date).items():
        data.append(t)
        i += 1
        if i >= limit:
            break
        else:
            pass

    context_dict, entity_dict = get_id_context_dict(data)
    already_added_tweets = myModels.Tweet.objects.filter(report=report)
    for t in data:
        if already_added_tweets.filter(tweet_id=t.id).exists():
            print("tweet already exists")
            continue
        if t.lang == language:
            sentiment = get_sentiment(t.full_text)
            tweet = myModels.Tweet.objects.create(report=report, tweet_id=t.id, creation_date=t.created_at,
                                                  tweet_text=t.full_text, lang=t.lang,
                                                  retweet_count=t.retweet_count,
                                                  like_count=t.favorite_count, sentiment=sentiment)
            hashtag_string = ''
            if str(t.id) in entity_dict:
                entity = entity_dict[str(t.id)]
                # print(entity)
                if "hashtags" in entity:
                    for h in entity["hashtags"]:
                        if 'tag' in h:
                            myModels.Hashtag.objects.create(tweet=tweet, tag=h["tag"])
                            if hashtag_string == '':
                                hashtag_string = hashtag_string + h['tag']
                            else:
                                hashtag_string = hashtag_string + " , " + h['tag']

            tweet.hashtag_string = hashtag_string

            context_domain = []
            context_entity = []
            context_domain_string = ''
            context_entity_string = ''
            if str(t.id) in context_dict:
                context = context_dict[str(t.id)]
                # print(context)
                for c in context:
                    # print(c)
                    if 'domain' in c and 'entity' in c and 'description' in c["domain"]:
                        myModels.ContextAnnotation.objects.create(tweet=tweet,
                                                                  domain_id=c["domain"]["id"],
                                                                  domain_name=c["domain"]["name"],
                                                                  domain_desc=c["domain"]["description"],
                                                                  entity_id=c["entity"]["id"],
                                                                  entity_name=c["entity"]["name"])

                        if c["domain"]["name"] not in context_domain:
                            context_domain.append(c['domain']['name'])
                            if context_domain_string == '':
                                context_domain_string = context_domain_string + c["domain"]["name"]
                            else:
                                context_domain_string = context_domain_string + " , " + c["domain"]["name"]

                        if c["entity"]["name"] not in context_entity:
                            if context_entity_string == '':
                                context_entity_string = context_entity_string + c["entity"]["name"]
                            else:
                                context_entity_string = context_entity_string + " , " + c["entity"]["name"]

            tweet.context_domain_string = context_domain_string
            tweet.context_entity_string = context_entity_string
            tweet.save(update_fields=['hashtag_string', 'context_domain_string', 'context_entity_string'])


def get_sentiment(text):
    analysis = TextBlob(text)
    cleaned_text = clean_text(text)
    score = SentimentIntensityAnalyzer().polarity_scores(cleaned_text)
    neg = score['neg']
    pos = score['pos']
    sentiment = 'neutral'

    if neg > pos:
        sentiment = 'negative'
    elif pos > neg:
        sentiment = 'positive'

    return sentiment


def clean_text(tweet):
    tweet = tweet.lower()
    tweet = re.sub(r'@[a-z0-9_]\S+', '', tweet)  # get rid of everything after @ symbol
    tweet = re.sub(r'#[a-z0-9_]\S+', '', tweet)  # get rid of everything after # symbol
    tweet = re.sub(r'&[a-z0-9_]\S+', '', tweet)  # get rid of everything after & symbol
    tweet = re.sub(r'[?!.+,;$%&"]+', '', tweet)  # get rid of every symbol in the tweet
    tweet = re.sub(r'rt[\s]+', '', tweet)  # get rid of retweet symbol rt
    tweet = re.sub(r'\d+', '', tweet)
    tweet = re.sub(r'[^\w]', ' ', tweet)
    tweet = re.sub(r'\$', '', tweet)
    tweet = re.sub(r'rt+', '', tweet)  # get rid of retweet symbol rt
    tweet = re.sub(r'https?:?\/\/\S+', '', tweet)  # get rid of links

    return tweet


def get_id_context_dict(data):
    id_context_dict = {}
    id_entity_dict = {}
    if len(data) < 100:
        id_list = ""
        for tw in data:
            if id_list == '':
                id_list = str(tw.id)
            else:
                id_list = id_list + "," + str(tw.id)
        response = get_context_response(id_list)
        get_context(response, id_context_dict, id_entity_dict)
    else:
        for ctr in range(len(data) // 100):
            id_list = ""
            for tw in data[(ctr * 100):(ctr + 1) * 100]:
                if id_list == '':
                    id_list = str(tw.id)
                else:
                    id_list = id_list + "," + str(tw.id)
            response = get_context_response(id_list)
            get_context(response, id_context_dict, id_entity_dict)
    return id_context_dict, id_entity_dict


def get_context_response(ids):
    tweet_fields = "tweet.fields=context_annotations,entities"
    # print(ids)
    url = "https://api.twitter.com/2/tweets?ids={}&{}".format(
        ids,
        tweet_fields
    )
    response = requests.request("GET", url, headers=headers)
    return response


def get_context(response, id_context_dict, id_entity_dict):
    json_response = response.json()
    if 'data' in json_response:
        for tw in json_response['data']:
            if 'context_annotations' in tw:
                id_context_dict[tw['id']] = tw['context_annotations']
            if 'entities' in tw:
                id_entity_dict[tw['id']] = tw['entities']
    return id_context_dict, id_entity_dict
