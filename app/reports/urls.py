from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ListReports.as_view(), name="all"),
    path('collect', views.report_collect_tweet, name='report_collect_tweet'),
    path('ajax/collect', views.collect_tweets, name='collect_tweets'),
    path('ajax/createreport', views.create_report, name='create_report'),
    path('ajax/get', views.get_tweets, name='get_tweets'),
    path('network/<int:pk>', views.get_network_chart, name='get_network_chart'),
    path('ajax/analyze', views.analyze_tweets, name='analyze_tweets'),
    path('ajax/draw', views.draw_charts, name='draw_charts'),
    path("details/in/<slug>/", views.SingleReport.as_view(), name="single"),
    path('report/<int:pk>', views.ReportDetailView.as_view(), name='report_detail'),
]