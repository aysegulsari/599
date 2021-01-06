from django.contrib import admin
from django.urls import path,include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.HomePage.as_view(), name="home"),
    path('accounts/', include("accounts.urls", namespace="accounts")),
    path('accounts/', include("django.contrib.auth.urls")),
    path('thanks/', views.ThanksPage.as_view(), name="thanks"),
    path('test/', views.TestPage.as_view(), name="test"),
    path('reports/',include("reports.urls", namespace="reports")),
]
