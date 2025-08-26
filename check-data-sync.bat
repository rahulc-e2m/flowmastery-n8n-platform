@echo off
echo 🔍 FlowMastery Data Sync Checker
echo ================================
echo.

echo 📊 Checking Docker services...
docker-compose ps

echo.
echo 🔄 Checking if Celery Beat is running...
docker-compose logs celery-beat --tail=5

echo.
echo 🔄 Checking if Celery Worker is running...
docker-compose logs celery-worker --tail=5

echo.
echo 📱 Redis status...
docker-compose exec redis redis-cli ping

echo.
echo 🗄️ PostgreSQL status...
docker-compose exec postgres pg_isready -U postgres

echo.
echo 📋 Available options:
echo 1. Restart all services: docker-compose down && docker-compose up -d
echo 2. Check logs: docker-compose logs [service-name]
echo 3. Force data sync via API: curl -X POST http://localhost:8000/api/v1/metrics/admin/quick-sync
echo.