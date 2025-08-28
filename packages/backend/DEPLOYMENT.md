# FlowMastery Backend Deployment Guide

This guide covers deploying the FlowMastery backend independently from the frontend.

## Prerequisites

- Python 3.9 or higher
- PostgreSQL 12 or higher
- Redis 6 or higher
- SMTP server for email notifications (Gmail, SendGrid, etc.)

## Environment Setup

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Configure environment variables:**
   Edit `.env` with your production settings:

   ```bash
   # Application Settings
   DEBUG=false
   SECRET_KEY=your-very-secure-secret-key-min-32-chars
   
   # Database (Required)
   DATABASE_URL=postgresql+asyncpg://username:password@your-db-host:5432/your_database
   
   # Redis (Required)
   REDIS_URL=redis://username:password@your-redis-host:6379/0
   
   # Email (Required for invitations)
   SMTP_HOST=smtp.your-provider.com
   SMTP_USERNAME=your-email@domain.com
   SMTP_PASSWORD=your-app-password
   FROM_EMAIL=noreply@yourdomain.com
   
   # Frontend URL (Required)
   FRONTEND_URL=https://your-frontend-domain.com
   
   # CORS Origins (Required)
   CORS_ORIGINS=https://your-frontend-domain.com,https://admin.yourdomain.com
   ```

## Deployment Options

### Option 1: Docker Deployment (Recommended)

1. **Build Docker image:**
   ```bash
   docker build -t flowmastery-backend .
   ```

2. **Run with Docker Compose:**
   ```yaml
   version: '3.8'
   services:
     backend:
       image: flowmastery-backend
       ports:
         - "8000:8000"
       environment:
         - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/flowmastery
         - REDIS_URL=redis://redis:6379/0
         - SECRET_KEY=your-secret-key
         - FRONTEND_URL=https://your-frontend.com
       depends_on:
         - db
         - redis
     
     db:
       image: postgres:14
       environment:
         POSTGRES_DB: flowmastery
         POSTGRES_USER: user
         POSTGRES_PASSWORD: pass
       volumes:
         - postgres_data:/var/lib/postgresql/data
     
     redis:
       image: redis:7-alpine
       
   volumes:
     postgres_data:
   ```

3. **Run migrations:**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

4. **Create admin user:**
   ```bash
   docker-compose exec backend python create_admin.py
   ```

### Option 2: Direct Deployment

1. **Install dependencies:**
   ```bash
   pip install -r requirements/prod.txt
   ```

2. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

3. **Create admin user:**
   ```bash
   python create_admin.py
   ```

4. **Start the application:**
   ```bash
   # For production use a WSGI server like Gunicorn
   gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

### Option 3: Cloud Platform Deployment

#### Heroku
```bash
# Create Heroku app
heroku create your-app-name

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DATABASE_URL=your-database-url
heroku config:set REDIS_URL=your-redis-url

# Deploy
git push heroku main

# Run migrations
heroku run alembic upgrade head

# Create admin user
heroku run python create_admin.py
```

#### Railway/Render
1. Connect your Git repository
2. Set environment variables in the dashboard
3. Deploy automatically on push

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SECRET_KEY` | ✅ | JWT signing key (32+ chars) | `your-secure-secret-key-here` |
| `DATABASE_URL` | ✅ | PostgreSQL connection URL | `postgresql+asyncpg://user:pass@host:5432/db` |
| `REDIS_URL` | ✅ | Redis connection URL | `redis://host:6379/0` |
| `SMTP_HOST` | ✅ | Email server hostname | `smtp.gmail.com` |
| `SMTP_USERNAME` | ✅ | Email username | `your-email@domain.com` |
| `SMTP_PASSWORD` | ✅ | Email password/app token | `your-app-password` |
| `FROM_EMAIL` | ✅ | Sender email address | `noreply@yourdomain.com` |
| `FRONTEND_URL` | ✅ | Frontend application URL | `https://app.yourdomain.com` |
| `CORS_ORIGINS` | ✅ | Allowed CORS origins | `https://app.yourdomain.com,https://admin.yourdomain.com` |
| `DEBUG` | ❌ | Enable debug mode | `false` |
| `LOG_LEVEL` | ❌ | Logging level | `INFO` |
| `N8N_API_URL` | ❌ | n8n instance URL | `https://n8n.yourdomain.com/api/v1` |
| `N8N_API_KEY` | ❌ | n8n API key | `your-n8n-api-key` |

## Security Considerations

1. **Use strong secrets:** Generate random 32+ character strings for `SECRET_KEY`
2. **Secure database:** Use SSL connections and strong passwords
3. **HTTPS only:** Always use HTTPS in production
4. **Environment isolation:** Never commit `.env` files to version control
5. **Regular updates:** Keep dependencies updated

## Monitoring

The backend exposes health check endpoints:
- `GET /health` - Basic health check
- `GET /api/v1/config/app/status` - Detailed application status

## Troubleshooting

1. **Database connection issues:**
   - Verify `DATABASE_URL` format
   - Check network connectivity
   - Ensure database exists

2. **Redis connection issues:**
   - Verify `REDIS_URL` format
   - Check Redis server status

3. **Email sending issues:**
   - Verify SMTP credentials
   - Check firewall settings
   - Test with email provider

4. **CORS issues:**
   - Add frontend domain to `CORS_ORIGINS`
   - Ensure protocol (http/https) matches

For more help, check the logs or create an issue in the repository.