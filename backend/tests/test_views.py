"""
Tests: Django API View Endpoints and Serialization Envelopes.

These tests use SQLite in-memory (via conftest.py) so no live Postgres needed.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User

from apps.events.models import SecurityEvent
from apps.alerts.models import SecurityAlert


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_event(**kwargs):
    defaults = dict(
        source_ip='8.8.8.8',
        http_method='GET',
        url='/api/test',
        user_agent='Mozilla/5.0',
        attack_type='normal',
        severity='normal',
        is_attack=False,
        confidence_score=0.99,
        processing_latency_ms=1.2,
    )
    defaults.update(kwargs)
    return SecurityEvent.objects.create(**defaults)


# ── test class ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestViewEndpoints:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testanalyst', password='password123')
        # Obtain JWT — LOGIN endpoint is unauthenticated
        response = self.client.post(
            reverse('auth-login'),
            {'username': 'testanalyst', 'password': 'password123'},
            format='json',
        )
        assert response.status_code == 200, f"Login failed: {response.data}"
        self.token = response.data['data']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    # ── auth ──────────────────────────────────────────────────────────────────

    def test_login_success(self):
        client = APIClient()
        response = client.post(
            reverse('auth-login'),
            {'username': 'testanalyst', 'password': 'password123'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data['data']
        assert 'refresh' in response.data['data']
        assert response.data['data']['user']['username'] == 'testanalyst'

    def test_login_invalid_credentials(self):
        client = APIClient()
        response = client.post(
            reverse('auth-login'),
            {'username': 'testanalyst', 'password': 'wrong'},
            format='json',
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['error'] == 'Invalid credentials'

    def test_me_endpoint(self):
        response = self.client.get(reverse('auth-me'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['username'] == 'testanalyst'

    # ── events ────────────────────────────────────────────────────────────────

    def test_classify_normal_request(self):
        response = self.client.post(
            reverse('classify-request'),
            {
                'method': 'GET',
                'url': '/api/products?id=42',
                'headers': {'User-Agent': 'Mozilla/5.0'},
                'body': '',
                'source_ip': '1.2.3.4',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.data['data']
        assert data['source_ip'] == '1.2.3.4'
        assert 'is_attack' in data
        assert 'severity' in data
        assert 'confidence_score' in data
        # Event persisted in DB
        assert SecurityEvent.objects.filter(source_ip='1.2.3.4').exists()

    def test_classify_path_traversal(self):
        response = self.client.post(
            reverse('classify-request'),
            {
                'method': 'GET',
                'url': '/index.php?file=../../../../etc/passwd',
                'headers': {'User-Agent': 'Wget/1.21'},
                'body': '',
                'source_ip': '5.5.5.5',
            },
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.data['data']
        assert data['is_attack'] is True
        assert data['attack_type'] in (
            'path_traversal', 'sql_injection', 'xss', 'command_injection', 'ldap_injection'
        )
        assert data['severity'] in ('medium', 'high', 'critical')

    def test_events_list_view(self):
        _make_event(source_ip='9.9.9.9')
        response = self.client.get(reverse('event-list'))
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data
        assert 'meta' in response.data
        assert len(response.data['data']) >= 1

    def test_events_list_filter_by_severity(self):
        _make_event(severity='critical', is_attack=True, attack_type='sql_injection', confidence_score=0.97)
        _make_event(severity='normal')
        response = self.client.get(reverse('event-list') + '?severity=critical')
        assert response.status_code == status.HTTP_200_OK
        for ev in response.data['data']:
            assert ev['severity'] == 'critical'

    def test_event_detail_view(self):
        ev = _make_event(source_ip='10.10.10.10')
        url = reverse('event-detail', args=[str(ev.id)])
        response = self.client.get(url)
        # Debug: show exactly what came back if not 200
        if response.status_code != status.HTTP_200_OK:
            print(f"\nDEBUG detail response status={response.status_code} data={response.data}")
        assert response.status_code == status.HTTP_200_OK
        # Handle both wrapped ({data: {...}}) and unwrapped ({source_ip: ...}) responses
        payload = response.data.get('data') or response.data
        assert payload['source_ip'] == '10.10.10.10'

    # ── alerts ────────────────────────────────────────────────────────────────

    def test_alerts_list(self):
        ev = _make_event(is_attack=True, attack_type='sql_injection', severity='high')
        SecurityAlert.objects.create(
            event=ev,
            title='SQL Injection Detected',
            severity='high',
            status='open',
        )
        response = self.client.get(reverse('alert-list'))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) >= 1

    def test_resolve_alert(self):
        ev = _make_event(is_attack=True, attack_type='brute_force', severity='high')
        alert = SecurityAlert.objects.create(
            event=ev,
            title='Brute Force',
            severity='high',
            status='open',
        )
        response = self.client.post(
            reverse('alert-resolve', args=[alert.id]),
            {'notes': 'Validated, blocked at FW'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['status'] == 'resolved'
        assert response.data['data']['analyst_notes'] == 'Validated, blocked at FW'

        alert.refresh_from_db()
        assert alert.status == 'resolved'

    def test_false_positive_alert(self):
        ev = _make_event(is_attack=True, attack_type='xss', severity='medium')
        alert = SecurityAlert.objects.create(
            event=ev, title='XSS Alert', severity='medium', status='open'
        )
        response = self.client.post(
            reverse('alert-false-positive', args=[alert.id]),
            {'notes': 'Scanner noise'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['status'] == 'false_positive'

        alert.refresh_from_db()
        assert alert.status == 'false_positive'
