"""
Top-level classify endpoint: POST /api/v1/classify/
Per Section 3.8.2 of the thesis.
"""
from django.urls import path
from .views import ClassifyRequestView

urlpatterns = [
    path('', ClassifyRequestView.as_view(), name='classify-request'),
]
