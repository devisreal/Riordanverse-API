from django.urls import path

from apps.access.views import RequestKeyView, VerifyKeyView

urlpatterns = [
    path('request-key/', RequestKeyView.as_view(), name='request-api-key'),
    path('verify-key/', VerifyKeyView.as_view(), name='verify-api-key'),
]
