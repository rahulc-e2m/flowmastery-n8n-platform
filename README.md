# Multi-Tenant Metrics Dashboard

A comprehensive multi-tenant metrics dashboard system with authentication, role-based access control, and n8n integration.

## Features

- **Multi-tenant Architecture**: Isolated client data and permissions
- **Authentication & Authorization**: JWT-based auth with role-based access control
- **Invitation System**: Secure user onboarding via email invitations
- **Metrics Dashboard**: Real-time workflow and execution analytics
- **n8n Integration**: Encrypted API key storage and workflow monitoring
- **Admin Panel**: Client management and system overview
- **Responsive UI**: Modern React interface with Tailwind CSS

## Quick Start

1. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd metrics-dashboard
   cp .env.example .env
   ```

2. **Configure Environment**:
   Edit `.env` file with your settings:
   - Database credentials
   - Email SMTP settings
   - Security keys (generate secure random keys)

3. **Start Services**:
   ```bash
   docker-compose up -d
   ```

4. **Create Admin User**:
   ```bash
   docker-compose exec backend python -c "
   from app.core.database import get_db
   from app.services.auth_service import AuthService
   from app.models.user import UserRole
   
   db = next(get_db())
   auth_service = AuthService(db)
   
   admin = auth_service.create_user(
       email='admin@example.com',
       password='admin123',
       role=UserRole.ADMIN,
       is_active=True
   )
   print(f'Admin user created: {admin.email}')
   "
   ```

5. **Access Application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Services

- **Frontend**: React application (port 3000)
- **Backend**: FastAPI application (port 8000)
- **PostgreSQL**: Database (port 5432)
- **Redis**: Caching and sessions (port 6379)

## Development

For development with hot reloading:

```bash
# Start all services
docker-compose up

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up --build
```

## Production Deployment

1. Update environment variables in `.env`
2. Use production-ready secrets and keys
3. Configure proper SMTP settings
4. Set up SSL/TLS termination
5. Configure backup strategies for PostgreSQL

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   PostgreSQL    │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   Database      │
│   Port 3000     │    │   Port 8000     │    │   Port 5432     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │     Redis       │
                       │   (Cache)       │
                       │   Port 6379     │
                       └─────────────────┘
```

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

## Security Features

- JWT token authentication
- Password hashing with bcrypt
- API key encryption
- Role-based access control
- Input validation and sanitization
- CORS protection