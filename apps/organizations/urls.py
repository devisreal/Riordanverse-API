from django.urls import path

from apps.organizations.views import (
    CabinByNumberView,
    CabinCamperListView,
    CabinDetailView,
    CabinListView,
    FactionDetailView,
    FactionListView,
    FactionMemberListView,
)

urlpatterns = [
    path('cabins/', CabinListView.as_view(), name='cabin-list'),
    path('cabins/number/<int:number>/', CabinByNumberView.as_view(), name='cabin-by-number'),
    path('cabins/<slug:slug>/', CabinDetailView.as_view(), name='cabin-detail'),
    path(
        'cabins/<slug:slug>/campers/',
        CabinCamperListView.as_view(),
        name='cabin-camper-list',
    ),
    path('factions/', FactionListView.as_view(), name='faction-list'),
    path('factions/<slug:slug>/', FactionDetailView.as_view(), name='faction-detail'),
    path(
        'factions/<slug:slug>/members/',
        FactionMemberListView.as_view(),
        name='faction-member-list',
    ),
]
