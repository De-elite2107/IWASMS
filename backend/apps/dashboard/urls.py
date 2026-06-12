from django.urls import path
from .views import OverviewStatsView, ThreatTimelineView, SeverityBreakdownView

urlpatterns = [
    path('overview/', OverviewStatsView.as_view(), name='stats-overview'),
    path('timeline/', ThreatTimelineView.as_view(), name='stats-timeline'),
    path('severity/', SeverityBreakdownView.as_view(), name='stats-severity'),
]
