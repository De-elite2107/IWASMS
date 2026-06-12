from django.urls import path
from .views import (
    ClassifyRequestView, SecurityEventListView,
    SecurityEventDetailView, WebApplicationListCreateView,
    EventExportView,
)

urlpatterns = [
    path('classify/', ClassifyRequestView.as_view(), name='classify-request'),
    path('', SecurityEventListView.as_view(), name='event-list'),
    path('export/', EventExportView.as_view(), name='event-export'),
    path('<uuid:id>/', SecurityEventDetailView.as_view(), name='event-detail'),
    path('applications/', WebApplicationListCreateView.as_view(), name='webapp-list'),
]
