# FlowMastery Backend - New Architecture

A modern, properly structured FastAPI backend for FlowMastery with n8n integration.

## Architecture Overview

```
packages/backend-new/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Application settings
│   │   └── database.py         # Database configuration
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py         # Authentication & authorization
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── middleware.py       # Custom middleware
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py            # API dependencies
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py      # Main API router
│   │       ├── endpoints/
│   │       │   ├── __init__.py
│   │       │   ├── health.py
│   │       │   ├── chat.py
│   │       │   ├── metrics.py
│   │       │   └── config.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── n8n/
│   │   │   ├── __init__.py
│   │   │   ├── client.py      # n8n API client
│   │   │   ├── chatbot.py     # Chatbot service
│   │   │   ├── metrics.py     # Metrics service
│   │   │   └── config.py      # Configuration service
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── gemini.py      # Gemini AI client
│   │   │   └── base.py        # Base AI client
│   │   └── cache/
│   │       ├── __init__.py
│   │       └── redis.py       # Redis cache service
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py            # Base model classes
│   │   ├── chat.py            # Chat models
│   │   └── metrics.py         # Metrics models
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── chat.py            # Chat schemas
│   │   ├── metrics.py         # Metrics schemas
│   │   └── config.py          # Configuration schemas
│   └── utils/
│       ├── __init__.py
│       ├── logging.py         # Logging utilities
│       └── helpers.py         # Helper functions
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   ├── test_services/
│   └── test_utils/
├── alembic/                   # Database migrations
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── .env.example
├── pyproject.toml
└── README.md
```

## Key Features

- **Modern FastAPI Architecture**: Clean separation of concerns
- **n8n Integration**: Full API integration with chatbot capabilities
- **AI Services**: Gemini AI integration for intelligent responses
- **Metrics & Analytics**: Comprehensive n8n metrics collection
- **Caching**: Redis-based caching for performance
- **Security**: JWT authentication, rate limiting, CORS
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Testing**: Comprehensive test suite with pytest
- **Monitoring**: Prometheus metrics, structured logging
- **Docker**: Production-ready containerization

## Quick Start

1. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements/dev.txt
   ```

3. Run the application:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Migration from Old Backend

The new backend integrates all functionality from the old backend while providing:
- Better code organization
- Improved error handling
- Enhanced security
- Better testing capabilities
- Production-ready deployment