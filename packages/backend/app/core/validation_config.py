"""
Centralized validation configuration for different endpoint types.
Provides consistent validation rules across the application.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ValidationConfig:
    """Configuration for input validation."""
    max_string_length: int = 1000
    validate_emails: bool = False
    validate_urls: bool = False
    allow_html_fields: Optional[List[str]] = None
    sanitize_strings: bool = True
    remove_sensitive_fields: Optional[List[str]] = None


class ValidationRules:
    """Predefined validation rules for different endpoint categories."""
    
    # Authentication endpoints
    AUTH_LOGIN = ValidationConfig(
        max_string_length=255,
        validate_emails=True,
        sanitize_strings=True
    )
    
    AUTH_REGISTER = ValidationConfig(
        max_string_length=255,
        validate_emails=True,
        sanitize_strings=True
    )
    
    AUTH_PROFILE = ValidationConfig(
        max_string_length=255,
        sanitize_strings=True
    )
    
    AUTH_INVITATION = ValidationConfig(
        max_string_length=500,
        validate_emails=True,
        sanitize_strings=True
    )
    
    # Client management endpoints
    CLIENT_CREATE = ValidationConfig(
        max_string_length=500,
        validate_emails=True,
        validate_urls=True,
        sanitize_strings=True
    )
    
    CLIENT_UPDATE = ValidationConfig(
        max_string_length=500,
        validate_emails=True,
        validate_urls=True,
        sanitize_strings=True
    )
    
    CLIENT_N8N_CONFIG = ValidationConfig(
        max_string_length=1000,
        validate_urls=True,
        sanitize_strings=True,
        remove_sensitive_fields=["n8n_api_key", "api_key", "password", "secret"]
    )
    
    # Chat endpoints
    CHAT_MESSAGE = ValidationConfig(
        max_string_length=5000,
        sanitize_strings=True,
        allow_html_fields=[]  # No HTML allowed in chat messages
    )
    
    # Chatbot endpoints
    CHATBOT_CREATE = ValidationConfig(
        max_string_length=2000,
        sanitize_strings=True,
        allow_html_fields=["description", "system_prompt"]
    )
    
    CHATBOT_UPDATE = ValidationConfig(
        max_string_length=2000,
        sanitize_strings=True,
        allow_html_fields=["description", "system_prompt"]
    )
    
    # Workflow endpoints
    WORKFLOW_UPDATE = ValidationConfig(
        max_string_length=100,
        sanitize_strings=True
    )
    
    # Task endpoints
    TASK_TRIGGER = ValidationConfig(
        max_string_length=100,
        sanitize_strings=True
    )
    
    # Metrics endpoints
    METRICS_ADMIN = ValidationConfig(
        max_string_length=100,
        sanitize_strings=True
    )
    
    # Dependency endpoints
    DEPENDENCY_CREATE = ValidationConfig(
        max_string_length=1000,
        validate_urls=True,
        sanitize_strings=True
    )
    
    DEPENDENCY_UPDATE = ValidationConfig(
        max_string_length=1000,
        validate_urls=True,
        sanitize_strings=True
    )
    
    # File upload validation
    FILE_UPLOAD_IMAGE = ValidationConfig(
        max_string_length=255,  # For filename
        sanitize_strings=True
    )
    
    FILE_UPLOAD_DOCUMENT = ValidationConfig(
        max_string_length=255,  # For filename
        sanitize_strings=True
    )


class FileUploadRules:
    """File upload validation rules."""
    
    # Image uploads
    ALLOWED_IMAGE_TYPES = [
        "image/jpeg",
        "image/png", 
        "image/gif",
        "image/webp"
    ]
    
    # Document uploads
    ALLOWED_DOCUMENT_TYPES = [
        "application/pdf",
        "text/plain",
        "text/csv",
        "application/json"
    ]
    
    # Size limits (in bytes)
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_REQUEST_SIZE = 50 * 1024 * 1024  # 50MB
    
    # Content scanning patterns
    DANGEROUS_FILE_SIGNATURES = [
        b'\x4d\x5a',  # PE executable
        b'\x7f\x45\x4c\x46',  # ELF executable
        b'\xca\xfe\xba\xbe',  # Mach-O executable
        b'<script',  # JavaScript
        b'javascript:',  # JavaScript URL
        b'vbscript:',  # VBScript URL
    ]


class SecurityPatterns:
    """Security patterns for detection and prevention."""
    
    # XSS patterns (more comprehensive)
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'data:text/html',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
        r'onfocus\s*=',
        r'onblur\s*=',
        r'onchange\s*=',
        r'onsubmit\s*=',
        r'onkeydown\s*=',
        r'onkeyup\s*=',
        r'onkeypress\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
        r'<style[^>]*>.*?</style>',
        r'<form[^>]*>.*?</form>',
        r'<input[^>]*>',
        r'<textarea[^>]*>.*?</textarea>',
        r'expression\s*\(',
        r'url\s*\(',
        r'@import',
    ]
    
    # SQL injection patterns (more comprehensive)
    SQL_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|TRUNCATE|REPLACE)\b)',
        r'(\b(UNION|OR|AND)\s+\d+\s*=\s*\d+)',
        r'(\b(OR|AND)\s+[\'"]?\w+[\'"]?\s*=\s*[\'"]?\w+[\'"]?)',
        r'(--|#|/\*|\*/)',
        r'(\bxp_cmdshell\b)',
        r'(\bsp_executesql\b)',
        r'(\bsp_password\b)',
        r'(\bsp_helpdb\b)',
        r'(\bsp_configure\b)',
        r'(\bsp_adduser\b)',
        r'(\bsp_dropuser\b)',
        r'(\bsp_grantdbaccess\b)',
        r'(\bsp_revokedbaccess\b)',
        r'(\bsp_addrolemember\b)',
        r'(\bsp_droprolemember\b)',
        r'(\bINTO\s+OUTFILE\b)',
        r'(\bLOAD_FILE\b)',
        r'(\bINTO\s+DUMPFILE\b)',
        r'(\bSHOW\s+DATABASES\b)',
        r'(\bSHOW\s+TABLES\b)',
        r'(\bDESCRIBE\b)',
        r'(\bEXPLAIN\b)',
        r'(\bINFORMATION_SCHEMA\b)',
        r'(\bmysql\.user\b)',
        r'(\bpg_user\b)',
        r'(\bsys\.tables\b)',
        r'(\bsys\.columns\b)',
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r'\.\.',
        r'\/\.\.',
        r'\\\.\.',
        r'\.\.\/',
        r'\.\.\\',
        r'%2e%2e',
        r'%252e%252e',
        r'0x2e0x2e',
        r'..%2f',
        r'..%5c',
        r'%2e%2e%2f',
        r'%2e%2e%5c',
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r';\s*\w+',
        r'\|\s*\w+',
        r'&&\s*\w+',
        r'\|\|\s*\w+',
        r'`[^`]*`',
        r'\$\([^)]*\)',
        r'\${[^}]*}',
        r'>\s*/\w+',
        r'<\s*/\w+',
        r'nc\s+-',
        r'netcat\s+-',
        r'wget\s+',
        r'curl\s+',
        r'chmod\s+',
        r'chown\s+',
        r'rm\s+-',
        r'rmdir\s+',
        r'mkdir\s+',
        r'cp\s+',
        r'mv\s+',
        r'cat\s+',
        r'more\s+',
        r'less\s+',
        r'head\s+',
        r'tail\s+',
        r'grep\s+',
        r'find\s+',
        r'locate\s+',
        r'which\s+',
        r'whoami',
        r'id\s*$',
        r'uname\s+',
        r'ps\s+',
        r'kill\s+',
        r'killall\s+',
    ]


class ValidationMessages:
    """Standardized validation error messages."""
    
    INVALID_EMAIL = "Invalid email format"
    INVALID_URL = "Invalid URL format"
    STRING_TOO_LONG = "Input exceeds maximum length of {max_length} characters"
    INVALID_FILE_TYPE = "File type '{file_type}' not allowed"
    FILE_TOO_LARGE = "File size exceeds maximum of {max_size} bytes"
    MALICIOUS_CONTENT = "Content contains potentially dangerous patterns"
    XSS_DETECTED = "Cross-site scripting attempt detected"
    SQL_INJECTION_DETECTED = "SQL injection attempt detected"
    PATH_TRAVERSAL_DETECTED = "Path traversal attempt detected"
    COMMAND_INJECTION_DETECTED = "Command injection attempt detected"
    INVALID_JSON = "Invalid JSON format"
    MISSING_REQUIRED_FIELD = "Required field '{field}' is missing"
    INVALID_UUID = "Invalid UUID format"
    INVALID_DATE = "Invalid date format"
    RATE_LIMIT_EXCEEDED = "Rate limit exceeded. Please try again later"


def get_validation_config(endpoint_type: str) -> ValidationConfig:
    """
    Get validation configuration for a specific endpoint type.
    
    Args:
        endpoint_type: Type of endpoint (e.g., 'auth_login', 'client_create')
        
    Returns:
        ValidationConfig object with appropriate settings
    """
    config_map = {
        'auth_login': ValidationRules.AUTH_LOGIN,
        'auth_register': ValidationRules.AUTH_REGISTER,
        'auth_profile': ValidationRules.AUTH_PROFILE,
        'auth_invitation': ValidationRules.AUTH_INVITATION,
        'client_create': ValidationRules.CLIENT_CREATE,
        'client_update': ValidationRules.CLIENT_UPDATE,
        'client_n8n_config': ValidationRules.CLIENT_N8N_CONFIG,
        'chat_message': ValidationRules.CHAT_MESSAGE,
        'chatbot_create': ValidationRules.CHATBOT_CREATE,
        'chatbot_update': ValidationRules.CHATBOT_UPDATE,
        'workflow_update': ValidationRules.WORKFLOW_UPDATE,
        'task_trigger': ValidationRules.TASK_TRIGGER,
        'metrics_admin': ValidationRules.METRICS_ADMIN,
        'dependency_create': ValidationRules.DEPENDENCY_CREATE,
        'dependency_update': ValidationRules.DEPENDENCY_UPDATE,
        'file_upload_image': ValidationRules.FILE_UPLOAD_IMAGE,
        'file_upload_document': ValidationRules.FILE_UPLOAD_DOCUMENT,
    }
    
    return config_map.get(endpoint_type, ValidationConfig())  # Default config if not found