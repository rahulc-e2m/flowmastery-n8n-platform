#!/usr/bin/env python3
"""
Start script for FlowMastery Backend
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📡 Debug mode: {settings.DEBUG}")
    print(f"🔗 n8n Integration: {'✅' if settings.N8N_API_URL else '❌'}")
    print(f"🤖 AI Services: {'✅' if settings.GEMINI_API_KEY else '❌'}")
    print(f"📊 Redis Cache: {settings.REDIS_URL}")
    print(f"🌐 CORS Origins: {', '.join(settings.CORS_ORIGINS)}")
    print(f"📝 Log Level: {settings.LOG_LEVEL}")
    print()
    print(f"🌍 Server will start at: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print()
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.DEBUG
    )