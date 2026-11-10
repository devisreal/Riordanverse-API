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
    # Documentation is public; API-data quotas apply only to the data routes.
    path('api/schema/', SpectacularAPIView.as_view(throttle_classes=[]), name='schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(
            url_name='schema', template_name='website/swagger_ui.html', throttle_classes=[]
        ),
        name='swagger-ui',
    ),
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema', throttle_classes=[]),
        name='redoc',
    ),
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
