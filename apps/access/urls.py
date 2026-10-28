from django.urls import path

from apps.access.views import RequestKeyView, RevokeAPIKeyView, VerifyKeyView

urlpatterns = [
    path('request-key/', RequestKeyView.as_view(), name='request-api-key'),
    path('verify-key/', VerifyKeyView.as_view(), name='verify-api-key'),
    path('revoke-key/', RevokeAPIKeyView.as_view(), name='revoke-api-key'),
]
