from django.urls import path
from . import api

urlpatterns = [
    path('list', api.news_list.as_view()),
]