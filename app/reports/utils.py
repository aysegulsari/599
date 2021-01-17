import requests
from dotenv import load_dotenv
import os
import tweepy

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
