from django.urls import path
from .views import MLModelListView, MLModelDetailView, RetrainModelView

urlpatterns = [
    path('', MLModelListView.as_view(), name='model-list'),
    path('<uuid:id>/', MLModelDetailView.as_view(), name='model-detail'),
    path('<uuid:id>/retrain/', RetrainModelView.as_view(), name='model-retrain'),
]
