from django.urls import path

from apps.locations.views import (
    LocationDetailView,
    LocationImageListView,
    LocationListView,
)

urlpatterns = [
    path('locations/', LocationListView.as_view(), name='location-list'),
    path('locations/<slug:slug>/', LocationDetailView.as_view(), name='location-detail'),
    path(
        'locations/<slug:slug>/images/',
        LocationImageListView.as_view(),
        name='location-image-list',
    ),
]
