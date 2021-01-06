from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)

from django.shortcuts import render
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
import os
from . import models
from django.http import JsonResponse
import twitter
from dotenv import load_dotenv

load_dotenv()

CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")


class CreateReport(LoginRequiredMixin, generic.CreateView):
    fields = ("name", "description")
    model = models.Report


class SingleReport(generic.DetailView):
    model = models.Report


class ListReports(generic.ListView):
    model = models.Report


def create_report(request):
    reports = models.Report.objects.filter(user=request.user)
    if request.method == 'POST':
        user = request.user
        name = request.POST.get('name')
        description = request.POST.get('description')
        keyword = request.POST.get('keyword')
        if name is not None:
            reports = models.Report.objects.filter(name=name, user=user)
            if not reports:
                models.Report.objects.create(name=name, description=description, keyword=keyword, user=user)
            reports = models.Report.objects.filter(user=request.user)
        return render(request, 'reports/report_list.html',
                      {'object_list': reports,
                       })
    else:
        return render(request, 'reports/report_form.html')


@csrf_exempt
def collect_tweets(request):
    keyword = request.POST.get('keyword')
    start_date = request.POST.get('start')
    end_date = request.POST.get('end')
    count = request.POST.get('count')
    api = twitter.Api(consumer_key=CONSUMER_KEY,
                      consumer_secret=CONSUMER_SECRET,
                      access_token_key=ACCESS_TOKEN,
                      access_token_secret=ACCESS_TOKEN_SECRET)
    data = api.GetSearch(term=keyword, count=count, lang='en', since=start_date, until=end_date, include_entities=False,
                         result_type='recent')
    tweets_text = [[tw.id, tw.created_at, tw.text] for tw in data]
    tweets_text = {'data': tweets_text}

    return JsonResponse(tweets_text, safe=False)


def report_collect_tweet(request):
    return render(request, 'reports/report_collect_tweet.html')
