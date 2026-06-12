"""
Management command: python manage.py seed_demo
Seeds the database with 500 historical events and test users.
"""
import random
import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Seed the database with demo data for the IWASMS dashboard'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Seeding demo data...'))

        # 1. Web Application
        from apps.events.models import WebApplication
        webapp, _ = WebApplication.objects.get_or_create(
            name='Demo E-Commerce Platform',
            defaults={
                'base_url': 'https://shop.example.com',
                'organization': 'IWASMS Demo Corp',
            }
        )
        self.stdout.write(f'  Web application: {webapp.name}')

        # 2. Users
        users = self._create_users()

        # 3. Generate 500 historical events
        self.stdout.write('  Generating 500 historical security events...')
        self._generate_events(webapp, users)

        # 4. Mark some alerts
        self._mark_alerts()

        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully!'))
        from apps.events.models import SecurityEvent
        from apps.alerts.models import SecurityAlert
        total = SecurityEvent.objects.count()
        alerts = SecurityAlert.objects.count()
        open_alerts = SecurityAlert.objects.filter(status='open').count()
        self.stdout.write(f'  Total events: {total}')
        self.stdout.write(f'  Total alerts: {alerts} ({open_alerts} open)')

    def _create_users(self):
        users = {}

        # Admin
        admin, created = User.objects.get_or_create(username='admin')
        if created:
            admin.set_password('admin123')
            admin.is_staff = True
            admin.is_superuser = True
            admin.email = 'admin@iwasms.local'
            admin.save()
        users['admin'] = admin

        # Analyst
        analyst, created = User.objects.get_or_create(username='analyst')
        if created:
            analyst.set_password('analyst123')
            analyst.email = 'analyst@iwasms.local'
            analyst.first_name = 'Security'
            analyst.last_name = 'Analyst'
            analyst.save()
        users['analyst'] = analyst

        # Viewer
        viewer, created = User.objects.get_or_create(username='viewer')
        if created:
            viewer.set_password('viewer123')
            viewer.email = 'viewer@iwasms.local'
            viewer.first_name = 'Read'
            viewer.last_name = 'Only'
            viewer.save()
        users['viewer'] = viewer

        self.stdout.write(f'  Created {len(users)} users')
        return users

    def _generate_events(self, webapp, users):
        from apps.events.models import SecurityEvent
        from apps.alerts.models import SecurityAlert
        from apps.ml.inference import InferenceService
        from ml_engine.trainer import (
            _make_normal_request, _make_attack_request, _ATTACK_CATEGORIES
        )

        attack_items = list(_ATTACK_CATEGORIES.items())
        now = timezone.now()
        inference = InferenceService.get_instance()

        events_created = 0
        for i in range(500):
            # Spread over past 7 days
            hours_ago = random.uniform(0, 7 * 24)
            event_time = now - timedelta(hours=hours_ago)

            # 40% attack
            if random.random() < 0.40:
                category, (payloads, _) = random.choice(attack_items)
                req = _make_attack_request(category, payloads)
            else:
                req = _make_normal_request()

            result = inference.classify(req)

            event = SecurityEvent.objects.create(
                timestamp=event_time,
                source_ip=req['source_ip'],
                http_method=req['method'],
                url=req['url'],
                user_agent=req.get('headers', {}).get('User-Agent', ''),
                raw_request=req,
                attack_type=result['attack_type'],
                severity=result['severity'],
                is_attack=result['is_attack'],
                confidence_score=result['confidence_score'],
                processing_latency_ms=result['processing_latency_ms'],
                web_application=webapp,
            )

            if result['is_attack']:
                SecurityAlert.objects.get_or_create(
                    event=event,
                    defaults={
                        'title': f"{result['attack_type'].replace('_', ' ').title()} Detected",
                        'description': (
                            f"Attack type '{result['attack_type']}' detected from {req['source_ip']}. "
                            f"Confidence: {result['confidence_score']:.2%}. URL: {req['url']}"
                        ),
                        'severity': result['severity'],
                        'created_at': event_time,
                    }
                )

            events_created += 1
            if events_created % 100 == 0:
                self.stdout.write(f'    {events_created}/500 events created')

    def _mark_alerts(self):
        from apps.alerts.models import SecurityAlert
        from django.contrib.auth.models import User

        analyst = User.objects.filter(username='analyst').first()
        alerts = list(SecurityAlert.objects.filter(status='open'))

        random.shuffle(alerts)

        # Resolve 40
        for alert in alerts[:40]:
            alert.status = 'resolved'
            alert.resolved_at = timezone.now() - timedelta(hours=random.uniform(0, 12))
            alert.assigned_to = analyst
            alert.analyst_notes = 'Investigated and resolved. Source IP blocked at firewall.'
            alert.save()

        # Mark 12 as false positive
        for alert in alerts[40:52]:
            alert.status = 'false_positive'
            alert.resolved_at = timezone.now() - timedelta(hours=random.uniform(0, 6))
            alert.assigned_to = analyst
            alert.analyst_notes = 'Confirmed false positive — internal scanner traffic.'
            alert.save()

        self.stdout.write(f'  Marked 40 alerts resolved, 12 as false positive')
