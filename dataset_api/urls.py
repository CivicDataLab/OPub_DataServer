from django.urls import path
from .search import facets, search

urlpatterns = [
    path('facets/', facets),
    # path('facets/<str:query_string>', facets),
    path('search/', search),
    
]