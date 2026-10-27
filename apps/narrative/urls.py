from django.urls import path

from apps.narrative.views import (
    BookCharacterListView,
    BookDetailView,
    BookGodListView,
    BookImageListView,
    BookListView,
    BookLocationListView,
    BookMonsterListView,
    BookQuestListView,
    EventDetailView,
    EventListView,
    ProphecyDetailView,
    ProphecyListView,
    QuestDetailView,
    QuestListView,
    QuestParticipantListView,
)

urlpatterns = [
    # Books
    path('books/', BookListView.as_view(), name='book-list'),
    path('books/<slug:slug>/', BookDetailView.as_view(), name='book-detail'),
    path('books/<slug:slug>/images/', BookImageListView.as_view(), name='book-image-list'),
    # Book sub-resources (deferred from feature/book-model)
    path('books/<slug:slug>/gods/', BookGodListView.as_view(), name='book-god-list'),
    path(
        'books/<slug:slug>/characters/', BookCharacterListView.as_view(), name='book-character-list'
    ),
    path('books/<slug:slug>/monsters/', BookMonsterListView.as_view(), name='book-monster-list'),
    path('books/<slug:slug>/locations/', BookLocationListView.as_view(), name='book-location-list'),
    path('books/<slug:slug>/quests/', BookQuestListView.as_view(), name='book-quest-list'),
    # Prophecies
    path('prophecies/', ProphecyListView.as_view(), name='prophecy-list'),
    path('prophecies/<slug:slug>/', ProphecyDetailView.as_view(), name='prophecy-detail'),
    # Quests
    path('quests/', QuestListView.as_view(), name='quest-list'),
    path('quests/<slug:slug>/', QuestDetailView.as_view(), name='quest-detail'),
    path(
        'quests/<slug:slug>/participants/',
        QuestParticipantListView.as_view(),
        name='quest-participant-list',
    ),
    # Events
    path('events/', EventListView.as_view(), name='event-list'),
    path('events/<slug:slug>/', EventDetailView.as_view(), name='event-detail'),
]
