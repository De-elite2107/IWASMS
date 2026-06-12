from django.urls import path
from .views import (
    SecurityAlertListView, SecurityAlertDetailView,
    ResolveAlertView, FalsePositiveAlertView
)

urlpatterns = [
    path('', SecurityAlertListView.as_view(), name='alert-list'),
    path('<uuid:id>/', SecurityAlertDetailView.as_view(), name='alert-detail'),
    path('<uuid:id>/resolve/', ResolveAlertView.as_view(), name='alert-resolve'),
    path('<uuid:id>/false-positive/', FalsePositiveAlertView.as_view(), name='alert-false-positive'),
]
