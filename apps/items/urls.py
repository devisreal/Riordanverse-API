from django.urls import path

from apps.items.views import WeaponDetailView, WeaponImageListView, WeaponListView

urlpatterns = [
    path('weapons/', WeaponListView.as_view(), name='weapon-list'),
    path('weapons/<slug:slug>/', WeaponDetailView.as_view(), name='weapon-detail'),
    path(
        'weapons/<slug:slug>/images/',
        WeaponImageListView.as_view(),
        name='weapon-image-list',
    ),
]
