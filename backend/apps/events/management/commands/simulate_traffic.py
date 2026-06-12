"""
Management command: python manage.py simulate_traffic --rate 10 --duration 60
Generates synthetic HTTP traffic and POSTs to /api/v1/events/classify/
"""
import time
import random
import logging
import requests as http_requests
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Simulate HTTP traffic for dashboard testing'

    def add_arguments(self, parser):
        parser.add_argument('--rate', type=int, default=5, help='Requests per second')
        parser.add_argument('--duration', type=int, default=60, help='Duration in seconds')
        parser.add_argument('--host', type=str, default='http://localhost:8000', help='API host')
        parser.add_argument('--direct', action='store_true', help='Classify directly (no HTTP)')

    def handle(self, *args, **options):
        rate = options['rate']
        duration = options['duration']
        host = options['host']
        direct = options['direct']
        interval = 1.0 / rate

        self.stdout.write(self.style.NOTICE(
            f'Simulating traffic: {rate} req/s for {duration}s (direct={direct})'
        ))

        from ml_engine.trainer import (
            _make_normal_request, _make_attack_request, _ATTACK_CATEGORIES
        )

        attack_items = list(_ATTACK_CATEGORIES.items())
        total = 0
        attacks = 0
        start = time.time()

        while time.time() - start < duration:
            t_req = time.time()

            # 40% attack, 60% normal
            if random.random() < 0.40:
                category, (payloads, _) = random.choice(attack_items)
                req = _make_attack_request(category, payloads)
                attacks += 1
            else:
                req = _make_normal_request()

            if direct:
                self._classify_direct(req)
            else:
                self._classify_http(host, req)

            total += 1
            if total % 10 == 0:
                elapsed = time.time() - start
                self.stdout.write(
                    f'  [{elapsed:.0f}s] {total} requests sent, {attacks} attacks'
                )

            # Sleep to maintain rate
            sleep_time = interval - (time.time() - t_req)
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.stdout.write(self.style.SUCCESS(
            f'\nSimulation complete: {total} total, {attacks} attacks ({attacks/max(total,1)*100:.1f}%)'
        ))

    def _classify_http(self, host: str, req: dict):
        try:
            url = f"{host}/api/v1/events/classify/"
            headers = req.pop('headers', {})
            payload = {**req, 'headers': headers}
            http_requests.post(url, json=payload, timeout=5)
        except Exception as e:
            logger.debug(f"HTTP classify failed: {e}")

    def _classify_direct(self, req: dict):
        try:
            from apps.ml.inference import InferenceService
            from apps.events.models import SecurityEvent
            from django.utils import timezone
            import asgiref.sync

            result = InferenceService.get_instance().classify(req)

            SecurityEvent.objects.create(
                source_ip=req.get('source_ip', '127.0.0.1'),
                http_method=req.get('method', 'GET'),
                url=req.get('url', '/'),
                user_agent=req.get('headers', {}).get('User-Agent', ''),
                raw_request=req,
                attack_type=result['attack_type'],
                severity=result['severity'],
                is_attack=result['is_attack'],
                confidence_score=result['confidence_score'],
                processing_latency_ms=result['processing_latency_ms'],
                timestamp=timezone.now(),
            )

            if result['is_attack']:
                from apps.alerts.models import SecurityAlert
                try:
                    event = SecurityEvent.objects.filter(
                        source_ip=req.get('source_ip', '127.0.0.1')
                    ).order_by('-timestamp').first()
                    if event:
                        SecurityAlert.objects.get_or_create(
                            event=event,
                            defaults={
                                'title': f"{result['attack_type'].replace('_', ' ').title()} Detected",
                                'description': f"Simulated attack: {result['attack_type']}",
                                'severity': result['severity'],
                            }
                        )
                except Exception:
                    pass

            # Push to WebSocket
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                channel_layer = get_channel_layer()
                if channel_layer:
                    from apps.events.models import SecurityEvent as SE
                    latest = SE.objects.filter(
                        source_ip=req.get('source_ip', '127.0.0.1')
                    ).order_by('-timestamp').first()
                    if latest:
                        async_to_sync(channel_layer.group_send)(
                            'security_events',
                            {
                                'type': 'security_event',
                                'data': {
                                    'id': str(latest.id),
                                    'timestamp': latest.timestamp.isoformat(),
                                    'source_ip': latest.source_ip,
                                    'http_method': latest.http_method,
                                    'url': latest.url,
                                    'attack_type': latest.attack_type,
                                    'severity': latest.severity,
                                    'is_attack': latest.is_attack,
                                    'confidence_score': latest.confidence_score,
                                },
                            }
                        )
            except Exception:
                pass
        except Exception as e:
            logger.debug(f"Direct classify failed: {e}")
