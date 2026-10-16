from django.urls import path

from apps.narrative.views import BookDetailView, BookImageListView, BookListView

urlpatterns = [
    path('books/', BookListView.as_view(), name='book-list'),
    path('books/<slug:slug>/', BookDetailView.as_view(), name='book-detail'),
    path('books/<slug:slug>/images/', BookImageListView.as_view(), name='book-image-list'),
]
