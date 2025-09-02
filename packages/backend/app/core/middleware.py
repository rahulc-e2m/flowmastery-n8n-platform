"""
Security middleware for the FastAPI application.
Handles input validation, security headers, and request sanitization.
"""

import json
import logging
from typing import Callable, Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .validation import InputSanitizer, ValidationMiddleware

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware."""
    
    def __init__(self, app: ASGIApp, max_request_size: int = 50 * 1024 * 1024):
        super().__init__(app)
        self.max_request_size = max_request_size
        self.sanitizer = InputSanitizer()
        self.validator = ValidationMiddleware()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security middleware."""
        
        # Validate request size
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                size = int(content_length)
                if not self.validator.validate_request_size(size, self.max_request_size):
                    logger.warning(f"Request size too large: {size} bytes")
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Request entity too large"}
                    )
            except ValueError:
                pass
        
        # Validate content type for file uploads
        content_type = request.headers.get('content-type', '')
        if content_type.startswith('multipart/form-data'):
            # File upload validation will be handled in the endpoint
            pass
        elif content_type.startswith('application/json'):
            # Sanitize JSON payload
            try:
                body = await request.body()
                if body:
                    data = json.loads(body)
                    if isinstance(data, dict):
                        sanitized_data = self.sanitizer.sanitize_dict(data)
                        # Replace request body with sanitized data
                        request._body = json.dumps(sanitized_data).encode()
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning(f"Invalid JSON in request: {e}")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid JSON format"}
                )
        
        # Sanitize query parameters
        if request.query_params:
            sanitized_params = {}
            for key, value in request.query_params.items():
                clean_key = self.sanitizer.sanitize_string(key)
                clean_value = self.sanitizer.sanitize_string(value)
                sanitized_params[clean_key] = clean_value
            
            # Log if any dangerous patterns were detected
            if sanitized_params != dict(request.query_params):
                logger.warning("Query parameters were sanitized")
        
        # Process the request
        response = await call_next(request)
        
        # Add security headers
        self._add_security_headers(response)
        
        return response
    
    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response."""
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # HTTP Strict Transport Security
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=()"
        )


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Specialized middleware for input validation."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.sanitizer = InputSanitizer()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate and sanitize all input data."""
        
        # Skip validation for certain endpoints
        skip_paths = ['/docs', '/redoc', '/openapi.json', '/health']
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        # Validate and sanitize request data
        try:
            await self._validate_request(request)
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        
        return await call_next(request)
    
    async def _validate_request(self, request: Request) -> None:
        """Validate request data."""
        
        # Check for suspicious patterns in URL path
        path = request.url.path
        suspicious_patterns = [
            '../', '..\\', '/etc/', '/proc/', '/sys/',
            'SELECT ', 'INSERT ', 'UPDATE ', 'DELETE ',
            '<script', 'javascript:', 'vbscript:'
        ]
        
        for pattern in suspicious_patterns:
            if pattern.lower() in path.lower():
                logger.warning(f"Suspicious pattern in URL path: {pattern}")
                raise HTTPException(status_code=400, detail="Invalid request")
        
        # Validate User-Agent header
        user_agent = request.headers.get('user-agent', '')
        if len(user_agent) > 1000:  # Unusually long user agent
            logger.warning("Unusually long User-Agent header")
            raise HTTPException(status_code=400, detail="Invalid request")
        
        # Check for SQL injection in headers
        for header_name, header_value in request.headers.items():
            if any(pattern in header_value.lower() for pattern in ['union select', 'drop table', 'insert into']):
                logger.warning(f"Potential SQL injection in header {header_name}")
                raise HTTPException(status_code=400, detail="Invalid request")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for secure request/response logging."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log requests and responses securely."""
        
        # Sanitize URL for logging (remove sensitive parameters)
        sanitized_url = self._sanitize_url_for_logging(str(request.url))
        
        # Log request (without sensitive data)
        logger.info(f"Request: {request.method} {sanitized_url}")
        
        # Process request
        response = await call_next(request)
        
        # Log response status
        logger.info(f"Response: {response.status_code} for {request.method} {sanitized_url}")
        
        return response
    
    def _sanitize_url_for_logging(self, url: str) -> str:
        """Remove sensitive parameters from URL for logging."""
        
        # Parameters that should not be logged
        sensitive_params = ['password', 'token', 'key', 'secret', 'auth']
        
        # Simple sanitization - replace sensitive parameter values
        for param in sensitive_params:
            if f'{param}=' in url.lower():
                # Replace the value with [REDACTED]
                import re
                pattern = f'({param}=)[^&]*'
                url = re.sub(pattern, r'\1[REDACTED]', url, flags=re.IGNORECASE)
        
        return url


# Error handling middleware
class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for secure error handling."""
    
    def __init__(self, app: ASGIApp, debug: bool = False):
        super().__init__(app)
        self.debug = debug
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors securely."""
        
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
            
            if self.debug:
                # In debug mode, return detailed error
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": str(e),
                        "type": type(e).__name__
                    }
                )
            else:
                # In production, return generic error
                return JSONResponse(
                    status_code=500,
                    content={"detail": "Internal server error"}
                )


def setup_middleware(app):
    """Setup all security middleware for the FastAPI application."""
    from ..config import settings
    
    # Add error handling middleware
    app.add_middleware(
        ErrorHandlingMiddleware,
        debug=settings.DEBUG
    )
    
    # Add security middleware
    app.add_middleware(SecurityMiddleware)
    
    # Add input validation middleware
    app.add_middleware(InputValidationMiddleware)
    
    # Add logging middleware
    app.add_middleware(LoggingMiddleware)