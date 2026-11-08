from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.core.views import APIDirectoryView, HealthLiveView, HealthReadyView

urlpatterns = [
    path('', include('website.urls')),
    path('health/live/', HealthLiveView.as_view(), name='health-live'),
    path('health/ready/', HealthReadyView.as_view(), name='health-ready'),
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('auth/', include('apps.access.urls')),
    path('api/v1/', APIDirectoryView.as_view(), name='api-directory'),
    path('api/v1/', include('apps.narrative.urls')),
    path('api/v1/', include('apps.divinities.urls')),
    path('api/v1/', include('apps.characters.urls')),
    path('api/v1/', include('apps.items.urls')),
    path('api/v1/', include('apps.bestiary.urls')),
    path('api/v1/', include('apps.locations.urls')),
    path('api/v1/', include('apps.organizations.urls')),
    path('api/v1/', include('apps.search.urls')),
    path('api/v1/', include('apps.images.urls')),
]

if settings.DEBUG:
    # Include django_browser_reload URLs only in DEBUG mode
    urlpatterns += [
        path('__reload__/', include('django_browser_reload.urls')),
    ]
