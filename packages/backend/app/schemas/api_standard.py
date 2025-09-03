"""Standardized API response schemas"""

from datetime import datetime
from typing import Optional, Any, Dict, List, Union, Generic, TypeVar, Literal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# Type variables for generic responses
T = TypeVar('T')
E = TypeVar('E')
DataT = TypeVar('DataT')

class ResponseStatus(str, Enum):
    """Standard response status codes"""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"

class StandardResponse(BaseModel, Generic[T]):
    """Standard API response format"""
    status: ResponseStatus = Field(
        default=ResponseStatus.SUCCESS,
        description="Overall status of the response"
    )
    data: Optional[T] = Field(
        default=None,
        description="Response data payload"
    )
    message: Optional[str] = Field(
        default=None,
        description="Human-readable message"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of the response"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the request"
    )
    
    model_config = {"json_schema_extra": {
        "examples": [{
            "status": "success",
            "data": {"example": "data"},
            "message": "Operation completed successfully",
            "timestamp": "2023-01-01T00:00:00Z",
            "request_id": "req_123456"
        }]
    }}

class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response format"""
    items: List[T] = Field(
        default=[],
        description="List of items in the current page"
    )
    total: int = Field(
        default=0,
        description="Total number of items across all pages"
    )
    page: int = Field(
        default=1,
        description="Current page number"
    )
    size: int = Field(
        default=50,
        description="Number of items per page"
    )
    total_pages: int = Field(
        default=0,
        description="Total number of pages"
    )

class ErrorResponseDetail(BaseModel):
    """Detailed error information"""
    code: str = Field(
        description="Machine-readable error code"
    )
    message: str = Field(
        description="Human-readable error message"
    )
    field: Optional[str] = Field(
        default=None,
        description="Field related to the error, if applicable"
    )
    value: Optional[Any] = Field(
        default=None,
        description="Value that caused the error, if applicable"
    )

class ErrorResponse(BaseModel):
    """Standard error response format"""
    status: ResponseStatus = Field(
        default=ResponseStatus.ERROR,
        description="Status indicating an error occurred"
    )
    error: str = Field(
        description="Brief error description"
    )
    message: Optional[str] = Field(
        default=None,
        description="Detailed error message"
    )
    code: Optional[str] = Field(
        default=None,
        description="Application-specific error code"
    )
    details: Optional[List[ErrorResponseDetail]] = Field(
        default=None,
        description="Detailed error information"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of the error"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the request"
    )
    path: Optional[str] = Field(
        default=None,
        description="Path of the request that caused the error"
    )
    
    model_config = {"json_schema_extra": {
        "examples": [{
            "status": "error",
            "error": "validation_error",
            "message": "One or more fields failed validation",
            "code": "VALIDATION_001",
            "details": [{
                "code": "VALUE_REQUIRED",
                "message": "Field is required",
                "field": "email",
                "value": None
            }],
            "timestamp": "2023-01-01T00:00:00Z",
            "request_id": "req_123456",
            "path": "/api/v1/users"
        }]
    }}

class HealthInfo(BaseModel):
    """Health check information"""
    status: str = Field(description="Service status")
    version: str = Field(description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthCheckResponse(StandardResponse[HealthInfo]):
    """Standard health check response"""
    pass


# Enhanced response models for specific use cases
class ResourceCreatedResponse(BaseModel, Generic[DataT]):
    """Standard response for resource creation"""
    status: Literal["success"] = "success"
    data: DataT
    message: str = "Resource created successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    location: Optional[str] = Field(None, description="Location of the created resource")


class ResourceUpdatedResponse(BaseModel, Generic[DataT]):
    """Standard response for resource updates"""
    status: Literal["success"] = "success"
    data: DataT
    message: str = "Resource updated successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class ResourceDeletedResponse(BaseModel):
    """Standard response for resource deletion"""
    status: Literal["success"] = "success"
    message: str = "Resource deleted successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    resource_id: Optional[str] = Field(None, description="ID of the deleted resource")


class ListResponse(BaseModel, Generic[DataT]):
    """Standard response for list operations with pagination"""
    status: Literal["success"] = "success"
    data: PaginatedResponse[DataT]
    message: str = "Resources retrieved successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class BulkOperationResponse(BaseModel):
    """Standard response for bulk operations"""
    status: Literal["success", "partial"] = "success"
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    successful_count: int = Field(description="Number of successful operations")
    failed_count: int = Field(default=0, description="Number of failed operations")
    errors: Optional[List[ErrorResponseDetail]] = Field(default=None, description="Details of failed operations")


class ValidationErrorResponse(ErrorResponse):
    """Enhanced validation error response"""
    error: Literal["validation_error"] = "validation_error"
    code: Literal["VALIDATION_ERROR"] = "VALIDATION_ERROR"


class NotFoundErrorResponse(ErrorResponse):
    """Standard not found error response"""
    error: Literal["not_found"] = "not_found"
    code: Literal["NOT_FOUND"] = "NOT_FOUND"
    message: str = "Resource not found"


class UnauthorizedErrorResponse(ErrorResponse):
    """Standard unauthorized error response"""
    error: Literal["unauthorized"] = "unauthorized"
    code: Literal["UNAUTHORIZED"] = "UNAUTHORIZED"
    message: str = "Authentication required"


class ForbiddenErrorResponse(ErrorResponse):
    """Standard forbidden error response"""
    error: Literal["forbidden"] = "forbidden"
    code: Literal["FORBIDDEN"] = "FORBIDDEN"
    message: str = "Access denied"


class ConflictErrorResponse(ErrorResponse):
    """Standard conflict error response"""
    error: Literal["conflict"] = "conflict"
    code: Literal["CONFLICT"] = "CONFLICT"
    message: str = "Resource conflict"


class RateLimitErrorResponse(ErrorResponse):
    """Standard rate limit error response"""
    error: Literal["rate_limited"] = "rate_limited"
    code: Literal["RATE_LIMITED"] = "RATE_LIMITED"
    message: str = "Rate limit exceeded"
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retrying")


class ServiceUnavailableErrorResponse(ErrorResponse):
    """Standard service unavailable error response"""
    error: Literal["service_unavailable"] = "service_unavailable"
    code: Literal["SERVICE_UNAVAILABLE"] = "SERVICE_UNAVAILABLE"
    message: str = "Service temporarily unavailable"


# Common error codes enum for consistency
class APIErrorCode(str, Enum):
    """Standard API error codes"""
    # Client errors (4xx)
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    CONFLICT = "CONFLICT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    
    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    GATEWAY_TIMEOUT = "GATEWAY_TIMEOUT"
    
    # Business logic errors
    RESOURCE_LOCKED = "RESOURCE_LOCKED"
    DEPENDENCY_FAILED = "DEPENDENCY_FAILED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


# HTTP status code mapping
HTTP_STATUS_CODE_MAP = {
    APIErrorCode.BAD_REQUEST: 400,
    APIErrorCode.UNAUTHORIZED: 401,
    APIErrorCode.FORBIDDEN: 403,
    APIErrorCode.NOT_FOUND: 404,
    APIErrorCode.METHOD_NOT_ALLOWED: 405,
    APIErrorCode.CONFLICT: 409,
    APIErrorCode.VALIDATION_ERROR: 422,
    APIErrorCode.RATE_LIMITED: 429,
    APIErrorCode.INTERNAL_ERROR: 500,
    APIErrorCode.SERVICE_UNAVAILABLE: 503,
    APIErrorCode.GATEWAY_TIMEOUT: 504,
    APIErrorCode.RESOURCE_LOCKED: 423,
    APIErrorCode.DEPENDENCY_FAILED: 424,
    APIErrorCode.QUOTA_EXCEEDED: 429,
    APIErrorCode.CONFIGURATION_ERROR: 500,
}