from django.shortcuts import render
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from . import models as myModels
from django.http import JsonResponse
from . import utils
import nltk
from nltk.corpus import stopwords
nltk.downloader.download('stopwords')
stopwords = set(stopwords.words('english'))
nltk.downloader.download('vader_lexicon')
nltk.downloader.download('stopwords')


class SingleReport(generic.DetailView):
    model = myModels.Report


class ListReports(generic.ListView):
    model = myModels.Report

    def get_queryset(self):
        return myModels.Report.objects.filter(user=self.request.user)


@csrf_exempt
def create_report(request):
    user = request.user
    name = request.POST.get('name')
    keyword = request.POST.get('keyword')
    language = request.POST.get('language')
    time_interval = request.POST.get('start') + " / " + request.POST.get('end')
    myReport = ''
    reports = myModels.Report.objects.filter(name=name, user=user)
    if reports is not None and len(reports) > 0:
        myReport = reports[0]

    if myReport == '':
        myReport = myModels.Report.objects.create(name=name, time_interval=time_interval, keyword=keyword, user=user,
                                                  language=language)
    if myReport is None:  # report could not saved
        temp_result = {'data': "report could not saved"}
        return JsonResponse(temp_result, safe=False)

    return JsonResponse("report is created", safe=False)


@csrf_exempt
def collect_tweets(request):
    user = request.user
    name = request.POST.get('name')
    keyword = request.POST.get('keyword')
    language = request.POST.get('language')
    start_date = request.POST.get('start')
    end_date = request.POST.get('end')
    count = request.POST.get('count')
    myReport = ''
    reports = myModels.Report.objects.filter(name=name, user=user)
    if reports is not None and len(reports) > 0:
        myReport = reports[0]

    if myReport is None:  # report could not saved
        temp_result = {'data': "report could not saved"}
        return JsonResponse(temp_result, safe=False)

    print("starting..")
    utils.get_tweets_via_tweepy(myReport, keyword, language, start_date, end_date, count)
    print("finishing..")
    return JsonResponse(start_date, safe=False)


def report_collect_tweet(request):
    return render(request, 'reports/report_collect_tweet.html')


@csrf_exempt
def get_tweets(request):
    name = request.POST.get('name')
    reports = myModels.Report.objects.filter(name=name, user=request.user)
    tweets = myModels.Tweet.objects.filter(report=reports[0])
    myReport = reports[0]
    myReport.tweet_count = str(len(tweets))
    myReport.save(update_fields=['tweet_count'])
    tweets_t = [
        [tw.tweet_id, tw.creation_date, tw.tweet_text, tw.lang, tw.retweet_count,
         tw.like_count, tw.hashtag_string, tw.context_domain_string, tw.context_entity_string, tw.sentiment] for tw in
        tweets]
    tweets_t = {'data': tweets_t}

    return JsonResponse(tweets_t, safe=False)


@csrf_exempt
def analyze_tweets(request):
    name = request.POST.get('name')
    reports = myModels.Report.objects.filter(name=name, user=request.user)
    tweets = myModels.Tweet.objects.filter(report=reports[0])
    for tw in tweets:
        print(tw.tweet_id)
        sentiment = utils.get_sentiment(tw.tweet_text)
        tw.sentiment = sentiment
        tw.save(update_fields=['sentiment'])

    return JsonResponse('ok', safe=False)


