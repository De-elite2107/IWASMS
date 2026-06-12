"""
Dashboard app — Stats and reporting API views
"""
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Q
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.events.models import SecurityEvent
from apps.alerts.models import SecurityAlert


class OverviewStatsView(APIView):
    """GET /api/v1/stats/overview/ — KPI card data"""

    def get(self, request):
        now = timezone.now()
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(hours=24)

        events_last_hour = SecurityEvent.objects.filter(timestamp__gte=last_hour)
        events_last_24h = SecurityEvent.objects.filter(timestamp__gte=last_24h)

        total = events_last_24h.count() or 1
        attacks = events_last_24h.filter(is_attack=True).count()
        normal = events_last_24h.filter(is_attack=False).count()

        false_positives = SecurityAlert.objects.filter(
            status='false_positive',
            created_at__gte=last_24h
        ).count()

        avg_latency = events_last_hour.aggregate(avg=Avg('processing_latency_ms'))['avg'] or 0

        attack_type_distribution = list(
            events_last_24h.filter(is_attack=True)
            .values('attack_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        severity_breakdown = dict(
            events_last_24h.filter(is_attack=True)
            .values('severity')
            .annotate(count=Count('id'))
            .values_list('severity', 'count')
        )

        # Top attacking IPs
        top_ips = list(
            events_last_24h.filter(is_attack=True)
            .values('source_ip')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        data = {
            'active_alerts': SecurityAlert.objects.filter(status='open').count(),
            'events_last_24h': total,
            'attacks_last_24h': attacks,
            'normal_last_24h': normal,
            'detection_rate': round((attacks / total) * 100, 2),
            'false_positive_rate': round((false_positives / max(attacks, 1)) * 100, 2),
            'avg_latency_ms': round(avg_latency, 2),
            'attack_type_distribution': attack_type_distribution,
            'severity_breakdown': severity_breakdown,
            'top_attacking_ips': top_ips,
            'generated_at': now.isoformat(),
        }
        return Response({'data': data, 'meta': {}, 'error': None})


class ThreatTimelineView(APIView):
    """GET /api/v1/stats/timeline/?hours=24 — time-series for chart"""

    def get(self, request):
        hours = int(request.query_params.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)

        from django.db.models.functions import TruncHour
        events = (
            SecurityEvent.objects
            .filter(timestamp__gte=since)
            .annotate(hour=TruncHour('timestamp'))
            .values('hour')
            .annotate(
                total=Count('id'),
                attacks=Count('id', filter=Q(is_attack=True)),
                normal=Count('id', filter=Q(is_attack=False)),
            )
            .order_by('hour')
        )

        timeline = [
            {
                'hour': e['hour'].isoformat(),
                'total': e['total'],
                'attacks': e['attacks'],
                'normal': e['normal'],
                'detection_rate': round(e['attacks'] / max(e['total'], 1) * 100, 1),
            }
            for e in events
        ]

        return Response({'data': {'timeline': timeline, 'hours': hours}, 'meta': {}, 'error': None})


class SeverityBreakdownView(APIView):
    """GET /api/v1/stats/severity/ — severity breakdown"""

    def get(self, request):
        hours = int(request.query_params.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)
        data = list(
            SecurityEvent.objects
            .filter(timestamp__gte=since, is_attack=True)
            .values('severity')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        return Response({'data': data, 'meta': {}, 'error': None})
