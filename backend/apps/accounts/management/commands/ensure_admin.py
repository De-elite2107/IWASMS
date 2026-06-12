"""
Management command: python manage.py ensure_admin
Creates the admin superuser if it doesn't exist.
Reads credentials from environment variables.
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create admin superuser from environment variables if not exists'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_ADMIN_USERNAME', 'admin')
        email = os.environ.get('DJANGO_ADMIN_EMAIL', 'admin@iwasms.local')
        password = os.environ.get('DJANGO_ADMIN_PASSWORD', 'admin123')

        if User.objects.filter(username=username).exists():
            self.stdout.write(f'Admin user "{username}" already exists.')
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Admin user "{username}" created.'))
