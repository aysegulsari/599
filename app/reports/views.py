from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin
)

from django.shortcuts import render
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from . import models
from django.http import JsonResponse
import twitter

CONSUMER_KEY = "sJJJUWkvfvpZYcbY0buMRYup7"
CONSUMER_SECRET = "iDQB0WGuOsY7ITZCYwZEk2o7a2kxiSKn6kFg3NZFO4ca11LoYA"
ACCESS_TOKEN = "184983841-Cg8ps0f6pp98lsQRwennlwhilmHpMFQp2TUuciH1"
ACCESS_TOKEN_SECRET = "an8rfv4cyuSLCCaUqfU3zy8RRS55hmGHUvim1FGDJkQlk"


class CreateReport(LoginRequiredMixin, generic.CreateView):
    fields = ("name", "description")
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


class SingleReport(generic.DetailView):
    model = models.Report


class ListReports(generic.ListView):
    model = models.Report


def report_collect_tweet(request):
    return render(request, 'reports/report_collect_tweet.html')


@csrf_exempt
def collect_tweets(request):
    keyword = request.POST.get('keyword')
    start_date = request.POST.get('start')
    end_date = request.POST.get('end')
    api = twitter.Api(consumer_key=CONSUMER_KEY,
                      consumer_secret=CONSUMER_SECRET,
                      access_token_key=ACCESS_TOKEN,
                      access_token_secret=ACCESS_TOKEN_SECRET)
    data = api.GetSearch(term=keyword, count=100, lang='en', since=start_date, until=end_date, include_entities=False,
                         result_type='recent')
    tweets_text = [[tw.id, tw.created_at, tw.text] for tw in data]
    tweets_text = {'data': tweets_text}

    return JsonResponse(tweets_text, safe=False)
