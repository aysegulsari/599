from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)
from django.shortcuts import render
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from . import models as myModels
from django.http import JsonResponse
import tweepy
from . import utils
from textblob import TextBlob
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

nltk.downloader.download('vader_lexicon')


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
    language = request.POST.get('language')
    if not count:
        count = "100"
    start_date = request.POST.get('start')
    end_date = request.POST.get('end')
    limit = int(count)
    # print("s", start_date)
    # print("e", end_date)

    i = 0
    data = []
    api = utils.get_api()
    for tweet in tweepy.Cursor(api.search, q=keyword + ' -filter:retweets', count=count, lang=language,
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
                                   tweet_count=count, language=language)
    reports = myModels.Report.objects.filter(name=name, user=user)
    if len(reports) == 0:  # report could not saved
        temp_result = {'data': "report could not saved"}
        return JsonResponse(temp_result, safe=False)

    id_context_dict = utils.get_id_context_dict(data)

    for t in data:
        context = id_context_dict[str(t.id)]

        analysis = TextBlob(t.full_text)
        score = SentimentIntensityAnalyzer().polarity_scores(t.full_text)
        neg = score['neg']
        neu = score['neu']
        pos = score['pos']
        comp = score['compound']
        polarity = analysis.sentiment.polarity
        sentiment = 'neutral'

        if neg > pos:
            sentiment = 'negative'
        elif pos > neg:
            sentiment = 'positive'

        myModels.Tweet.objects.create(report=reports[0], tweet_id=t.id, creation_date=t.created_at,
                                      tweet_text=t.full_text, category=context, neutral=neu, negative=neg, positive=pos,
                                      compound=comp, sentiment=sentiment)

    tweets = myModels.Tweet.objects.filter(report=reports[0])
    tweets_t = [
        [tw.tweet_id, tw.creation_date, tw.tweet_text, tw.category, tw.sentiment, tw.neutral, tw.negative, tw.positive,
         tw.compound, tw.sentiment] for tw in tweets]
    tweets_t = {'data': tweets_t}

    # print(id_context_dict)
    # tweets_t = {'data': id_context_dict}

    return JsonResponse(tweets_t, safe=False)


def report_collect_tweet(request):
    return render(request, 'reports/report_collect_tweet.html')


@csrf_exempt
def get_tweets(request):
    name = request.POST.get('name')
    reports = myModels.Report.objects.filter(name=name, user=request.user)
    print("rep ", len(reports))
    tweets = myModels.Tweet.objects.filter(report=reports[0])
    print("twe ", tweets.count)
    tweets_t = [
        [tw.tweet_id, tw.creation_date, tw.tweet_text, tw.category, tw.sentiment, tw.neutral, tw.negative, tw.positive,
         tw.compound, tw.sentiment] for tw in tweets]
    tweets_t = {'data': tweets_t}

    # print(id_context_dict)
    # tweets_t = {'data': id_context_dict}

    return JsonResponse(tweets_t, safe=False)
