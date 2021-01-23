from django.shortcuts import render
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from . import models as myModels
from django.http import JsonResponse
from . import utils
import nltk

nltk.downloader.download('vader_lexicon')


class SingleReport(generic.DetailView):
    model = myModels.Report


class ListReports(generic.ListView):
    model = myModels.Report

    def get_queryset(self):
        return myModels.Report.objects.filter(user=self.request.user)


@csrf_exempt
def collect_tweets(request):
    user = request.user
    name = request.POST.get('name')
    reports = myModels.Report.objects.filter(name=name, user=user)
    if len(reports) != 0:  # report name exists
        temp_result = {'data': "report name exists"}
        return JsonResponse(temp_result, safe=False)

    keyword = request.POST.get('keyword')
    language = request.POST.get('language')
    start_date = request.POST.get('start')
    end_date = request.POST.get('end')
    time_interval = request.POST.get('start') + " / " + request.POST.get('end')
    include_hashtags = request.POST.get('hashtag')

    myReport = myModels.Report.objects.create(name=name, time_interval=time_interval, keyword=keyword, user=user,
                                              language=language, hashtag=include_hashtags)
    if myReport is None:  # report could not saved
        temp_result = {'data': "report could not saved"}
        return JsonResponse(temp_result, safe=False)

    #utils.get_tweets_via_api(myReport, keyword, language, start_date, end_date, include_hashtags)
    utils.get_tweets_via_tweepy(myReport, keyword, language, start_date, end_date, include_hashtags)

    tweets = myModels.Tweet.objects.filter(report=myReport)
    tweets_t = [
        [tw.tweet_id, tw.creation_date, tw.tweet_text, tw.lang, tw.retweet_count, tw.reply_count,
         tw.like_count] for tw in tweets]
    tweets_t = {'data': tweets_t}

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
        [tw.tweet_id, tw.creation_date, tw.tweet_text, tw.lang, tw.retweet_count, tw.reply_count,
         tw.like_count] for tw in tweets]
    tweets_t = {'data': tweets_t}

    return JsonResponse(tweets_t, safe=False)
