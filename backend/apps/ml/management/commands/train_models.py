"""
Management command: python manage.py train_models
Alias for ingest_and_train. Named to match Section 3.5.3 of the thesis.
"""
from apps.ml.management.commands.ingest_and_train import Command as BaseCommand


class Command(BaseCommand):
    help = 'Load dataset and train the IWASMS ensemble ML model (alias for ingest_and_train)'
