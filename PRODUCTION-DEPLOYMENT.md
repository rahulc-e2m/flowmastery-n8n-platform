# FlowMastery Production Deployment Guide

This guide covers deploying FlowMastery in production, both as a monorepo and as separate frontend/backend services.

## Overview

FlowMastery can be deployed in two ways:
1. **Monorepo deployment** - Both frontend and backend together (current setup)
2. **Separate deployment** - Frontend and backend deployed independently

## Deployment Scenarios

### Scenario 1: Monorepo Deployment (Docker Compose)

Use this when deploying both services together on the same infrastructure.

1. **Setup environment:**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Deploy with Docker Compose:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Initialize database:**
   ```bash
   docker-compose exec backend alembic upgrade head
   docker-compose exec backend python create_admin.py
   ```

### Scenario 2: Separate Deployment

Use this when deploying frontend and backend to different services/providers.

#### Backend Deployment

1. **Navigate to backend:**
   ```bash
   cd packages/backend
   ```

2. **Setup environment:**
   ```bash
   cp .env.example .env
   # Configure with production values
   ```

3. **Deploy using your preferred method:**
   - See [Backend Deployment Guide](packages/backend/DEPLOYMENT.md)
   - Platforms: Heroku, Railway, AWS ECS, Google Cloud Run, etc.

#### Frontend Deployment

1. **Navigate to frontend:**
   ```bash
   cd packages/frontend
   ```

2. **Setup environment:**
   ```bash
   cp .env.example .env
   # Set VITE_API_URL to your backend URL
   ```

3. **Build and deploy:**
   ```bash
   npm run build
   # Deploy 'dist' folder to your static hosting
   ```
   - Platforms: Netlify, Vercel, AWS S3+CloudFront, etc.
   - See [Frontend Deployment Guide](packages/frontend/DEPLOYMENT.md)

## Environment Configuration Templates

### Production .env Template (Root Level)
```bash
# Copy this template when deploying with Docker Compose
# Application
DEBUG=false
SECRET_KEY=your-production-secret-key-32-chars-minimum
ENCRYPTION_KEY=your-32-char-encryption-key-here!!

# Database
DATABASE_URL=postgresql+asyncpg://username:password@your-db-host:5432/flowmastery_prod

# Redis
REDIS_URL=redis://username:password@your-redis-host:6379/0

# Email (Required)
SMTP_HOST=smtp.your-provider.com
SMTP_USERNAME=your-email@yourdomain.com
SMTP_PASSWORD=your-secure-app-password
FROM_EMAIL=noreply@yourdomain.com

# URLs
FRONTEND_URL=https://app.yourdomain.com
VITE_API_URL=https://api.yourdomain.com

# CORS
CORS_ORIGINS=https://app.yourdomain.com,https://admin.yourdomain.com

# Optional: n8n Integration
N8N_API_URL=https://n8n.yourdomain.com/api/v1
N8N_API_KEY=your-n8n-api-key
```

### Backend .env Template
```bash
# For independent backend deployment
DEBUG=false
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
SMTP_HOST=smtp.your-provider.com
SMTP_USERNAME=your-email@domain.com
SMTP_PASSWORD=your-password
FRONTEND_URL=https://your-frontend.com
CORS_ORIGINS=https://your-frontend.com
```

### Frontend .env Template
```bash
# For independent frontend deployment
VITE_API_URL=https://your-backend-api.com
VITE_APP_NAME=FlowMastery
VITE_DEV_MODE=false
VITE_SOURCE_MAPS=false
```

## Security Checklist

### Backend Security
- [ ] Use strong SECRET_KEY (32+ random characters)
- [ ] Use strong ENCRYPTION_KEY (32 random characters)
- [ ] Set DEBUG=false in production
- [ ] Use HTTPS for all URLs
- [ ] Secure database with SSL and strong credentials
- [ ] Configure proper CORS origins
- [ ] Use environment variables, never hardcode secrets
- [ ] Enable rate limiting
- [ ] Keep dependencies updated

### Frontend Security
- [ ] Serve over HTTPS only
- [ ] Configure Content Security Policy (CSP) headers
- [ ] Set proper cache headers
- [ ] Remove source maps in production (VITE_SOURCE_MAPS=false)
- [ ] Validate all environment variables
- [ ] Keep dependencies updated

