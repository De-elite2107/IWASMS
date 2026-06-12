"""
Tests: Feature extractor correctness
"""
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_engine.features import HTTPFeatureExtractor, shannon_entropy


class TestHTTPFeatureExtractor:
    def setup_method(self):
        self.extractor = HTTPFeatureExtractor()

    def _normal_request(self):
        return {
            'method': 'GET',
            'url': '/api/products?id=42',
            'headers': {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'},
            'body': '',
            'source_ip': '192.168.1.100',
        }

    def _sql_request(self):
        return {
            'method': 'GET',
            'url': "/api/users?id=1 UNION SELECT username,password FROM users--",
            'headers': {'User-Agent': 'sqlmap/1.7'},
            'body': '',
            'source_ip': '10.0.0.1',
        }

    def test_returns_77_features(self):
        features = self.extractor.extract(self._normal_request())
        assert features.shape == (77,), f"Expected 77 features, got {features.shape}"

    def test_all_finite(self):
        features = self.extractor.extract(self._sql_request())
        assert np.all(np.isfinite(features)), "Some features are not finite"
        assert not np.any(np.isnan(features)), "NaN in features"

    def test_sql_features_detected(self):
        normal = self.extractor.extract(self._normal_request())
        sql = self.extractor.extract(self._sql_request())
        # Semantic group (indices 37-54) should have higher counts for SQL request
        sql_semantic = sql[37:45]  # SQL keyword counts
        normal_semantic = normal[37:45]
        assert sql_semantic.sum() > normal_semantic.sum(), "SQL keywords not detected"

    def test_suspicious_ua_detected(self):
        req = self._sql_request()  # user_agent = 'sqlmap/1.7'
        features = self.extractor.extract(req)
        # has_suspicious_user_agent is at index 75 (behavioural)
        assert features[75] == 1.0, f"Suspicious UA not flagged, got {features[75]}"

    def test_shannon_entropy(self):
        assert shannon_entropy('') == 0.0
        assert shannon_entropy('aaa') == 0.0
        entropy = shannon_entropy('Hello, World!')
        assert 0 < entropy < 5

    def test_normal_request_low_special_chars(self):
        normal = self.extractor.extract(self._normal_request())
        special_char_ratio = normal[6]  # index 6: special_char_ratio
        assert special_char_ratio < 0.3, f"Normal request has too many special chars: {special_char_ratio}"

    def test_xss_detection(self):
        xss_req = {
            'method': 'GET',
            'url': '/search?q=<script>alert(document.cookie)</script>',
            'headers': {},
            'body': '',
            'source_ip': '10.0.0.2',
        }
        features = self.extractor.extract(xss_req)
        # XSS indicators at indices 45-50 (in semantic group)
        xss_features = features[45:51]
        assert xss_features.sum() > 0, "XSS indicators not detected"

    def test_empty_request(self):
        empty = {'method': 'GET', 'url': '/', 'headers': {}, 'body': '', 'source_ip': '127.0.0.1'}
        features = self.extractor.extract(empty)
        assert features.shape == (77,)
        assert np.all(np.isfinite(features))