@csrf_exempt
def draw_charts(request):
    name = request.POST.get('name')
    reports = myModels.Report.objects.filter(name=name, user=request.user)
    tweets = myModels.Tweet.objects.filter(report=reports[0])

    positive_tweet_count = len(myModels.Tweet.objects.filter(report=reports[0], sentiment="positive"))
    negative_tweet_count = len(myModels.Tweet.objects.filter(report=reports[0], sentiment="negative"))
    neutral_tweets_count = len(myModels.Tweet.objects.filter(report=reports[0], sentiment="neutral"))

    sentiment_pie_object = {'positive': positive_tweet_count,
                            'negative': negative_tweet_count,
                            'neutral': neutral_tweets_count}
    domain_objects = []
    entity_objects = []
    all_tweets = ""
    for tw in tweets:
        all_tweets = all_tweets + tw.tweet_text + " "
        sentiment = tw.sentiment
        contextAnnotations = myModels.ContextAnnotation.objects.filter(tweet=tw)
        for context in contextAnnotations:
            domain_name = context.domain_name
            entity_name = context.entity_name

            if any(x['name'] == domain_name for x in domain_objects) is False:
                domain_object = {'name': domain_name,
                                 'occurrence': 0,
                                 'values': {'positive_counts': 0, 'negative_counts': 0, 'neutral_counts': 0}}
                domain_objects.append(domain_object)

            if any(x['name'] == entity_name for x in entity_objects) is False:
                entity_object = {'name': entity_name,
                                 'occurrence': 0,
                                 'values': {'positive_counts': 0, 'negative_counts': 0, 'neutral_counts': 0}}
                entity_objects.append(entity_object)

            domain_obj = [x for x in domain_objects if x['name'] == domain_name]
            domain_obj[0]['occurrence'] = domain_obj[0]['occurrence'] + 1

            entity_obj = [x for x in entity_objects if x['name'] == entity_name]
            entity_obj[0]['occurrence'] = entity_obj[0]['occurrence'] + 1

            if sentiment == 'positive':
                domain_obj[0]['values']['positive_counts'] = domain_obj[0]['values']['positive_counts'] + 1
                entity_obj[0]['values']['positive_counts'] = entity_obj[0]['values']['positive_counts'] + 1
            elif sentiment == 'negative':
                domain_obj[0]['values']['negative_counts'] = domain_obj[0]['values']['negative_counts'] + 1
                entity_obj[0]['values']['negative_counts'] = entity_obj[0]['values']['negative_counts'] + 1
            else:
                domain_obj[0]['values']['neutral_counts'] = domain_obj[0]['values']['neutral_counts'] + 1
                entity_obj[0]['values']['neutral_counts'] = entity_obj[0]['values']['neutral_counts'] + 1

    cleaned_text = utils.clean_text(all_tweets)
    domain_names = []
    domain_positive_counts = []
    domain_negative_counts = []
    domain_neutral_counts = []

    domain_objects_sorted = sorted(domain_objects, key=lambda x: x['occurrence'], reverse=True)
    count = 0
    for o in domain_objects_sorted:
        domain_names.append(o['name'])
        domain_positive_counts.append(o['values']['positive_counts'])
        domain_negative_counts.append(o['values']['negative_counts'])
        domain_neutral_counts.append(o['values']['neutral_counts'])
        count = count + 1
        if count == 10:
            break

    entity_names = []
    entity_positive_counts = []
    entity_negative_counts = []
    entity_neutral_counts = []

    entity_objects_sorted = sorted(entity_objects, key=lambda x: x['occurrence'], reverse=True)
    count = 0
    for o in entity_objects_sorted:
        entity_names.append(o['name'])
        entity_positive_counts.append(o['values']['positive_counts'])
        entity_negative_counts.append(o['values']['negative_counts'])
        entity_neutral_counts.append(o['values']['neutral_counts'])
        count = count + 1
        if count == 10:
            break
    print('sssssssssssss',stopwords)
    sentiment_bar_object = {'domain_names': domain_names, 'domain_positive_counts': domain_positive_counts,
                            'domain_negative_counts': domain_negative_counts,
                            'domain_neutral_counts': domain_neutral_counts,
                            'entity_names': entity_names, 'entity_positive_counts': entity_positive_counts,
                            'entity_negative_counts': entity_negative_counts,
                            'entity_neutral_counts': entity_neutral_counts}

    sentiment_graph_object = {'pie_data': sentiment_pie_object, 'bar_data': sentiment_bar_object, 'text': cleaned_text,
                              'search_term': reports[0].keyword, 'stop_words': stopwords}

    return JsonResponse(sentiment_graph_object, safe=False)
