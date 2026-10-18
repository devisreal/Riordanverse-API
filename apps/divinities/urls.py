from django.urls import path

from apps.divinities.views import (
    GodChildrenListView,
    GodDetailView,
    GodImageListView,
    GodListView,
    GodWeaponListView,
    TitanDetailView,
    TitanImageListView,
    TitanListView,
)

urlpatterns = [
    path('gods/', GodListView.as_view(), name='god-list'),
    path('gods/<slug:slug>/', GodDetailView.as_view(), name='god-detail'),
    path('gods/<slug:slug>/images/', GodImageListView.as_view(), name='god-image-list'),
    path(
        'gods/<slug:slug>/children/',
        GodChildrenListView.as_view(),
        name='god-children-list',
    ),
    path(
        'gods/<slug:slug>/weapons/',
        GodWeaponListView.as_view(),
        name='god-weapon-list',
    ),
    path('titans/', TitanListView.as_view(), name='titan-list'),
    path('titans/<slug:slug>/', TitanDetailView.as_view(), name='titan-detail'),
    path('titans/<slug:slug>/images/', TitanImageListView.as_view(), name='titan-image-list'),
]
