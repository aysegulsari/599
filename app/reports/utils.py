import requests
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


def get_id_context_dict(data):
    id_context_dict = {}

    if len(data) < 100:
        id_list = ""
        for tw in data:
            if id_list == '':
                id_list = str(tw.id)
            else:
                id_list = id_list + "," + str(tw.id)
        response = get_context_response(id_list)
        get_context(response, id_context_dict)
    else:
        for ctr in range(len(data) // 100):
            id_list = ""
            for tw in data[(ctr * 100):(ctr + 1) * 100]:
                if id_list == '':
                    id_list = str(tw.id)
                else:
                    id_list = id_list + "," + str(tw.id)
            response = get_context_response(id_list)
            get_context(response, id_context_dict)
    return id_context_dict


def get_context_response(ids):
    tweet_fields = "tweet.fields=context_annotations"
    print(ids)
    url = "https://api.twitter.com/2/tweets?ids={}&{}".format(
        ids,
        tweet_fields
    )
    response = requests.request("GET", url, headers=headers)
    return response


def get_context(response, id_context_dict):
    json_response = response.json()
    list_ids = []
    for tw in json_response['data']:
        if 'context_annotations' in tw:
            for x in tw['context_annotations']:
                context_id = x['domain']['id']
                if context_id not in list_ids:
                    list_ids.append(context_id)
        print(list_ids)
        context = get_context_type(list_ids)
        id_context_dict[tw['id']] = context

    return id_context_dict


def get_context_type(list_ids):
    politics_count = 0
    entertainment_count = 0
    sports_count = 0
    technology_count = 0

    politics = [35, 38, 94]
    entertainment = [3, 4, 54, 55, 56, 58, 65, 66, 67, 84, 85, 86, 87, 89, 90, 91, 114, 117, 118, 119, 132, 139]
    sports = [6, 11, 12, 26, 27, 28, 39, 40, 60, 68, 92, 93]
    technology = [71, 78, 79, 115, 116, 120, 122, 130, 136, 137, 138]

    for context_id in list_ids:
        print('context_id', context_id)
        if int(context_id) in politics:
            politics_count = politics_count + 1
        elif int(context_id) in entertainment:
            entertainment_count = entertainment_count + 1
        elif int(context_id) in sports:
            sports_count = sports_count + 1
        elif int(context_id) in technology:
            technology_count = technology_count + 1

    maxCount = max(politics_count, entertainment_count, sports_count, technology_count)

    context = 'general'
    print("m", maxCount)
    if maxCount != 0:
        if maxCount == politics_count:
            context = 'politics'
        elif maxCount == entertainment_count:
            context = 'entertainment'
        elif maxCount == sports_count:
            context = 'sports'
        elif maxCount == technology_count:
            context = 'technology'

    return context


def get_tweets_via_api(report, keyword, language, start_date, end_date):
    date_list = pd.date_range(start_date, end_date)
    total_tweet_count_report = 0;
    i = 0
    if len(date_list) > 2:
        while i < len(date_list) - 1:
            start = date_list[i].strftime("%Y-%m-%d") + "T00:00:00.000Z"
            end = date_list[i].strftime("%Y-%m-%d") + "T08:00:00.000Z"
            collect_tweet_for_time_interval(report, keyword, language, start, end, total_tweet_count_report)

            start = date_list[i].strftime("%Y-%m-%d") + "T08:00:00.000Z"
            end = date_list[i].strftime("%Y-%m-%d") + "T12:00:00.000Z"
            collect_tweet_for_time_interval(report, keyword, language, start, end, total_tweet_count_report)

            start = date_list[i].strftime("%Y-%m-%d") + "T12:00:00.000Z"
            end = date_list[i].strftime("%Y-%m-%d") + "T18:00:00.000Z"
            collect_tweet_for_time_interval(report, keyword, language, start, end, total_tweet_count_report)

            start = date_list[i].strftime("%Y-%m-%d") + "T18:00:00.000Z"
            end = date_list[i + 1].strftime("%Y-%m-%d") + "T00:00:00.000Z"
            collect_tweet_for_time_interval(report, keyword, language, start, end, total_tweet_count_report)

            i = i + 1
    else:
        start = date_list[0].strftime("%Y-%m-%d") + "T00:00:00.000Z"
        end = date_list[0].strftime("%Y-%m-%d") + "T08:00:00.000Z"
        collect_tweet_for_time_interval(report, keyword, language, start, end, total_tweet_count_report)

        start = date_list[0].strftime("%Y-%m-%d") + "T08:00:00.000Z"
        end = date_list[0].strftime("%Y-%m-%d") + "T12:00:00.000Z"
        collect_tweet_for_time_interval(report, keyword, language, start, end, total_tweet_count_report)

        start = date_list[0].strftime("%Y-%m-%d") + "T12:00:00.000Z"
        end = date_list[0].strftime("%Y-%m-%d") + "T18:00:00.000Z"
        collect_tweet_for_time_interval(report, keyword, language, start, end, total_tweet_count_report)

        start = date_list[0].strftime("%Y-%m-%d") + "T18:00:00.000Z"
        end = date_list[1].strftime("%Y-%m-%d") + "T00:00:00.000Z"
        collect_tweet_for_time_interval(report, keyword, language, start, end, total_tweet_count_report)


def collect_tweet_for_time_interval(report, keyword, language, start_date, end_date, total_tweet_count_report):
    print("lllllllllllllllllll", language)
    query = keyword + " has:hashtags lang=" + language
    url = "https://api.twitter.com/2/tweets/search/recent?place.fields=country&query=" + query + "&start_time=" + start_date + \
          "&end_time=" + end_date + "&tweet.fields=id,text,context_annotations,created_at,lang,entities,public_metrics&max_results=100"
    print(url)
    response = requests.request("GET", url, headers=headers)
    tweets = response.json()
    count = 0
    if 'data' in tweets:
        count = len(tweets['data'])
        for t in tweets['data']:
            print("--------------------------------------------")
            print("--------------------------------------------")
            print("--------------------------------------------")
            print("--------------------------------------------")
            print(t['text'])
            sentiment = get_sentiment(t['text'])
            if t['lang'] == language:
                tweet = myModels.Tweet.objects.create(tweet_id=t['id'], creation_date=t['created_at'],
                                                      tweet_text=t['text'], sentiment=sentiment, lang=t['lang'],
                                                      retweet_count=t['public_metrics']['retweet_count'],
                                                      reply_count=t['public_metrics']['reply_count'],
                                                      like_count=t['public_metrics']['like_count'])

                tweet.reports.add(report)

                if 'entities' in t:
                    if 'hashtags' in t['entities']:
                        for hash in t['entities']['hashtags']:
                            if 'tag' in hash:
                                hashtag = myModels.Hashtag.objects.create(tweet=tweet,
                                                                          tag=hash['tag'])

                if 'context_annotations' in t:
                    for c in t['context_annotations']:
                        if 'domain' in c and 'entity' in c and 'description' in c['domain']:
                            context_annotation = myModels.ContextAnnotation.objects.create(tweet=tweet,
                                                                                           domain_id=c['domain']['id'],
                                                                                           domain_name=c['domain'][
                                                                                               'name'],
                                                                                           domain_desc=c['domain'][
                                                                                               'description'],
                                                                                           entity_id=c['entity']['id'],
                                                                                           entity_name=c['entity'][
                                                                                               'name'])
    total_tweet_count_report = count


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
