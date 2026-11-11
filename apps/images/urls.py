from django.urls import path

from apps.images.views import ImageListView

urlpatterns = [
    path('images/', ImageListView.as_view(), name='image-list'),
]
