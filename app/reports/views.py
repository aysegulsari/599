from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)
import pandas as pd
from django.shortcuts import render
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
import os
from . import models as myModels
from django.http import JsonResponse
import twitter
from dotenv import load_dotenv
import tweepy
import json
from django.core.serializers.json import DjangoJSONEncoder
import requests

load_dotenv()

CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)
headers = {"Authorization": "Bearer {}".format(BEARER_TOKEN)}


class CreateReport(LoginRequiredMixin, generic.CreateView):
    fields = ("name", "description")
    model = myModels.Report


class SingleReport(generic.DetailView):
    model = myModels.Report


class ListReports(generic.ListView):
    model = myModels.Report

    def get_queryset(self):
        return myModels.Report.objects.filter(user=self.request.user)


def create_report(request):
    reports = myModels.Report.objects.filter(user=request.user)
    if request.method == 'POST':
        user = request.user
        name = request.POST.get('name')
        description = request.POST.get('description')
        keyword = request.POST.get('keyword')
        if name is not None:
            reports = myModels.Report.objects.filter(name=name, user=user)
            if not reports:
                myModels.Report.objects.create(name=name, description=description, keyword=keyword, user=user)
            reports = myModels.Report.objects.filter(user=request.user)
        return render(request, 'reports/report_list.html',
                      {'object_list': reports,
                       })
    else:
        return render(request, 'reports/report_form.html')


@csrf_exempt
def collect_tweets(request):
    user = request.user
    name = request.POST.get('name')
    reports = myModels.Report.objects.filter(name=name, user=user)
    if len(reports) != 0:  # report name exists
        temp_result = {'data': "report name exists"}
        return JsonResponse(temp_result, safe=False)

    keyword = request.POST.get('keyword')
    count = request.POST.get('count')
    if not count:
        count = "100"
    start_date = request.POST.get('start')
    end_date = request.POST.get('end')
    limit = int(count)
    # print("s", start_date)
    # print("e", end_date)

    i = 0
    data = []
    for tweet in tweepy.Cursor(api.search, q=keyword + ' -filter:retweets', count=count, lang='en',
                               tweet_mode='extended', since=start_date,
                               until=end_date).items():
        data.append(tweet)

        i += 1
        if i >= limit:
            break
        else:
            pass

    if len(data) == 0:  # no tweet found
        temp_result = {'data': "no tweet"}
        return JsonResponse(temp_result, safe=False)

    time_interval = request.POST.get('start') + " / " + request.POST.get('end')
    count = len(data)

    myModels.Report.objects.create(name=name, time_interval=time_interval, keyword=keyword, user=user,
                                   tweet_count=count)
    reports = myModels.Report.objects.filter(name=name, user=user)
    if len(reports) == 0:  # report could not saved
        temp_result = {'data': "report could not saved"}
        return JsonResponse(temp_result, safe=False)

    id_context_dict = get_id_context_dict(data)

    for t in data:
        print("id", t.id)

        context = id_context_dict[str(t.id)]
        print('c', context)
        myModels.Tweet.objects.create(report=reports[0], tweet_id=t.id, creation_date=t.created_at,
                                      tweet_text=t.full_text, category=context)
    
    tweets = myModels.Tweet.objects.filter(report=reports[0])
    tweets_t = [[tw.tweet_id, tw.creation_date, tw.tweet_text, tw.category] for tw in tweets]
    tweets_t = {'data': tweets_t}


    #print(id_context_dict)
    #tweets_t = {'data': id_context_dict}

    return JsonResponse(tweets_t, safe=False)


def get_id_context_dict(data):
    id_context_dict = {}

    if (len(data) < 100):
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
    print("m",maxCount)
    if maxCount!=0:
        if maxCount == politics_count:
            context = 'politics'
        elif maxCount == entertainment_count:
            context = 'entertainment'
        elif maxCount == sports_count:
            context = 'sports'
        elif maxCount == technology_count:
            context = 'technology'

    return context


def report_collect_tweet(request):
    return render(request, 'reports/report_collect_tweet.html')