### Infrastructure Security
- [ ] Use SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Enable database backups
- [ ] Set up monitoring and logging
- [ ] Use secrets management (AWS Secrets, etc.)

## Deployment Platforms

### Cloud Platforms

#### AWS
- **Backend:** ECS Fargate, Lambda, or EC2
- **Frontend:** S3 + CloudFront
- **Database:** RDS PostgreSQL
- **Cache:** ElastiCache Redis

#### Google Cloud
- **Backend:** Cloud Run, App Engine, or GKE
- **Frontend:** Cloud Storage + CDN
- **Database:** Cloud SQL PostgreSQL
- **Cache:** Memorystore Redis

#### Azure
- **Backend:** Container Instances, App Service
- **Frontend:** Static Web Apps, Blob Storage + CDN
- **Database:** Azure Database for PostgreSQL
- **Cache:** Azure Cache for Redis

### Platform-as-a-Service

#### Heroku
- **Backend:** Heroku app with PostgreSQL and Redis addons
- **Frontend:** Static deployment or separate Heroku app

#### Railway
- **Backend:** Deploy from GitHub with PostgreSQL and Redis
- **Frontend:** Static deployment

#### Render
- **Backend:** Web Service with PostgreSQL and Redis
- **Frontend:** Static Site

### Static Hosting (Frontend)
- Netlify
- Vercel
- AWS S3 + CloudFront
- Google Cloud Storage
- Azure Static Web Apps

## Database Migration

When moving to production:

1. **Export development data (if needed):**
   ```bash
   pg_dump development_db > backup.sql
   ```

2. **Set up production database:**
   - Create PostgreSQL instance
   - Configure connection security
   - Set up automated backups

3. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

4. **Create admin user:**
   ```bash
   python create_admin.py
   ```

## Monitoring and Maintenance

### Health Checks
- Backend: `GET /health`
- Application status: `GET /api/v1/config/app/status`

### Logging
- Configure structured logging with LOG_LEVEL=INFO
- Use centralized logging (CloudWatch, LogDNA, etc.)
- Monitor error rates and performance metrics

### Backups
- Automated database backups
- Regular testing of backup restoration
- Version control for configuration files

### Updates
- Keep dependencies updated
- Monitor security advisories
- Test updates in staging environment first

## Troubleshooting

### Common Issues

1. **CORS Errors:**
   - Add frontend domain to CORS_ORIGINS
   - Ensure protocol (http/https) matches

2. **Database Connection:**
   - Verify DATABASE_URL format
   - Check network connectivity and firewall rules
   - Ensure database exists and user has permissions

3. **Email Sending:**
   - Verify SMTP credentials
   - Check provider-specific requirements (app passwords, OAuth)
   - Test with a simple email client first

4. **Environment Variables:**
   - Ensure all required variables are set
   - Check for typos in variable names
   - Verify values are properly quoted if needed

### Getting Help

1. Check application logs
2. Review this deployment guide
3. Check the troubleshooting sections in:
   - [Backend Deployment Guide](packages/backend/DEPLOYMENT.md)
   - [Frontend Deployment Guide](packages/frontend/DEPLOYMENT.md)
4. Create an issue in the repository with:
   - Deployment method used
   - Error messages
   - Environment configuration (without secrets)

## Migration from Monorepo to Separate Deployment

If you're currently using the monorepo setup and want to migrate to separate deployments:

1. **Deploy backend first:**
   - Copy `packages/backend/.env.example` to `packages/backend/.env`
   - Configure with your production settings
   - Deploy backend to your chosen platform
   - Note the backend URL

2. **Deploy frontend:**
   - Copy `packages/frontend/.env.example` to `packages/frontend/.env`
   - Set `VITE_API_URL` to your backend URL
   - Build and deploy to static hosting

3. **Update CORS:**
   - Add your frontend URL to backend's `CORS_ORIGINS`
   - Restart backend service

4. **Test integration:**
   - Verify frontend can connect to backend
   - Test authentication and API calls
   - Check email functionality

This approach allows you to gradually migrate from monorepo to microservices architecture.