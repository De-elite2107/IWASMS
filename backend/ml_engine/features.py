"""
IWASMS ML Engine — 77-Feature HTTP Request Extractor

Feature groups:
  Lexical     (15 features) — indices  0-14
  Syntactic   (22 features) — indices 15-36
  Semantic    (18 features) — indices 37-54
  Statistical (12 features) — indices 55-66
  Behavioural (10 features) — indices 67-76
"""
import math
import re
import ipaddress
import logging
from urllib.parse import urlparse, parse_qs, unquote_plus
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

KNOWN_SCANNER_UAS = [
    'sqlmap', 'nikto', 'nmap', 'masscan', 'burpsuite', 'burp suite',
    'dirbuster', 'dirb', 'gobuster', 'wfuzz', 'hydra', 'metasploit',
    'zgrab', 'nuclei', 'acunetix', 'nessus', 'openvas',
]

KNOWN_SCANNER_IPS = [
    '0.0.0.0/8', '100.64.0.0/10',
]

SUSPICIOUS_BIGRAMS = {'or', '--', '/*', '*/', 'xp', 'ex', 'ec', 'un', 'se', 'dr'}

HTTP_METHOD_MAP = {
    'GET': 0, 'POST': 1, 'PUT': 2, 'DELETE': 3,
    'PATCH': 4, 'HEAD': 5, 'OPTIONS': 6, 'TRACE': 7, 'CONNECT': 8,
}

CONTENT_TYPE_MAP = {
    None: 0, '': 0,
    'form': 1, 'application/x-www-form-urlencoded': 1,
    'json': 2, 'application/json': 2,
    'xml': 3, 'application/xml': 3, 'text/xml': 3,
    'multipart': 4, 'multipart/form-data': 4,
}

# Approximate English character frequencies (a-z normalised)
ENGLISH_CHAR_FREQ = {
    'e': 0.1270, 't': 0.0906, 'a': 0.0817, 'o': 0.0751, 'i': 0.0697,
    'n': 0.0675, 's': 0.0633, 'h': 0.0609, 'r': 0.0599, 'd': 0.0425,
    'l': 0.0403, 'c': 0.0278, 'u': 0.0276, 'm': 0.0241, 'w': 0.0234,
    'f': 0.0223, 'g': 0.0202, 'y': 0.0197, 'p': 0.0193, 'b': 0.0149,
    'v': 0.0098, 'k': 0.0077, 'j': 0.0015, 'x': 0.0015, 'q': 0.0010,
    'z': 0.0007,
}

SQL_KEYWORDS = ['select', 'union', 'insert', 'update', 'delete', 'drop', 'exec', 'xp_']
XSS_INDICATORS = ['<script', 'javascript:', 'onerror=', 'onload=', 'alert(', 'document.cookie']
CMD_INDICATORS = ['; ls', '| cat', '&& rm', '../', 'wget ', 'curl ']

BASE64_PATTERN = re.compile(r'^[A-Za-z0-9+/]{16,}={0,2}$')
FILE_EXTENSION_PATTERN = re.compile(r'\.[a-zA-Z]{2,4}(\?|$|#)')
PERCENT_ENCODING_PATTERN = re.compile(r'%[0-9A-Fa-f]{2}')


# ---------------------------------------------------------------------------
# Redis helper (optional — graceful fallback when Redis unavailable)
# ---------------------------------------------------------------------------

def _get_redis_client():
    try:
        import redis
        import os
        host = os.environ.get('REDIS_HOST', 'redis')
        port = int(os.environ.get('REDIS_PORT', 6379))
        r = redis.Redis(host=host, port=port, db=2, socket_connect_timeout=1, socket_timeout=1)
        r.ping()
        return r
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def shannon_entropy(s: str) -> float:
    """Compute Shannon entropy of string s."""
    if not s:
        return 0.0
    counts: dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    length = len(s)
    entropy = 0.0
    for count in counts.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def longest_consecutive_special_chars(s: str) -> int:
    """Return the length of the longest run of non-alphanumeric, non-space chars."""
    if not s:
        return 0
    max_run = 0
    run = 0
    for ch in s:
        if not ch.isalnum() and ch != ' ':
            run += 1
            max_run = max(max_run, run)
        else:
            run = 0
    return max_run


