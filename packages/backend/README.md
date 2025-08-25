# FlowMastery Backend - Multi-Tenant Metrics Dashboard

Modern FastAPI backend for FlowMastery with multi-tenant architecture, authentication, and n8n integration.

## Features

- **Multi-Tenant Architecture**: Support for multiple clients with isolated data
- **Authentication & Authorization**: JWT-based auth with role-based access control
- **Invitation System**: Secure user registration via email invitations
- **n8n Integration**: Per-client n8n API configuration and metrics
- **Encrypted Storage**: Client API keys stored with encryption
- **FastAPI Framework**: Modern, fast web framework with auto-documentation
- **Async/Await Support**: Full asynchronous request handling
- **PostgreSQL Database**: Robust relational database with SQLAlchemy ORM
- **Redis Caching**: High-performance caching layer
- **Comprehensive Logging**: Structured JSON logging

## Architecture Overview

### User Roles
- **Admins**: Can invite users, manage clients, configure n8n APIs, view all metrics
- **Clients**: Can only view their own dashboard and workflow metrics

### Key Components
- **Users**: Admin and client users with JWT authentication
- **Clients**: Organizations with their own n8n instances
- **Invitations**: Secure registration system with expiring tokens
- **Metrics**: Real-time n8n workflow and execution metrics per client

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (for development)

### Development Setup

1. **Clone and navigate to backend**:
   ```bash
   cd packages/backend
   ```

2. **Start services with Docker**:
   ```bash
   python start-dev.py
   ```

   This will:
   - Start PostgreSQL and Redis containers
   - Create .env file from template
   - Run database migrations
   - Prompt to create first admin user
   - Start the FastAPI server

3. **Manual setup (alternative)**:
   ```bash
   # Start database services
   docker-compose -f docker-compose.dev.yml up -d
   
   # Install dependencies
   pip install -e .
   
   # Configure environment
   cp .env.example .env
   # Edit .env with your configuration
   
   # Run migrations
   alembic upgrade head
   
   # Create first admin user
   python create_admin.py
   
   # Start server
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

## Configuration

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/flowmastery

# Security
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email (for invitations)
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@flowmastery.com

# Frontend URL (for invitation links)
FRONTEND_URL=http://localhost:3000

# Redis
REDIS_URL=redis://localhost:6379/0
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/invitations` - Create invitation (admin only)
- `GET /api/v1/auth/invitations` - List invitations (admin only)
- `GET /api/v1/auth/invitations/{token}` - Get invitation details
- `POST /api/v1/auth/invitations/accept` - Accept invitation

### Client Management
- `POST /api/v1/clients/` - Create client (admin only)
- `GET /api/v1/clients/` - List all clients (admin only)
- `GET /api/v1/clients/{client_id}` - Get client details
- `PUT /api/v1/clients/{client_id}` - Update client (admin only)
- `POST /api/v1/clients/{client_id}/n8n-config` - Configure n8n API (admin only)
- `DELETE /api/v1/clients/{client_id}` - Delete client (admin only)

### Metrics
- `GET /api/v1/metrics/all` - All clients metrics (admin only)
- `GET /api/v1/metrics/client/{client_id}` - Client metrics
- `GET /api/v1/metrics/client/{client_id}/workflows` - Client workflow metrics
- `GET /api/v1/metrics/my-metrics` - Current client user's metrics
- `GET /api/v1/metrics/my-workflows` - Current client user's workflow metrics

### Health & Status
- `GET /` - Root endpoint with API info
- `GET /health` - Health check

## Usage Flow

### 1. Admin Setup
```bash
# Create first admin user
python create_admin.py
```

### 2. Admin Creates Client
```bash
curl -X POST "http://localhost:8000/api/v1/clients/" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp"}'
```

### 3. Admin Invites Client User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/invitations" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "client@acme.com",
    "role": "client",
    "client_id": 1
  }'
```

### 4. Client Accepts Invitation
```bash
curl -X POST "http://localhost:8000/api/v1/auth/invitations/accept" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "<invitation_token>",
    "password": "securepassword"
  }'
```

### 5. Admin Configures n8n API
```bash
curl -X POST "http://localhost:8000/api/v1/clients/1/n8n-config" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "n8n_api_url": "https://n8n.acme.com/api/v1",
    "n8n_api_key": "n8n_api_key_here"
  }'
```

### 6. View Metrics
```bash
# Client views their metrics
curl -X GET "http://localhost:8000/api/v1/metrics/my-metrics" \
  -H "Authorization: Bearer <client_token>"

# Admin views all metrics
curl -X GET "http://localhost:8000/api/v1/metrics/all" \
  -H "Authorization: Bearer <admin_token>"
```

## Database Schema

### Users Table
- `id`, `email`, `hashed_password`, `role`, `is_active`
- `client_id` (for client users), `created_by_admin_id`
- `last_login`, `created_at`, `updated_at`

### Clients Table
- `id`, `name`, `n8n_api_url`
- `n8n_api_key_encrypted` (encrypted storage)
- `created_by_admin_id`, `created_at`, `updated_at`

### Invitations Table
- `id`, `email`, `role`, `token`, `status`
- `expiry_date`, `client_id`, `invited_by_admin_id`
- `accepted_user_id`, `accepted_at`, `created_at`

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: bcrypt for password security
- **API Key Encryption**: Client n8n API keys encrypted at rest
- **Role-Based Access**: Strict permission controls
- **Invitation Expiry**: Time-limited invitation tokens
- **Input Validation**: Comprehensive request validation

## Development

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Running Tests
```bash
pytest
```

### Code Quality
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8

# Type checking
mypy .
```

## Production Deployment

1. **Install production dependencies**:
   ```bash
   pip install -e .[prod]
   ```

2. **Set production environment**:
   ```bash
   export DEBUG=false
   export SECRET_KEY=<strong-secret-key>
   export DATABASE_URL=<production-db-url>
   ```

3. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Create admin user**:
   ```bash
   python create_admin.py
   ```

5. **Run with Gunicorn**:
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## Troubleshooting

### Common Issues

1. **Database connection failed**: Ensure PostgreSQL is running and credentials are correct
2. **Redis connection failed**: Ensure Redis is running on the specified port
3. **Email not configured**: SMTP settings are optional for development
4. **n8n metrics not loading**: Check client's n8n API configuration

### Logs
```bash
# View application logs
tail -f logs/app.log

# View database queries (set DB_ECHO=true)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.