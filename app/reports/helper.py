import pandas as pd
from . import models as myModels

time_slots = ["00:00-03:00", "03:00-06:00",
              "06:00-09:00", "09:00-12:00",
              "12:00-15:00", "15:00-18:00",
              "18:00-21:00", "21:00-23:59"]

starts = {"00:00-03:00": "T00:00:00.000Z", "03:00-06:00": "T03:00:00.000Z",
          "06:00-09:00": "T06:00:00.000Z", "09:00-12:00": "T09:00:00.000Z",
          "12:00-15:00": "T12:00:00.000Z", "15:00-18:00": "T15:00:00.000Z",
          "18:00-21:00": "T18:00:00.000Z", "21:00-23:59": "T21:00:00.000Z"}

ends = {"00:00-03:00": "T02:59:59.000Z", "03:00-06:00": "T05:59:59.000Z",
        "06:00-09:00": "T05:59:59.000Z", "09:00-12:00": "T11:59:59.000Z",
        "12:00-15:00": "T14:59:59.000Z", "15:00-18:00": "T17:59:59.000Z",
        "18:00-21:00": "T20:59:59.000Z", "21:00-23:59": "T23:59:59.000Z"}


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
    response = ""  # requests.request("GET", url, headers=headers)
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


def get_tweets_via_api(report, keyword, language, start_date, end_date, include_hashtags):
    date_list = pd.date_range(start_date, end_date)
    total_tweet_count_report = 0;
    i = 0

    while i < len(date_list):
        for time_slot in time_slots:
            start = date_list[i].strftime("%Y-%m-%d") + starts[time_slot]
            end = date_list[i].strftime("%Y-%m-%d") + ends[time_slot]
            total_tweet_count_report = total_tweet_count_report + collect_tweet_for_interval(report, keyword,
                                                                                             language, start,
                                                                                             end, include_hashtags)
        i = i + 1

    report.tweet_count = total_tweet_count_report
    report.save(update_fields=['tweet_count'])


def collect_tweet_for_interval(report, keyword, language, start_date, end_date, include_hashtags):
    print("language", language)

    query = ""  # get_query(keyword, include_hashtags, language)

    url = "https://api.twitter.com/2/tweets/search/recent?query=" + query + "&start_time=" + start_date + \
          "&end_time=" + end_date + "&max_results=100&place.fields=country&tweet.fields=id,text,context_annotations,created_at,lang,entities,public_metrics"

    print(url)
    response = ""  # requests.request("GET", url, headers=headers)
    # print(headers)

    tweets = response.json()
    print(tweets)
    count = 0
    if 'data' in tweets:
        count = len(tweets['data'])
        print("count", count)
        # store_tweets(tweets['data'], language, report)
    return count


def store_tweets(tweets, language, report):
    for t in tweets:
        print("----------------")
        # print(t['text'])
        # sentiment = get_sentiment(t['text'])
        if t.lang == language:
            tweet = myModels.Tweet.objects.create(report=report, tweet_id=t.id, creation_date=t.created_at,
                                                  tweet_text=t.full_text, lang=t.lang,
                                                  retweet_count=t.retweet_count,
                                                  like_count=t.favorite_count)
