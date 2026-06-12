"""
Events app — API Views
"""
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import SecurityEvent, WebApplication
from .serializers import (
    SecurityEventSerializer, SecurityEventDetailSerializer,
    ClassifyRequestSerializer, WebApplicationSerializer
)
from apps.core.pagination import StandardResultsSetPagination

logger = logging.getLogger(__name__)


class ClassifyRequestView(APIView):
    """POST /api/v1/events/classify/ — classify an HTTP request"""
    permission_classes = []  # API-key or open for simplicity in MVP

    def post(self, request):
        serializer = ClassifyRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'data': None, 'meta': {}, 'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        req_data = serializer.validated_data
        request_dict = {
            'method': req_data['method'],
            'url': req_data['url'],
            'headers': req_data.get('headers', {}),
            'body': req_data.get('body', ''),
            'source_ip': str(req_data.get('source_ip', '127.0.0.1')),
        }

        # Classify
        from apps.ml.inference import InferenceService
        result = InferenceService.get_instance().classify(request_dict)

        # Persist SecurityEvent
        user_agent = request_dict['headers'].get('User-Agent', '')
        event = SecurityEvent.objects.create(
            source_ip=request_dict['source_ip'],
            destination_ip=str(req_data.get('destination_ip') or ''),
            http_method=request_dict['method'],
            url=request_dict['url'],
            user_agent=user_agent,
            raw_request=request_dict,
            attack_type=result['attack_type'],
            severity=result['severity'],
            is_attack=result['is_attack'],
            confidence_score=result['confidence_score'],
            processing_latency_ms=result['processing_latency_ms'],
        )

        # Persist ModelPrediction
        try:
            from apps.ml.models import MLModel, ModelPrediction
            active_model = MLModel.objects.filter(is_active=True).first()
            if active_model:
                ModelPrediction.objects.create(
                    event=event,
                    model=active_model,
                    predicted_label=result['attack_type'],
                    confidence=result['confidence_score'],
                    raw_probabilities=result.get('model_probabilities', {}),
                    inference_time_ms=result['processing_latency_ms'],
                )
        except Exception as e:
            logger.debug(f"Prediction record error: {e}")

        # Create alert if attack detected
        if result['is_attack']:
            try:
                from apps.alerts.models import SecurityAlert
                SecurityAlert.objects.get_or_create(
                    event=event,
                    defaults={
                        'title': f"{result['attack_type'].replace('_', ' ').title()} Detected",
                        'description': (
                            f"Attack type '{result['attack_type']}' detected from {request_dict['source_ip']}. "
                            f"Confidence: {result['confidence_score']:.2%}. URL: {request_dict['url']}"
                        ),
                        'severity': result['severity'],
                    }
                )
            except Exception as e:
                logger.error(f"Alert creation error: {e}")

        # Push to WebSocket
        try:
            channel_layer = get_channel_layer()
            event_data = {
                'id': str(event.id),
                'timestamp': event.timestamp.isoformat(),
                'source_ip': event.source_ip,
                'http_method': event.http_method,
                'url': event.url,
                'attack_type': event.attack_type,
                'severity': event.severity,
                'is_attack': event.is_attack,
                'confidence_score': event.confidence_score,
                'processing_latency_ms': event.processing_latency_ms,
            }
            async_to_sync(channel_layer.group_send)(
                'security_events',
                {'type': 'security_event', 'data': event_data}
            )
        except Exception as e:
            logger.debug(f"WebSocket push error: {e}")

        response_data = {
            **SecurityEventSerializer(event).data,
            'classification': result,
        }
        return Response(
            {'data': response_data, 'meta': {}, 'error': None},
            status=status.HTTP_201_CREATED
        )


class SecurityEventListView(generics.ListAPIView):
    queryset = SecurityEvent.objects.all().order_by('-timestamp')
    serializer_class = SecurityEventSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['severity', 'is_attack', 'attack_type', 'source_ip']
    search_fields = ['url', 'source_ip', 'attack_type']
    ordering_fields = ['timestamp', 'severity', 'confidence_score']
    pagination_class = StandardResultsSetPagination


class SecurityEventDetailView(generics.RetrieveAPIView):
    queryset = SecurityEvent.objects.prefetch_related('predictions').all()
    serializer_class = SecurityEventDetailSerializer
    lookup_field = 'id'


class WebApplicationListCreateView(generics.ListCreateAPIView):
    queryset = WebApplication.objects.all().order_by('-created_at')
    serializer_class = WebApplicationSerializer


class EventExportView(APIView):
    """GET /api/v1/events/export/?format=csv|json&hours=24 — Export events (FR-11)"""

    def get(self, request):
        import csv
        import io
        from django.http import HttpResponse

        export_format = request.query_params.get('format', 'json')
        hours = int(request.query_params.get('hours', 24))
        severity = request.query_params.get('severity', '')
        is_attack = request.query_params.get('is_attack', '')

        from datetime import timedelta
        since = timezone.now() - timedelta(hours=hours)

        queryset = SecurityEvent.objects.filter(timestamp__gte=since)
        if severity:
            queryset = queryset.filter(severity=severity)
        if is_attack in ('true', 'True', '1'):
            queryset = queryset.filter(is_attack=True)
        elif is_attack in ('false', 'False', '0'):
            queryset = queryset.filter(is_attack=False)

        events = queryset.order_by('-timestamp')[:10000]  # Cap at 10k for export

        if export_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                'id', 'timestamp', 'source_ip', 'http_method', 'url',
                'attack_type', 'severity', 'is_attack', 'confidence_score',
                'processing_latency_ms', 'user_agent'
            ])
            for event in events:
                writer.writerow([
                    str(event.id), event.timestamp.isoformat(), event.source_ip,
                    event.http_method, event.url, event.attack_type,
                    event.severity, event.is_attack, event.confidence_score,
                    event.processing_latency_ms, event.user_agent[:100],
                ])
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="iwasms_events_{hours}h.csv"'
            return response
        else:
            # JSON export
            data = []
            for event in events:
                data.append({
                    'id': str(event.id),
                    'timestamp': event.timestamp.isoformat(),
                    'source_ip': event.source_ip,
                    'http_method': event.http_method,
                    'url': event.url,
                    'attack_type': event.attack_type,
                    'severity': event.severity,
                    'is_attack': event.is_attack,
                    'confidence_score': event.confidence_score,
                    'processing_latency_ms': event.processing_latency_ms,
                    'user_agent': event.user_agent,
                    'raw_request': event.raw_request,
                })
            from django.http import JsonResponse
            response = JsonResponse(data, safe=False)
            response['Content-Disposition'] = f'attachment; filename="iwasms_events_{hours}h.json"'
            return response
