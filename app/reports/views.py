from django.shortcuts import render
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from . import models as myModels
from django.http import JsonResponse, HttpResponse
from . import utils
import nltk
import itertools
import matplotlib.pyplot as plt
from io import StringIO
import numpy as np
import networkx as nx
import io
import pandas as pd
import plotly.offline as py
import plotly.graph_objects as go

network = []
network_entity_count = {}

nltk.downloader.download('vader_lexicon')


class SingleReport(generic.DetailView):
    model = myModels.Report


class ListReports(generic.ListView):
    model = myModels.Report


class ReportDetailView(generic.DetailView):
    model = myModels.Report


@csrf_exempt
def create_report(request):
    user = request.user
    name = request.POST.get('name')
    keyword = request.POST.get('keyword')
    language = request.POST.get('language')
    time_interval = request.POST.get('start') + " / " + request.POST.get('end')
    myReport = ''
    reports = myModels.Report.objects.filter(name=name)
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
    reports = myModels.Report.objects.filter(name=name)
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
    reports = myModels.Report.objects.filter(name=name)
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
    reports = myModels.Report.objects.filter(name=name)
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
    keywords = request.POST.get('keyword')
    reports = myModels.Report.objects.filter(name=name)
    tweets = myModels.Tweet.objects.filter(report=reports[0] )

    positive_tweet_count = len(myModels.Tweet.objects.filter(report=reports[0], sentiment="positive"))
    negative_tweet_count = len(myModels.Tweet.objects.filter(report=reports[0], sentiment="negative"))
    neutral_tweets_count = len(myModels.Tweet.objects.filter(report=reports[0], sentiment="neutral"))

    sentiment_pie_object = {'positive': positive_tweet_count,
                            'negative': negative_tweet_count,
                            'neutral': neutral_tweets_count}
    domain_objects = []
    entity_objects = []
    all_tweets = ""

    retweet_data = []
    like_data = []

    global network
    network = []
    global network_entity_count
    network_entity_count = {}
    for tw in tweets:
        all_tweets = all_tweets + tw.tweet_text + " "
        sentiment = tw.sentiment
        retweet_data.append([tw.creation_date, tw.retweet_count])
        like_data.append([tw.creation_date, tw.like_count])
        contextAnnotations = myModels.ContextAnnotation.objects.filter(tweet=tw)
        networkItem = []
        for context in contextAnnotations:
            domain_name = context.domain_name
            entity_name = context.entity_name
            if keywords.lower() not in entity_name.lower():
                print("key", keywords, "---entity", entity_name)
                if entity_name in network_entity_count.keys():
                    network_entity_count[entity_name] = network_entity_count[entity_name] + 1
                else:
                    network_entity_count[entity_name] = 1
                if entity_name not in networkItem:
                    networkItem.append(entity_name)
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
        if len(networkItem) > 1:
            network.append(networkItem)

    network = get_combinations(network)
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
    sentiment_bar_object = {'domain_names': domain_names, 'domain_positive_counts': domain_positive_counts,
                            'domain_negative_counts': domain_negative_counts,
                            'domain_neutral_counts': domain_neutral_counts,
                            'entity_names': entity_names, 'entity_positive_counts': entity_positive_counts,
                            'entity_negative_counts': entity_negative_counts,
                            'entity_neutral_counts': entity_neutral_counts}

    like_object = {'retweet_data': retweet_data,  # [[1646333207000, 15], [1646592407000, 20]],
                   'like_data': like_data}  # [[1646333207000, 10], [1646592407000, 25]]}

    sentiment_graph_object = {'pie_data': sentiment_pie_object, 'bar_data': sentiment_bar_object, 'text': cleaned_text,
                              'search_term': reports[0].keyword, 'keywords': keywords, 'like_data': like_object,
                              'network': network, 'network_entity_count': network_entity_count}

    return JsonResponse(sentiment_graph_object, safe=False)


def get_combinations(array):
    # print(array)
    combinations = []
    for a in array:
        combList = list(itertools.combinations(a, 2))
        for c in combList:
            combinations.append(c)
    return combinations


