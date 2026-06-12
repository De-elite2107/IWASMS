"""
Tests: Real-time inference singleton and heuristic fallback
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.ml.inference import InferenceService


class TestInferenceService:
    def test_singleton_behavior(self):
        s1 = InferenceService.get_instance()
        s2 = InferenceService.get_instance()
        assert s1 is s2

    def test_inference_runs_successfully(self):
        req = {
            'method': 'POST',
            'url': '/login',
            'headers': {'User-Agent': 'Mozilla/5.0'},
            'body': 'username=admin&password=or+1=1--',
            'source_ip': '127.0.0.1',
        }
        service = InferenceService.get_instance()
        res = service.classify(req)

        assert 'is_attack' in res
        assert 'attack_type' in res
        assert 'severity' in res
        assert 'confidence_score' in res
        assert 'processing_latency_ms' in res
        assert isinstance(res['is_attack'], bool)

    def test_heuristic_fallback_with_extreme_inputs(self):
        # Even if the ML model isn't trained yet or is missing,
        # the InferenceService should fall back to heuristic checks.
        sql_req = {
            'method': 'GET',
            'url': '/search?q=UNION SELECT NULL,NULL--',
            'headers': {},
            'body': '',
            'source_ip': '127.0.0.1',
        }
        service = InferenceService.get_instance()
        res = service.classify(sql_req)

        # High special characters & SQL union keywords should trigger attack label
        assert res['is_attack'] is True
        assert res['attack_type'] in ('sql_injection', 'xss', 'command_injection')
        assert res['severity'] in ('high', 'critical')
