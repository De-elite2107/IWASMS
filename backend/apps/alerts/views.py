"""
Alerts app — API Views
"""
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import SecurityAlert
from .serializers import SecurityAlertSerializer
from apps.core.pagination import StandardResultsSetPagination


class SecurityAlertListView(generics.ListAPIView):
    queryset = SecurityAlert.objects.select_related('event', 'assigned_to').order_by('-created_at')
    serializer_class = SecurityAlertSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['status', 'severity']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'severity', 'status']
    pagination_class = StandardResultsSetPagination


class SecurityAlertDetailView(generics.RetrieveUpdateAPIView):
    queryset = SecurityAlert.objects.all()
    serializer_class = SecurityAlertSerializer
    lookup_field = 'id'


class ResolveAlertView(APIView):
    """POST /api/v1/alerts/{id}/resolve/"""

    def post(self, request, id):
        try:
            alert = SecurityAlert.objects.get(id=id)
        except SecurityAlert.DoesNotExist:
            return Response(
                {'data': None, 'meta': {}, 'error': 'Alert not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        notes = request.data.get('notes', '')
        alert.resolve(user=request.user, notes=notes)
        return Response(
            {'data': SecurityAlertSerializer(alert).data, 'meta': {}, 'error': None}
        )


class FalsePositiveAlertView(APIView):
    """POST /api/v1/alerts/{id}/false-positive/"""

    def post(self, request, id):
        try:
            alert = SecurityAlert.objects.get(id=id)
        except SecurityAlert.DoesNotExist:
            return Response(
                {'data': None, 'meta': {}, 'error': 'Alert not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        notes = request.data.get('notes', '')
        alert.mark_false_positive(user=request.user, notes=notes)
        return Response(
            {'data': SecurityAlertSerializer(alert).data, 'meta': {}, 'error': None}
        )
