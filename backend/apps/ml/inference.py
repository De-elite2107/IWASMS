"""
IWASMS ML — Inference Service (singleton)

Loads trained model artefacts once and serves predictions.
"""
import json
import logging
import time
import pathlib

import numpy as np
import joblib

logger = logging.getLogger(__name__)

_MODELS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / 'ml_engine' / 'models'

SEVERITY_MAP = {
    'sql_injection': 'critical',
    'command_injection': 'critical',
    'xss': 'high',
    'ldap_injection': 'high',
    'xxe': 'high',
    'path_traversal': 'medium',
    'csrf': 'medium',
    'brute_force': 'high',
    'dos': 'critical',
    'normal': 'normal',
}


class InferenceService:
    _instance = None
    _models: dict = {}
    _scaler = None
    _meta_learner = None
    _label_map: dict = {}
    _loaded: bool = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load_models()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Force reload — call after retraining."""
        cls._instance = None

    def _load_models(self):
        """Load model artefacts from disk using active MLModel DB record."""
        try:
            from apps.ml.models import MLModel
            active = MLModel.objects.filter(is_active=True).order_by('-created_at').first()
            if active:
                self._load_from_db_record(active)
            else:
                self._load_latest_from_disk()
        except Exception as e:
            logger.warning(f"DB not ready, loading from disk: {e}")
            self._load_latest_from_disk()

    def _load_from_db_record(self, record):
        try:
            logger.info(f"Loading models from DB record: {record}")
            self._scaler = joblib.load(record.scaler_path)
            self._meta_learner = joblib.load(record.meta_learner_path)
            # Load individual models referenced by name in model_path (JSON dict)
            try:
                paths = json.loads(record.model_path)
            except Exception:
                paths = {}
            for name, path in paths.items():
                if pathlib.Path(path).exists():
                    self._models[name] = joblib.load(path)
            if record.label_map_path and pathlib.Path(record.label_map_path).exists():
                with open(record.label_map_path) as f:
                    self._label_map = {int(k): v for k, v in json.load(f).items()}
            else:
                self._label_map = {0: 'normal', 1: 'sql_injection', 2: 'xss',
                                   3: 'command_injection', 4: 'path_traversal',
                                   5: 'csrf', 6: 'ldap_injection'}
            self._loaded = True
            logger.info("Inference models loaded from DB record.")
        except Exception as e:
            logger.error(f"Failed to load from DB record: {e}")
            self._load_latest_from_disk()

    def _load_latest_from_disk(self):
        """Scan ml_engine/models/ for the most recent artefact set."""
        try:
            scalers = sorted(_MODELS_DIR.glob('scaler_v*.pkl'), reverse=True)
            if not scalers:
                logger.warning("No trained models found on disk.")
                return
            ts = scalers[0].stem.replace('scaler_v', '')
            self._scaler = joblib.load(scalers[0])

            for name in ('random_forest', 'xgboost', 'neural_network', 'isolation_forest'):
                path = _MODELS_DIR / f'{name}_v{ts}.pkl'
                if path.exists():
                    self._models[name] = joblib.load(path)

            meta_path = _MODELS_DIR / f'meta_learner_v{ts}.pkl'
            if meta_path.exists():
                self._meta_learner = joblib.load(meta_path)

            label_path = _MODELS_DIR / f'label_map_v{ts}.json'
            if label_path.exists():
                with open(label_path) as f:
                    self._label_map = {int(k): v for k, v in json.load(f).items()}
            else:
                self._label_map = {0: 'normal', 1: 'sql_injection', 2: 'xss',
                                   3: 'command_injection', 4: 'path_traversal',
                                   5: 'csrf', 6: 'ldap_injection'}

            self._loaded = True
            logger.info(f"Models loaded from disk (timestamp {ts})")
        except Exception as e:
            logger.error(f"Failed to load models from disk: {e}")

    def is_ready(self) -> bool:
        return self._loaded and self._scaler is not None

    def classify(self, request_dict: dict) -> dict:
        from ml_engine.features import HTTPFeatureExtractor

        start = time.perf_counter()

        if not self.is_ready():
            # Fallback heuristic classification when models not loaded
            return self._heuristic_classify(request_dict, start)

        try:
            features = HTTPFeatureExtractor().extract(request_dict)
            features_scaled = self._scaler.transform(features.reshape(1, -1))

            # Level-1 predictions
            rf_proba = self._get_proba('random_forest', features_scaled)
            xgb_proba = self._get_proba('xgboost', features_scaled)
            nn_proba = self._get_proba('neural_network', features_scaled)
            if_score = self._get_if_score('isolation_forest', features_scaled)

            if self._meta_learner is not None:
                meta_features = np.concatenate([rf_proba, xgb_proba, nn_proba, [if_score]])
                final_proba = self._meta_learner.predict_proba(meta_features.reshape(1, -1))[0]
                predicted_class = int(self._meta_learner.predict(meta_features.reshape(1, -1))[0])
                confidence = float(np.max(final_proba))
            else:
                # No meta-learner — average RF + XGB + NN
                avg_proba = (rf_proba + xgb_proba + nn_proba) / 3.0
                predicted_class = int(np.argmax(avg_proba))
                confidence = float(np.max(avg_proba))

            attack_type = self._label_map.get(predicted_class, 'unknown')
            # Binary model only outputs 0 (normal) or 1 (attack).
            # Use heuristic rules to determine the specific attack category.
            if predicted_class == 1 or attack_type == 'unknown':
                attack_type = self._identify_attack_type(request_dict)

            is_attack = attack_type != 'normal'
            severity = self._compute_severity(attack_type, confidence)
            latency_ms = (time.perf_counter() - start) * 1000

            # Threshold gate (Section 3.5.1, Figure 3.3):
            # confidence >= 0.85 → alert; below → flagged for human review
            needs_review = is_attack and confidence < 0.85

            return {
                'attack_type': attack_type,
                'is_attack': is_attack,
                'confidence_score': confidence,
                'severity': severity,
                'needs_review': needs_review,
                'processing_latency_ms': latency_ms,
                'model_probabilities': {
                    'random_forest': rf_proba.tolist(),
                    'xgboost': xgb_proba.tolist(),
                    'neural_network': nn_proba.tolist(),
                    'isolation_forest_score': float(if_score),
                },
            }
        except Exception as e:
            logger.error(f"Inference error: {e}", exc_info=True)
            return self._heuristic_classify(request_dict, start)

    def _get_proba(self, model_name: str, features_scaled: np.ndarray) -> np.ndarray:
        model = self._models.get(model_name)
        if model is None:
            return np.array([0.5, 0.5])
        proba = model.predict_proba(features_scaled)[0]
        # Ensure 2-class output [normal_prob, attack_prob]
        if len(proba) < 2:
            proba = np.array([1 - proba[0], proba[0]])
        return proba[:2]

    def _get_if_score(self, model_name: str, features_scaled: np.ndarray) -> float:
        model = self._models.get(model_name)
        if model is None:
            return 0.0
        return float(model.decision_function(features_scaled)[0])

    def _compute_severity(self, attack_type: str, confidence: float) -> str:
        base = SEVERITY_MAP.get(attack_type, 'medium')
        if base == 'medium' and confidence > 0.95:
            return 'high'
        return base

    def _heuristic_classify(self, request_dict: dict, start: float) -> dict:
        """Rule-based fallback when ML models aren't loaded."""
        combined = (str(request_dict.get('url', '')) + str(request_dict.get('body', ''))).lower()
        attack_type = 'normal'
        if any(kw in combined for kw in ['union', 'select', 'drop', 'insert', "' or "]):
            attack_type = 'sql_injection'
        elif any(kw in combined for kw in ['<script', 'javascript:', 'onerror=']):
            attack_type = 'xss'
        elif any(kw in combined for kw in ['cat /etc', '| ls', '&& rm', '../etc']):
            attack_type = 'command_injection'
        elif '../' in combined and 'etc' in combined:
            attack_type = 'path_traversal'

        is_attack = attack_type != 'normal'
        confidence = 0.85 if is_attack else 0.90
        severity = self._compute_severity(attack_type, confidence)
        latency_ms = (time.perf_counter() - start) * 1000

        return {
            'attack_type': attack_type,
            'is_attack': is_attack,
            'confidence_score': confidence,
            'severity': severity,
            'processing_latency_ms': latency_ms,
            'model_probabilities': {},
        }

    def _identify_attack_type(self, request_dict: dict) -> str:
        """
        Rule-based attack type classification.
        Used after the ML model confirms a request IS an attack (binary=1),
        to identify the specific OWASP category.
        """
        url = str(request_dict.get('url', '')).lower()
        body = str(request_dict.get('body', '')).lower()
        combined = url + ' ' + body
        headers = request_dict.get('headers', {}) or {}
        ua = str(headers.get('User-Agent', headers.get('user-agent', ''))).lower()

        # SQL Injection indicators
        sql_patterns = ['union', 'select ', 'insert ', 'update ', 'delete ', 'drop ',
                        "' or ", "' and ", '1=1', '1=2', 'exec ', 'xp_',
                        'information_schema', '--', 'sleep(', 'benchmark(']
        if any(p in combined for p in sql_patterns):
            return 'sql_injection'

        # XSS indicators
        xss_patterns = ['<script', 'javascript:', 'onerror=', 'onload=', 'alert(',
                        'document.cookie', 'document.domain', '<svg', '<img src=x',
                        'fromcharcode', '<body on', '<iframe']
        if any(p in combined for p in xss_patterns):
            return 'xss'

        # Command Injection indicators
        cmd_patterns = ['; cat ', '| cat ', '&& cat ', '; ls', '| ls', '&& rm',
                        '; wget ', '&& wget ', '| nc ', '; nc ', '; uname',
                        '/bin/bash', '/bin/sh', 'curl ', '; id', '| id']
        if any(p in combined for p in cmd_patterns):
            return 'command_injection'

        # Path Traversal indicators
        if '../' in combined or '..\\' in combined or '%2e%2e' in combined:
            return 'path_traversal'

        # LDAP Injection indicators
        ldap_patterns = [')(|', ')(&', 'objectclass=*', '*(|', '*(uid=']
        if any(p in combined for p in ldap_patterns):
            return 'ldap_injection'

        # CSRF indicators
        csrf_patterns = ['csrf_token=invalid', 'csrf_token=fake', 'token=forged',
                         'csrf=', '_token=']
        if any(p in combined for p in csrf_patterns):
            if 'transfer' in combined or 'delete' in combined or 'amount' in combined:
                return 'csrf'

        # Scanner detection via User-Agent
        scanner_uas = ['sqlmap', 'nikto', 'nmap', 'burp', 'dirbuster', 'gobuster',
                       'wfuzz', 'nuclei', 'acunetix']
        if any(s in ua for s in scanner_uas):
            return 'sql_injection'  # Scanner traffic defaults to SQLi category

        # Generic attack if no specific pattern matched
        return 'sql_injection'