def bigram_suspicion_score(s: str) -> float:
    """Count how many 2-char bigrams in s appear in SUSPICIOUS_BIGRAMS."""
    if len(s) < 2:
        return 0.0
    s_lower = s.lower()
    count = sum(1 for i in range(len(s_lower) - 1) if s_lower[i:i+2] in SUSPICIOUS_BIGRAMS)
    return float(count)


def char_frequency_deviation(s: str) -> float:
    """L1 distance between actual char frequency and expected English frequency."""
    if not s:
        return 0.0
    s_lower = s.lower()
    total = len(s_lower)
    actual: dict[str, float] = {}
    for ch in s_lower:
        if ch.isalpha():
            actual[ch] = actual.get(ch, 0) + 1
    if total == 0:
        return 0.0
    actual = {k: v / total for k, v in actual.items()}
    deviation = 0.0
    all_chars = set(list(actual.keys()) + list(ENGLISH_CHAR_FREQ.keys()))
    for ch in all_chars:
        deviation += abs(actual.get(ch, 0.0) - ENGLISH_CHAR_FREQ.get(ch, 0.0))
    return deviation


def content_type_encode(ct: Optional[str]) -> int:
    if not ct:
        return 0
    ct_lower = ct.lower()
    if 'multipart' in ct_lower:
        return 4
    if 'json' in ct_lower:
        return 2
    if 'xml' in ct_lower:
        return 3
    if 'form' in ct_lower or 'urlencoded' in ct_lower:
        return 1
    return 5


def is_valid_base64(s: str) -> bool:
    try:
        import base64
        decoded = base64.b64decode(s + '==', validate=False)
        return len(decoded) > 8
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Main Feature Extractor
# ---------------------------------------------------------------------------

