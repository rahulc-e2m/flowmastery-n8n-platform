"""Custom exceptions and error handlers"""

from typing import Any, Dict
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)


class FlowMasteryException(Exception):
    """Base exception for FlowMastery application"""
    
    def __init__(self, message: str, status_code: int = 500, details: Dict[str, Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class N8nConnectionError(FlowMasteryException):
    """n8n connection error"""
    
    def __init__(self, message: str = "Failed to connect to n8n instance"):
        super().__init__(message, status_code=503)


class N8nAPIError(FlowMasteryException):
    """n8n API error"""
    
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, status_code=status_code)


class AIServiceError(FlowMasteryException):
    """AI service error"""
    
    def __init__(self, message: str = "AI service unavailable"):
        super().__init__(message, status_code=503)


class CacheError(FlowMasteryException):
    """Cache service error"""
    
    def __init__(self, message: str = "Cache service error"):
        super().__init__(message, status_code=500)


async def flowmastery_exception_handler(request: Request, exc: FlowMasteryException):
    """Handle FlowMastery custom exceptions"""
    logger.error(f"FlowMastery exception: {exc.message}", extra={"details": exc.details})
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
            "type": exc.__class__.__name__
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "type": "HTTPException"
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation exceptions"""
    logger.warning(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "type": "ValidationError"
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "type": "InternalServerError"
        }
    )


def setup_exception_handlers(app: FastAPI):
    """Setup exception handlers for the application"""
    
    app.add_exception_handler(FlowMasteryException, flowmastery_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)