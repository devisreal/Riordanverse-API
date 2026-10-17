from django.urls import path

from apps.characters.views import (
    CharacterDetailView,
    CharacterImageListView,
    CharacterListView,
)

urlpatterns = [
    path('characters/', CharacterListView.as_view(), name='character-list'),
    path('characters/<slug:slug>/', CharacterDetailView.as_view(), name='character-detail'),
    path(
        'characters/<slug:slug>/images/',
        CharacterImageListView.as_view(),
        name='character-image-list',
    ),
]
