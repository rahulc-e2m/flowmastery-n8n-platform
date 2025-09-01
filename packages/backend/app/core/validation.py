"""
Comprehensive input validation and sanitization utilities.
Provides protection against XSS, SQL injection, and other malicious input.
"""

import re
import html
import bleach
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class InputSanitizer:
    """Comprehensive input sanitization utility."""
    
    # Allowed HTML tags for rich text (very restrictive)
    ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
    ALLOWED_ATTRIBUTES = {}
    
    # Common XSS patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
        r'onfocus\s*=',
        r'onblur\s*=',
        r'onchange\s*=',
        r'onsubmit\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
        r'<style[^>]*>.*?</style>',
    ]
    
    # SQL injection patterns
    SQL_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)',
        r'(\b(UNION|OR|AND)\s+\d+\s*=\s*\d+)',
        r'(\b(OR|AND)\s+[\'"]?\w+[\'"]?\s*=\s*[\'"]?\w+[\'"]?)',
        r'(--|#|/\*|\*/)',
        r'(\bxp_cmdshell\b)',
        r'(\bsp_executesql\b)',
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, allow_html: bool = False) -> str:
        """
        Sanitize a string input.
        
        Args:
            value: Input string to sanitize
            allow_html: Whether to allow safe HTML tags
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return str(value)
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Detect and log potential XSS attempts
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential XSS attempt detected: {pattern}")
                break
        
        # Detect and log potential SQL injection attempts
        for pattern in cls.SQL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential SQL injection attempt detected: {pattern}")
                break
        
        if allow_html:
            # Use bleach to sanitize HTML
            value = bleach.clean(
                value,
                tags=cls.ALLOWED_TAGS,
                attributes=cls.ALLOWED_ATTRIBUTES,
                strip=True
            )
        else:
            # Escape HTML entities
            value = html.escape(value)
        
        # Additional XSS protection - remove dangerous patterns
        for pattern in cls.XSS_PATTERNS:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE)
        
        return value.strip()
    
    @classmethod
    def sanitize_email(cls, email: str) -> str:
        """
        Sanitize email input.
        
        Args:
            email: Email address to sanitize
            
        Returns:
            Sanitized email
        """
        if not isinstance(email, str):
            return ""
        
        # Basic email pattern validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        # Remove dangerous characters
        email = re.sub(r'[<>"\'\(\)&]', '', email)
        
        # Validate format
        if not re.match(email_pattern, email):
            logger.warning(f"Invalid email format detected: {email}")
            return ""
        
        return email.lower().strip()
    
    @classmethod
    def sanitize_url(cls, url: str) -> str:
        """
        Sanitize URL input.
        
        Args:
            url: URL to sanitize
            
        Returns:
            Sanitized URL or empty string if invalid
        """
        if not isinstance(url, str):
            return ""
        
        # Remove dangerous protocols
        dangerous_protocols = ['javascript:', 'vbscript:', 'data:', 'file:']
        url_lower = url.lower()
        
        for protocol in dangerous_protocols:
            if url_lower.startswith(protocol):
                logger.warning(f"Dangerous protocol detected in URL: {protocol}")
                return ""
        
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ['http', 'https', '']:
                logger.warning(f"Invalid URL scheme: {parsed.scheme}")
                return ""
            
            return url.strip()
        except Exception:
            logger.warning(f"Invalid URL format: {url}")
            return ""
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitize filename input.
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            Sanitized filename
        """
        if not isinstance(filename, str):
            return ""
        
        # Remove path traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*\x00-\x1f]', '', filename)
        
        # Limit length
        filename = filename[:255]
        
        return filename.strip()
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any], allow_html_fields: List[str] = None) -> Dict[str, Any]:
        """
        Recursively sanitize dictionary data.
        
        Args:
            data: Dictionary to sanitize
            allow_html_fields: List of field names that can contain HTML
            
        Returns:
            Sanitized dictionary
        """
        if allow_html_fields is None:
            allow_html_fields = []
        
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize the key itself
            clean_key = cls.sanitize_string(str(key))
            
            if isinstance(value, str):
                allow_html = key in allow_html_fields
                sanitized[clean_key] = cls.sanitize_string(value, allow_html=allow_html)
            elif isinstance(value, dict):
                sanitized[clean_key] = cls.sanitize_dict(value, allow_html_fields)
            elif isinstance(value, list):
                sanitized[clean_key] = [
                    cls.sanitize_string(str(item)) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[clean_key] = value
        
        return sanitized


class ValidationMiddleware:
    """Middleware for input validation."""
    
    @staticmethod
    def validate_content_type(content_type: str) -> bool:
        """
        Validate content type for file uploads.
        
        Args:
            content_type: MIME type to validate
            
        Returns:
            True if content type is allowed
        """
        allowed_types = [
            'text/plain',
            'text/csv',
            'application/json',
            'image/jpeg',
            'image/png',
            'image/gif',
            'application/pdf',
        ]
        
        return content_type in allowed_types
    
    @staticmethod
    def validate_file_size(size: int, max_size: int = 10 * 1024 * 1024) -> bool:
        """
        Validate file size.
        
        Args:
            size: File size in bytes
            max_size: Maximum allowed size in bytes (default 10MB)
            
        Returns:
            True if size is within limits
        """
        return 0 < size <= max_size
    
    @staticmethod
    def validate_request_size(content_length: int, max_size: int = 50 * 1024 * 1024) -> bool:
        """
        Validate request content length.
        
        Args:
            content_length: Request content length in bytes
            max_size: Maximum allowed size in bytes (default 50MB)
            
        Returns:
            True if size is within limits
        """
        return 0 <= content_length <= max_size


# Convenience functions for common use cases
def sanitize_user_input(data: Union[str, Dict[str, Any]], allow_html: bool = False) -> Union[str, Dict[str, Any]]:
    """
    Sanitize user input data.
    
    Args:
        data: Input data to sanitize
        allow_html: Whether to allow HTML in string fields
        
    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        return InputSanitizer.sanitize_string(data, allow_html=allow_html)
    elif isinstance(data, dict):
        return InputSanitizer.sanitize_dict(data)
    else:
        return data


def validate_and_sanitize_email(email: str) -> Optional[str]:
    """
    Validate and sanitize email address.
    
    Args:
        email: Email to validate and sanitize
        
    Returns:
        Sanitized email or None if invalid
    """
    sanitized = InputSanitizer.sanitize_email(email)
    return sanitized if sanitized else None


def validate_and_sanitize_url(url: str) -> Optional[str]:
    """
    Validate and sanitize URL.
    
    Args:
        url: URL to validate and sanitize
        
    Returns:
        Sanitized URL or None if invalid
    """
    sanitized = InputSanitizer.sanitize_url(url)
    return sanitized if sanitized else None