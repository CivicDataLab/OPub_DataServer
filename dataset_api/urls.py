from django.urls import path

from .search import facets, search, more_like_this

urlpatterns = [
    path('facets/', facets),
    # path('facets/<str:query_string>', facets),
    path('search/<str:index>', search),
    path('likethis/', more_like_this),
]