class HTTPFeatureExtractor:
    """
    Extract exactly 77 features from an HTTP request dictionary.

    Input schema:
        {
            "method": str,
            "url": str,
            "headers": dict,
            "body": str,
            "source_ip": str,
        }
    """

    def extract(self, request_dict: dict) -> np.ndarray:
        method = str(request_dict.get('method', 'GET')).upper()
        url = str(request_dict.get('url', '/'))
        headers = request_dict.get('headers', {}) or {}
        if not isinstance(headers, dict):
            headers = {}
        body = str(request_dict.get('body', '') or '')
        source_ip = str(request_dict.get('source_ip', '127.0.0.1') or '127.0.0.1')

        # Parsed URL components
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query, keep_blank_values=True)
        except Exception:
            parsed = urlparse('/')
            query_params = {}

        path_segments = [s for s in parsed.path.split('/') if s]
        all_param_values = []
        for vals in query_params.values():
            all_param_values.extend(vals)

        # Parse body params if form-encoded
        body_params: dict = {}
        content_type = headers.get('Content-Type', headers.get('content-type', ''))
        if content_type and 'urlencoded' in content_type.lower():
            try:
                body_params = dict(parse_qs(body))
                for vals in body_params.values():
                    all_param_values.extend(vals)
            except Exception:
                pass

        combined = url + body
        total_length = len(url) + len(body) + sum(len(str(v)) for v in headers.values())

        # ================================================================
        # GROUP 1: Lexical (15 features, indices 0-14)
        # ================================================================
        url_length = float(len(url))
        body_length = float(len(body))
        total_request_length = float(total_length)

        all_params = list(query_params.values()) + list(body_params.values())
        flat_params = [str(v) for group in all_params for v in group]
        num_parameters = float(len(flat_params))
        max_param_length = float(max((len(v) for v in flat_params), default=0))
        avg_param_length = float(sum(len(v) for v in flat_params) / max(len(flat_params), 1))

        special_chars = set('<>\'\"%;()&+{}[]\\|`^~')
        special_count = sum(1 for c in combined if c in special_chars)
        special_char_ratio = float(special_count / max(len(combined), 1))

        digit_count = sum(1 for c in combined if c.isdigit())
        digit_ratio = float(digit_count / max(len(combined), 1))

        upper_count = sum(1 for c in combined if c.isupper())
        uppercase_ratio = float(upper_count / max(len(combined), 1))

        num_path_segments = float(len(path_segments))
        num_query_params = float(len(query_params))

        has_encoded_chars = float(1 if PERCENT_ENCODING_PATTERN.search(url) else 0)

        user_agent = str(headers.get('User-Agent', headers.get('user-agent', '')) or '')
        cookie = str(headers.get('Cookie', headers.get('cookie', '')) or '')

        num_headers = float(len(headers))
        user_agent_length = float(len(user_agent))
        cookie_length = float(len(cookie))

        lexical = [
            url_length, body_length, total_request_length,
            num_parameters, max_param_length, avg_param_length,
            special_char_ratio, digit_ratio, uppercase_ratio,
            num_path_segments, num_query_params,
            has_encoded_chars, num_headers, user_agent_length, cookie_length,
        ]  # 15 features

        # ================================================================
        # GROUP 2: Syntactic (22 features, indices 15-36)
        # ================================================================
        method_encoded = float(HTTP_METHOD_MAP.get(method, 9))

        ct_lower = content_type.lower() if content_type else ''
        has_multipart_body = float(1 if 'multipart' in ct_lower else 0)
        has_json_body = float(1 if 'json' in ct_lower or (body.strip().startswith('{') or body.strip().startswith('[')) else 0)
        has_xml_body = float(1 if 'xml' in ct_lower or body.strip().startswith('<') else 0)

        all_param_names = list(query_params.keys()) + list(body_params.keys())
        param_name_max_length = float(max((len(k) for k in all_param_names), default=0))
        param_value_max_length = float(max((len(v) for v in flat_params), default=0))

        num_equal_signs = float(combined.count('='))
        num_ampersands = float(combined.count('&'))
        num_semicolons = float(combined.count(';'))
        num_forward_slashes = float(url.count('/'))
        num_dots = float(combined.count('.'))
        num_hyphens = float(combined.count('-'))

        has_base64 = float(0)
        for val in flat_params:
            if len(val) >= 16 and BASE64_PATTERN.match(val) and is_valid_base64(val):
                has_base64 = 1.0
                break

        content_type_encoded = float(content_type_encode(content_type))

        has_file_ext_in_url = float(1 if FILE_EXTENSION_PATTERN.search(url) else 0)
        has_numeric_only_param = float(1 if any(v.isdigit() for v in flat_params) else 0)

        num_single_quotes = float(combined.count("'"))
        num_double_quotes = float(combined.count('"'))
        num_parentheses = float(combined.count('(') + combined.count(')'))

        has_comment_syntax = float(1 if ('--' in combined or '/*' in combined) else 0)

        syntactic = [
            method_encoded, has_multipart_body, has_json_body, has_xml_body,
            param_name_max_length, param_value_max_length,
            num_equal_signs, num_ampersands, num_semicolons,
            num_forward_slashes, num_dots, num_hyphens,
            has_base64, content_type_encoded,
            has_file_ext_in_url, has_numeric_only_param,
            num_single_quotes, num_double_quotes, num_parentheses,
            has_comment_syntax,
            float(combined.count('`')),     # extra backtick count
            float(url.count('?')),          # extra query marker count
        ]  # 22 features

        # ================================================================
        # GROUP 3: Semantic (18 features, indices 37-54)
        # ================================================================
        combined_lower = combined.lower()

        sql_counts = [float(combined_lower.count(kw)) for kw in SQL_KEYWORDS]  # 8
        xss_counts = [float(combined_lower.count(ind)) for ind in XSS_INDICATORS]  # 6
        cmd_counts = [float(combined_lower.count(ind)) for ind in CMD_INDICATORS]  # 6 → but wait, need exact 18

        # Pad/trim to exactly 18
        semantic_raw = sql_counts + xss_counts + cmd_counts  # 8+6+6 = 20 → trim 2
        semantic = semantic_raw[:18]  # take first 18

        # ================================================================
        # GROUP 4: Statistical (12 features, indices 55-66)
        # ================================================================
        param_values_concat = ''.join(all_param_values)

        entropy_url = shannon_entropy(url)
        entropy_body = shannon_entropy(body)
        entropy_params = shannon_entropy(param_values_concat)

        freq_deviation = char_frequency_deviation(combined)

        url_bigram_score = bigram_suspicion_score(url)
        body_bigram_score = bigram_suspicion_score(body)

        longest_special_url = float(longest_consecutive_special_chars(url))
        longest_special_body = float(longest_consecutive_special_chars(body))

        distinct_url = float(len(set(url)))
        distinct_body = float(len(set(body)))

        param_entropies = [shannon_entropy(v) for v in all_param_values] if all_param_values else [0.0]
        param_entropy_max = float(max(param_entropies))
        param_entropy_std = float(np.std(param_entropies))

        statistical = [
            entropy_url, entropy_body, entropy_params,
            freq_deviation,
            url_bigram_score, body_bigram_score,
            longest_special_url, longest_special_body,
            distinct_url, distinct_body,
            param_entropy_max, param_entropy_std,
        ]  # 12 features

        # ================================================================
        # GROUP 5: Behavioural (10 features, indices 67-76)
        # ================================================================
        behavioural = self._extract_behavioural(source_ip, method, url, total_length, user_agent)

        # ================================================================
        # Assemble and sanitise
        # ================================================================
        features = lexical + syntactic + semantic + statistical + behavioural

        assert len(features) == 77, f"Expected 77 features, got {len(features)}"

        arr = np.array(features, dtype=np.float64)
        arr = np.nan_to_num(arr, nan=0.0, posinf=1e6, neginf=-1e6)
        return arr

    def _extract_behavioural(self, source_ip: str, method: str,
                              url: str, total_length: int,
                              user_agent: str) -> list:
        redis_client = _get_redis_client()

        # --- requests_per_minute_from_ip ---
        rpm = 0.0
        rph = 0.0
        distinct_urls = 0.0
        time_since_last = 0.0
        consecutive_failed = 0.0
        method_changed = 0.0

        if redis_client:
            try:
                ip_key = source_ip.replace(':', '_').replace('.', '_')

                # RPM — 60s window
                rpm_key = f'iwasms:rpm:{ip_key}'
                rpm = float(redis_client.incr(rpm_key))
                redis_client.expire(rpm_key, 60)

                # RPH — 3600s window
                rph_key = f'iwasms:rph:{ip_key}'
                rph = float(redis_client.incr(rph_key))
                redis_client.expire(rph_key, 3600)

                # Distinct URLs (HyperLogLog)
                hll_key = f'iwasms:urls:{ip_key}'
                redis_client.pfadd(hll_key, url)
                redis_client.expire(hll_key, 3600)
                distinct_urls = float(redis_client.pfcount(hll_key))

                # Time since last request
                ts_key = f'iwasms:last_ts:{ip_key}'
                import time
                now_ts = time.time()
                last_ts = redis_client.get(ts_key)
                if last_ts:
                    time_since_last = float(now_ts - float(last_ts))
                redis_client.setex(ts_key, 3600, now_ts)

                # Consecutive failed requests
                fail_key = f'iwasms:fails:{ip_key}'
                fail_val = redis_client.get(fail_key)
                consecutive_failed = float(fail_val) if fail_val else 0.0

                # Method change detection
                method_key = f'iwasms:method:{ip_key}'
                last_method = redis_client.get(method_key)
                if last_method and last_method.decode('utf-8') != method:
                    method_changed = 1.0
                redis_client.setex(method_key, 3600, method)

            except Exception as e:
                logger.debug(f"Redis behavioural feature error: {e}")

        # --- is_known_scanner_ip ---
        is_scanner = 0.0
        try:
            ip_obj = ipaddress.ip_address(source_ip)
            for cidr in KNOWN_SCANNER_IPS:
                if ip_obj in ipaddress.ip_network(cidr, strict=False):
                    is_scanner = 1.0
                    break
        except ValueError:
            pass

        # --- is_tor_exit_node (placeholder) ---
        is_tor = 0.0

        # --- request_size_percentile ---
        if total_length < 200:
            size_bucket = 0.0
        elif total_length < 500:
            size_bucket = 1.0
        elif total_length < 1500:
            size_bucket = 2.0
        elif total_length < 5000:
            size_bucket = 3.0
        else:
            size_bucket = 4.0

        # --- has_suspicious_user_agent ---
        ua_lower = user_agent.lower()
        has_suspicious_ua = float(1 if any(s in ua_lower for s in KNOWN_SCANNER_UAS) else 0)

        return [
            rpm, rph, distinct_urls,
            is_scanner, time_since_last,
            consecutive_failed, is_tor,
            size_bucket, has_suspicious_ua, method_changed,
        ]  # 10 features
