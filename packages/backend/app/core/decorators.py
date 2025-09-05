"""
Security decorators for API endpoints.
Provides input validation and sanitization decorators.
"""

import functools
import logging
from typing import Any, Callable, Dict, List, Optional
from fastapi import HTTPException, Request
from .validation import InputSanitizer, ValidationMiddleware

logger = logging.getLogger(__name__)


def validate_input(
    sanitize_strings: bool = True,
    allow_html_fields: Optional[List[str]] = None,
    skip_sql_check_fields: Optional[List[str]] = None,
    max_string_length: int = 10000,
    validate_emails: bool = True,
    validate_urls: bool = True,
    endpoint_type: Optional[str] = None
):
    """
    Decorator to validate and sanitize input data for API endpoints.
    
    Args:
        sanitize_strings: Whether to sanitize string inputs
        allow_html_fields: List of field names that can contain HTML
        skip_sql_check_fields: List of field names to skip SQL injection checks
        max_string_length: Maximum allowed string length
        validate_emails: Whether to validate email fields
        validate_urls: Whether to validate URL fields
        endpoint_type: Predefined endpoint type for automatic configuration
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Use predefined configuration if endpoint_type is provided
            if endpoint_type:
                from .validation_config import get_validation_config
                config = get_validation_config(endpoint_type)
                sanitize_strings = config.sanitize_strings
                allow_html_fields = config.allow_html_fields or []
                max_string_length = config.max_string_length
                validate_emails = config.validate_emails
                validate_urls = config.validate_urls
            
            # Find request data in arguments
            request_data = None
            for arg in args:
                if hasattr(arg, '__dict__') and hasattr(arg, '__annotations__'):
                    # This is likely a Pydantic model
                    request_data = arg.dict() if hasattr(arg, 'dict') else arg.__dict__
                    break
            
            if request_data and sanitize_strings:
                sanitizer = InputSanitizer()
                
                # Validate string lengths
                for key, value in request_data.items():
                    if isinstance(value, str) and len(value) > max_string_length:
                        logger.warning(f"String too long in field {key}: {len(value)} chars")
                        raise HTTPException(
                            status_code=400,
                            detail=f"Field '{key}' exceeds maximum length of {max_string_length} characters"
                        )
                
                # Sanitize the data
                if allow_html_fields is None:
                    allow_html_fields = []
                if skip_sql_check_fields is None:
                    skip_sql_check_fields = []
                
                sanitized_data = sanitizer.sanitize_dict(request_data, allow_html_fields, skip_sql_check_fields)
                
                # Validate emails
                if validate_emails:
                    email_fields = ['email', 'user_email', 'contact_email']
                    for field in email_fields:
                        if field in sanitized_data:
                            email = sanitizer.sanitize_email(sanitized_data[field])
                            if not email:
                                raise HTTPException(
                                    status_code=400,
                                    detail=f"Invalid email format in field '{field}'"
                                )
                            sanitized_data[field] = email
                
                # Validate URLs
                if validate_urls:
                    url_fields = ['url', 'website', 'callback_url', 'redirect_url', 'n8n_api_url', 
                                 'guide_link', 'documentation_link', 'where_to_get']
                    for field in url_fields:
                        if field in sanitized_data:
                            url = sanitizer.sanitize_url(sanitized_data[field])
                            if sanitized_data[field] and not url:
                                raise HTTPException(
                                    status_code=400,
                                    detail=f"Invalid URL format in field '{field}'"
                                )
                            sanitized_data[field] = url
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_by_type(endpoint_type: str):
    """
    Simplified decorator that uses predefined validation configuration.
    
    Args:
        endpoint_type: Type of endpoint (e.g., 'auth_login', 'client_create')
    """
    return validate_input(endpoint_type=endpoint_type)


def validate_file_upload(
    allowed_types: Optional[List[str]] = None,
    max_size: int = 10 * 1024 * 1024,  # 10MB
    scan_content: bool = True
):
    """
    Decorator to validate file uploads.
    
    Args:
        allowed_types: List of allowed MIME types
        max_size: Maximum file size in bytes
        scan_content: Whether to scan file content for malicious patterns
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Look for file uploads in the request
            for arg in args:
                if hasattr(arg, 'content_type') and hasattr(arg, 'size'):
                    # This looks like an uploaded file
                    file = arg
                    
                    # Validate content type
                    if allowed_types and file.content_type not in allowed_types:
                        logger.warning(f"Invalid file type: {file.content_type}")
                        raise HTTPException(
                            status_code=400,
                            detail=f"File type '{file.content_type}' not allowed"
                        )
                    
                    # Validate file size
                    if hasattr(file, 'size') and file.size > max_size:
                        logger.warning(f"File too large: {file.size} bytes")
                        raise HTTPException(
                            status_code=400,
                            detail=f"File size exceeds maximum of {max_size} bytes"
                        )
                    
                    # Validate filename
                    if hasattr(file, 'filename'):
                        sanitizer = InputSanitizer()
                        clean_filename = sanitizer.sanitize_filename(file.filename)
                        if not clean_filename:
                            raise HTTPException(
                                status_code=400,
                                detail="Invalid filename"
                            )
                    
                    # Scan file content for malicious patterns
                    if scan_content and hasattr(file, 'read'):
                        content = await file.read()
                        await file.seek(0)  # Reset file pointer
                        
                        # Check for executable signatures
                        dangerous_signatures = [
                            b'\x4d\x5a',  # PE executable
                            b'\x7f\x45\x4c\x46',  # ELF executable
                            b'\xca\xfe\xba\xbe',  # Mach-O executable
                            b'<script',  # JavaScript
                            b'javascript:',  # JavaScript URL
                            b'vbscript:',  # VBScript URL
                        ]
                        
                        for signature in dangerous_signatures:
                            if signature in content[:1024]:  # Check first 1KB
                                logger.warning("Dangerous file signature detected")
                                raise HTTPException(
                                    status_code=400,
                                    detail="File contains potentially dangerous content"
                                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit_by_content(
    max_requests: int = 10,
    window_seconds: int = 60,
    content_fields: Optional[List[str]] = None
):
    """
    Decorator to implement content-based rate limiting.
    
    Args:
        max_requests: Maximum requests per window
        window_seconds: Time window in seconds
        content_fields: Fields to use for content-based limiting
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # This is a placeholder for content-based rate limiting
            # In a real implementation, you would track requests by content hash
            # and use Redis or another cache to store rate limit data
            
            if content_fields:
                # Extract content for hashing
                content_hash = None
                for arg in args:
                    if hasattr(arg, '__dict__'):
                        data = arg.__dict__ if hasattr(arg, '__dict__') else {}
                        content_parts = []
                        for field in content_fields:
                            if field in data:
                                content_parts.append(str(data[field]))
                        
                        if content_parts:
                            import hashlib
                            content_hash = hashlib.sha256(
                                ''.join(content_parts).encode()
                            ).hexdigest()
                            break
                
                if content_hash:
                    # Here you would implement the actual rate limiting logic
                    # using Redis or another cache system
                    logger.info(f"Content-based rate limiting for hash: {content_hash[:8]}...")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_json_schema(schema: Dict[str, Any]):
    """
    Decorator to validate JSON input against a schema.
    
    Args:
        schema: JSON schema to validate against
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # This would implement JSON schema validation
            # For now, it's a placeholder
            logger.info("JSON schema validation applied")
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def sanitize_response(
    remove_sensitive_fields: Optional[List[str]] = None,
    sanitize_strings: bool = True
):
    """
    Decorator to sanitize response data.
    
    Args:
        remove_sensitive_fields: List of field names to remove from response
        sanitize_strings: Whether to sanitize string fields in response
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            sensitive_fields = remove_sensitive_fields
            if sensitive_fields is None:
                sensitive_fields = ['password', 'secret', 'token', 'key']
            
            # Sanitize response if it's a dictionary
            if isinstance(result, dict):
                sanitized_result = {}
                sanitizer = InputSanitizer()
                
                for key, value in result.items():
                    # Remove sensitive fields
                    if key.lower() in [field.lower() for field in sensitive_fields]:
                        continue
                    
                    # Sanitize string values
                    if sanitize_strings and isinstance(value, str):
                        sanitized_result[key] = sanitizer.sanitize_string(value)
                    else:
                        sanitized_result[key] = value
                
                return sanitized_result
            
            return result
        
        return wrapper
    return decorator