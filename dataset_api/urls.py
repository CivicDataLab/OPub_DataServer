from django.urls import path
from .search import facets

urlpatterns = [
    path('facets/', facets),
    path('facets/<str:query_string>', facets)
]