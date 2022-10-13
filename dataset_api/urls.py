from django.urls import path

from . import organization_logo
from .search import facets, search, more_like_this

urlpatterns = [
    path('facets/', facets),
    # path('facets/<str:query_string>', facets),
    path('search/', search),
    path('likethis/', more_like_this),
    path('logo/<int:organization_id>/', organization_logo.logo),
]