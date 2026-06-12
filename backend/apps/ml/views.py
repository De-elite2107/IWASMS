"""
ML app — API Views
"""
import logging
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MLModel
from .serializers import MLModelSerializer

logger = logging.getLogger(__name__)


class MLModelListView(generics.ListAPIView):
    queryset = MLModel.objects.all().order_by('-created_at')
    serializer_class = MLModelSerializer


class MLModelDetailView(generics.RetrieveAPIView):
    queryset = MLModel.objects.all()
    serializer_class = MLModelSerializer
    lookup_field = 'id'


class RetrainModelView(APIView):
    """POST /api/v1/models/{id}/retrain/ — queue a retraining task"""

    def post(self, request, id):
        try:
            model = MLModel.objects.get(id=id)
        except MLModel.DoesNotExist:
            return Response(
                {'data': None, 'meta': {}, 'error': 'Model not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            from apps.ml.tasks import retrain_models_task
            retrain_models_task.delay()
            return Response(
                {'data': {'message': 'Retraining queued'}, 'meta': {}, 'error': None}
            )
        except Exception as e:
            logger.error(f"Retrain error: {e}")
            return Response(
                {'data': None, 'meta': {}, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
