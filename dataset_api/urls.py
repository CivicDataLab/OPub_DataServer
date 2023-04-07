from django.urls import path

from .search import facets, organization_search, more_like_this

urlpatterns = [
    path('facets/', facets),
    # path('facets/<str:query_string>', facets),
    path('search/organizations', organization_search),
    path('likethis/', more_like_this),
]