.PHONY: build up down migrate createsuperuser train seed logs setup clean

# ──────────────────────────────────────────────────────────────
# IWASMS — Docker Compose Commands (Section 3.6.3)
# Requires: Docker Engine 24+ and Docker Compose v2 plugin
# ──────────────────────────────────────────────────────────────

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

migrate:
	docker compose exec django python manage.py migrate --noinput

createsuperuser:
	docker compose exec django python manage.py createsuperuser

train:
	docker compose exec django python manage.py train_models

ingest:
	docker compose exec django python manage.py ingest_dataset --train

seed:
	docker compose exec django python manage.py seed_demo

logs:
	docker compose logs -f django celery

logs-all:
	docker compose logs -f

ps:
	docker compose ps

shell:
	docker compose exec django python manage.py shell

test:
	docker compose exec django pytest

clean:
	docker compose down -v --remove-orphans

# ──────────────────────────────────────────────────────────────
# Full production-ready setup (single command)
# ──────────────────────────────────────────────────────────────

setup: build up
	@echo "Waiting for services to start..."
	@sleep 15
	$(MAKE) migrate
	@echo "Creating admin user..."
	@docker compose exec django python manage.py shell -c \
		"from django.contrib.auth.models import User; \
		 User.objects.filter(username='admin').exists() or \
		 User.objects.create_superuser('admin', 'admin@iwasms.local', 'admin123')"
	@echo "Training ML ensemble (this may take 1-2 minutes)..."
	$(MAKE) train
	@echo ""
	@echo "======================================"
	@echo "  IWASMS Production Ready"
	@echo "  Dashboard:  http://localhost"
	@echo "  API:        http://localhost/api/v1/"
	@echo "  WebSocket:  ws://localhost/ws/events/"
	@echo "  Admin:      http://localhost/admin/"
	@echo "  Username:   admin"
	@echo "  Password:   admin123"
	@echo "======================================"
