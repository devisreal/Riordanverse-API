from django.urls import path

from apps.bestiary.views import (
    CreatureDetailView,
    CreatureListView,
    CreatureMemberListView,
    MonsterDetailView,
    MonsterImageListView,
    MonsterListView,
)

urlpatterns = [
    path('monsters/', MonsterListView.as_view(), name='monster-list'),
    path('monsters/<slug:slug>/', MonsterDetailView.as_view(), name='monster-detail'),
    path(
        'monsters/<slug:slug>/images/',
        MonsterImageListView.as_view(),
        name='monster-image-list',
    ),
    path('creatures/', CreatureListView.as_view(), name='creature-list'),
    path('creatures/<slug:slug>/', CreatureDetailView.as_view(), name='creature-detail'),
    path(
        'creatures/<slug:slug>/members/',
        CreatureMemberListView.as_view(),
        name='creature-member-list',
    ),
]