def return_graph():
    x = np.arange(0, np.pi * 3, .1)
    y = np.sin(x)

    fig = plt.figure()
    plt.plot(x, y)

    imgdata = StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)

    data = imgdata.getvalue()
    return data


@csrf_exempt
def get_network_chart(request, *args, **kwargs):
    context = {}
    reports = myModels.Report.objects.filter(id=kwargs['pk'])
    global network
    global network_entity_count
    # print("name", reports[0].name)
    # print("network", network)
    # print("network_entity", network_entity_count)

    characters = []
    for key in network_entity_count:
        characters.append(key)
    appearances = get_empty_appearances(characters)

    for item in network:
        appearances[item[0]][item[1]].append(1)
        appearances[item[1]][item[0]].append(1)

    all_appearances = appearances
    appearance_counts = get_empty_appearances(characters, True)
    scene_counts = {}
    for character in all_appearances:
        scene_counts[character] = []
        for co_char in all_appearances[character]:
            appearance_counts[character][co_char] = len(all_appearances[character][co_char])
            scene_counts[character].extend(all_appearances[character][co_char])

        scene_counts[character] = len(set(scene_counts[character]))

    G = nx.Graph()
    for key in network_entity_count:
        G.add_node(key, size=network_entity_count[key])

    for char in appearance_counts.keys():
        for co_char in appearance_counts[char].keys():

            if appearance_counts[char][co_char] > 0:
                G.add_edge(char, co_char, weight=appearance_counts[char][co_char])

    pos_ = nx.spring_layout(G)

    edge_trace = []
    for edge in G.edges():

        if G.edges()[edge]['weight'] > 0:
            char_1 = edge[0]
            char_2 = edge[1]

            x0, y0 = pos_[char_1]
            x1, y1 = pos_[char_2]

            text = char_1 + '--' + char_2 + ': ' + str(G.edges()[edge]['weight'])

            trace = make_edge([x0, x1, None], [y0, y1, None], text,
                              0.3 * G.edges()[edge]['weight'] ** 1.75)

            edge_trace.append(trace)

    node_trace = go.Scatter(x=[],
                            y=[],
                            text=[],
                            textposition="top center",
                            textfont_size=10,
                            mode='markers+text',
                            marker=dict(color=[],
                                        size=[],
                                        line=None))
    for node in G.nodes():
        x, y = pos_[node]
        node_trace['x'] += tuple([x])
        node_trace['y'] += tuple([y])
        node_trace['marker']['color'] += tuple(['cornflowerblue'])
        node_trace['marker']['size'] += tuple([5 * G.nodes()[node]['size']])
        node_trace['text'] += tuple(['<b>' + node + '</b>'])

    layout = go.Layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    fig = go.Figure(layout=layout)

    for trace in edge_trace:
        fig.add_trace(trace)

    fig.add_trace(node_trace)

    fig.update_layout(showlegend=False)

    fig.update_xaxes(showticklabels=False)

    fig.update_yaxes(showticklabels=False)
    div = py.plot(fig, auto_open=False, output_type='div')

    '''
    fig.show()
    py.plot(fig, filename='midsummer_network.html')

    G = nx.Graph()

    # rectanle width 1.5
    G.add_node('root', time='5pm')
    G.add_node('red', time='2pm')
    G.add_node('blue', time='3pm')

    # label: to_red
    G.add_edge('root', 'red')
    # label: to_blue
    G.add_edge('root', 'blue')

    nx.draw(G)
    buf = io.BytesIO()
    plt.savefig(buf, format='svg', bbox_inches='tight')
    image_bytes = buf.getvalue().decode('utf-8')
    buf.close()
    plt.close()
     '''

    context['graph'] = div  # image_bytes
    print("hello")
    return render(request, 'reports/report_network_chart.html', context)


def get_empty_appearances(characters, num=False):
    appearances = {}
    for character in characters:
        companions = {}
        for companion in characters:
            if companion != character:

                if num:
                    companions[companion] = 0

                else:
                    companions[companion] = []
        appearances[character] = companions
    return appearances


def make_edge(x, y, text, width):
    return go.Scatter(x=x,
                      y=y,
                      line=dict(width=width,
                                color='cornflowerblue'),
                      hoverinfo='text',
                      text=([text]),
                      mode='lines')
