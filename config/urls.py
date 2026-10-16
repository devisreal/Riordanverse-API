from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('apps.access.urls')),
    path('api/v1/', include('apps.narrative.urls')),
]
