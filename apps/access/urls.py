from django.urls import path

from apps.access.views import RequestKeyView

urlpatterns = [
    path('request-key/', RequestKeyView.as_view(), name='request-api-key'),
]
