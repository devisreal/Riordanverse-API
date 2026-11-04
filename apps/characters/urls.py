from django.urls import path

from apps.characters.views import (
    CharacterDetailView,
    CharacterImageListView,
    CharacterListView,
    CharacterPowerListView,
    CharacterQuestListView,
    CharacterWeaponListView,
)

urlpatterns = [
    path('characters/', CharacterListView.as_view(), name='character-list'),
    path('characters/<slug:slug>/', CharacterDetailView.as_view(), name='character-detail'),
    path(
        'characters/<slug:slug>/images/',
        CharacterImageListView.as_view(),
        name='character-image-list',
    ),
    path(
        'characters/<slug:slug>/powers/',
        CharacterPowerListView.as_view(),
        name='character-power-list',
    ),
    path(
        'characters/<slug:slug>/weapons/',
        CharacterWeaponListView.as_view(),
        name='character-weapon-list',
    ),
    path(
        'characters/<slug:slug>/quests/',
        CharacterQuestListView.as_view(),
        name='character-quest-list',
    ),
]
