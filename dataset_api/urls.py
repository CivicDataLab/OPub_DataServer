from django.urls import path
from .search import facets

urlpatterns = [
    path('facets/', facets)
]