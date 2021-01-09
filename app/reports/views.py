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

load_dotenv()

CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")


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
    keyword = request.POST.get('keyword')
    count = request.POST.get('count')
    if not count:
        count="100"
    start_date = request.POST.get('start')
    end_date = request.POST.get('end')
    print(count)
    limit = int(count)
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)
    '''
    api = twitter.Api(consumer_key=CONSUMER_KEY,consumer_secret=CONSUMER_SECRET,
            access_token_key=ACCESS_TOKEN, access_token_secret=ACCESS_TOKEN_SECRET)
    data = api.GetSearch(term=keyword,count=100, lang='en', since=start_date, until=end_date, include_entities=False,
                         result_type='recent')
    '''
    i = 0
    data = []
    for tweet in tweepy.Cursor(api.search, q=keyword+' -filter:retweets', count=count, lang='tr', tweet_mode='extended', since=start_date,
                               until=end_date).items():
        data.append(tweet)
        i += 1
        if i >= limit:
            break
        else:
            pass

    tweets_text = [[1, str(tw.created_at), tw.full_text] for tw in data]
    tweets_text = {'data': tweets_text}
    print(tweets_text)
    return JsonResponse(tweets_text, safe=False)


def report_collect_tweet(request):
    return render(request, 'reports/report_collect_tweet.html')
