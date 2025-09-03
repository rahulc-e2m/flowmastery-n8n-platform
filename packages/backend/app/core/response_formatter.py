"""Standardized API response formatter and decorator"""

import functools
import uuid
import asyncio
from datetime import datetime
from typing import Any, Callable, Union, Type, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from app.schemas.api_standard import (
    StandardResponse, 
    ResponseStatus, 
    ErrorResponse,
    APIErrorCode,
    HTTP_STATUS_CODE_MAP,
    ValidationErrorResponse,
    NotFoundErrorResponse,
    UnauthorizedErrorResponse,
    ForbiddenErrorResponse,
    ConflictErrorResponse,
    RateLimitErrorResponse,
    ServiceUnavailableErrorResponse,
    ResourceCreatedResponse,
    ResourceUpdatedResponse,
    ResourceDeletedResponse
)


def format_response(
    message: str = None,
    status: ResponseStatus = ResponseStatus.SUCCESS,
    response_model: Type[BaseModel] = None,
    status_code: int = None
):
    """
    Enhanced decorator to format API responses in a standardized format.
    
    Args:
        message (str, optional): Default message for successful responses
        status (ResponseStatus, optional): Default status for responses
        response_model (Type[BaseModel], optional): Specific response model to use
        status_code (int, optional): HTTP status code for successful responses
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request object if present
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request and 'request' in kwargs:
                request = kwargs['request']
            
            # Generate request ID if not present
            request_id = str(uuid.uuid4()) if request else None
            
            try:
                # Execute the original function
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
                # If result is already a StandardResponse, return as-is
                if isinstance(result, StandardResponse):
                    if result.request_id is None:
                        result.request_id = request_id
                    if result.timestamp is None:
                        result.timestamp = datetime.utcnow()
                    return result
                
                # If result is an ErrorResponse, ensure it has request info
                if isinstance(result, ErrorResponse):
                    if result.request_id is None:
                        result.request_id = request_id
                    if result.path is None and request:
                        result.path = request.url.path
                    return JSONResponse(
                        content=result.model_dump(mode='json'),
                        status_code=_get_status_code_from_error(result)
                    )
                
                # Handle 204 No Content responses (should not have body)
                if status_code == 204:
                    return JSONResponse(content=None, status_code=204)
                
                # Use specific response model if provided
                if response_model:
                    if hasattr(response_model, 'model_validate'):
                        response_data = response_model.model_validate({
                            "data": result,
                            "message": message,
                            "request_id": request_id
                        })
                    else:
                        response_data = response_model(
                            data=result,
                            message=message,
                            request_id=request_id
                        )
                    
                    # Set appropriate status code
                    response_status_code = status_code or 200
                    if isinstance(response_data, ResourceCreatedResponse):
                        response_status_code = 201
                        
                    return JSONResponse(
                        content=response_data.model_dump(mode='json'),
                        status_code=response_status_code
                    )
                
                # Wrap the result in a StandardResponse
                response_data = StandardResponse(
                    status=status,
                    data=result,
                    message=message,
                    request_id=request_id
                )
                
                # Check if we have a FastAPI Response object (for auth endpoints with cookies)
                response_obj = None
                
                # Check args for Response object (look for FastAPI Response type)
                from fastapi import Response
                for arg in args:
                    if isinstance(arg, Response):
                        response_obj = arg
                        break
                
                # Also check kwargs
                if not response_obj and 'response' in kwargs:
                    if isinstance(kwargs['response'], Response):
                        response_obj = kwargs['response']
                
                if response_obj:
                    # This is an auth endpoint - check if cookies have been set
                    has_cookies = False
                    if hasattr(response_obj, '_cookies') and response_obj._cookies:
                        has_cookies = True
                    
                    if has_cookies:
                        # Cookies are set, modify the response object directly to preserve them
                        response_obj.media_type = "application/json"
                        response_obj.body = response_data.model_dump_json(by_alias=True).encode('utf-8')
                        response_obj.status_code = status_code or 200
                        return response_obj
                    else:
                        # No cookies, return standard JSON response
                        return JSONResponse(
                            content=response_data.model_dump(mode='json'),
                            status_code=status_code or 200
                        )
                else:
                    # Regular endpoint - return standard JSON response
                    return JSONResponse(
                        content=response_data.model_dump(mode='json'),
                        status_code=status_code or 200
                    )
                
            except ValidationError as e:
                # Handle Pydantic validation errors
                error_response = _validation_error_to_response(e, request, request_id)
                return JSONResponse(
                    content=error_response.model_dump(mode='json'),
                    status_code=422
                )
                
            except HTTPException as e:
                # Convert HTTP exceptions to standardized error format
                error_response = _http_exception_to_error_response(e, request, request_id)
                return JSONResponse(
                    content=error_response.model_dump(mode='json'),
                    status_code=e.status_code
                )
                
            except Exception as e:
                # Convert general exceptions to standardized error format
                error_response = _exception_to_error_response(e, request, request_id)
                return JSONResponse(
                    content=error_response.model_dump(mode='json'),
                    status_code=500
                )
        
        return wrapper
    return decorator


def _validation_error_to_response(
    exc: ValidationError,
    request: Request = None,
    request_id: str = None
) -> ValidationErrorResponse:
    """Convert Pydantic ValidationError to standardized ValidationErrorResponse"""
    from app.schemas.api_standard import ErrorResponseDetail
    
    details = []
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        details.append(ErrorResponseDetail(
            code=error["type"].upper(),
            message=error["msg"],
            field=field_path,
            value=error.get("input")
        ))
    
    return ValidationErrorResponse(
        message="Validation failed",
        details=details,
        timestamp=datetime.utcnow(),
        request_id=request_id,
        path=request.url.path if request else None
    )


def _http_exception_to_error_response(
    exc: HTTPException, 
    request: Request = None, 
    request_id: str = None
) -> ErrorResponse:
    """Convert HTTPException to standardized ErrorResponse"""
    # Use specific error response types for common status codes
    error_response_map = {
        401: UnauthorizedErrorResponse,
        403: ForbiddenErrorResponse,
        404: NotFoundErrorResponse,
        409: ConflictErrorResponse,
        422: ValidationErrorResponse,
        429: RateLimitErrorResponse,
        503: ServiceUnavailableErrorResponse,
    }
    
    response_class = error_response_map.get(exc.status_code, ErrorResponse)
    
    # Map status codes to error codes
    status_code_map = {
        400: APIErrorCode.BAD_REQUEST,
        401: APIErrorCode.UNAUTHORIZED,
        403: APIErrorCode.FORBIDDEN,
        404: APIErrorCode.NOT_FOUND,
        409: APIErrorCode.CONFLICT,
        422: APIErrorCode.VALIDATION_ERROR,
        429: APIErrorCode.RATE_LIMITED,
        500: APIErrorCode.INTERNAL_ERROR,
        503: APIErrorCode.SERVICE_UNAVAILABLE
    }
    
    error_code = status_code_map.get(exc.status_code, APIErrorCode.INTERNAL_ERROR)
    
    response_data = {
        "error": error_code.value.lower(),
        "message": exc.detail or "An error occurred",
        "code": error_code.value,
        "timestamp": datetime.utcnow(),
        "request_id": request_id,
        "path": request.url.path if request else None
    }
    
    # Add retry_after for rate limit responses
    if exc.status_code == 429 and hasattr(exc, 'headers') and exc.headers:
        retry_after = exc.headers.get('Retry-After')
        if retry_after:
            response_data['retry_after'] = int(retry_after)
    
    return response_class(**response_data)


def _exception_to_error_response(
    exc: Exception, 
    request: Request = None, 
    request_id: str = None
) -> ErrorResponse:
    """Convert general exceptions to standardized ErrorResponse"""
    return ErrorResponse(
        error="internal_error",
        message="An unexpected error occurred",
        code="INTERNAL_ERROR",
        timestamp=datetime.utcnow(),
        request_id=request_id,
        path=request.url.path if request else None
    )


def _get_status_code_from_error(error_response: ErrorResponse) -> int:
    """Derive HTTP status code from error response"""
    # Use the enhanced mapping from API standards
    if hasattr(error_response, 'code') and error_response.code:
        try:
            error_code = APIErrorCode(error_response.code)
            return HTTP_STATUS_CODE_MAP.get(error_code, 500)
        except ValueError:
            pass
    
    # Fallback to error string mapping
    error_code_map = {
        "bad_request": 400,
        "unauthorized": 401,
        "forbidden": 403,
        "not_found": 404,
        "conflict": 409,
        "validation_error": 422,
        "rate_limited": 429,
        "internal_error": 500,
        "service_unavailable": 503
    }
    
    return error_code_map.get(error_response.error, 500)


# For backward compatibility, also provide a sync version
def format_response_sync(
    message: str = None,
    status: ResponseStatus = ResponseStatus.SUCCESS
):
    """
    Synchronous version of format_response decorator.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract request object if present
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request and 'request' in kwargs:
                request = kwargs['request']
            
            # Generate request ID if not present
            request_id = str(uuid.uuid4()) if request else None
            
            try:
                # Execute the original function
                result = func(*args, **kwargs)
                
                # If result is already a StandardResponse, return as-is
                if isinstance(result, StandardResponse):
                    if result.request_id is None:
                        result.request_id = request_id
                    if result.timestamp is None:
                        result.timestamp = datetime.utcnow()
                    return result
                
                # If result is an ErrorResponse, ensure it has request info
                if isinstance(result, ErrorResponse):
                    if result.request_id is None:
                        result.request_id = request_id
                    if result.path is None and request:
                        result.path = request.url.path
                    return JSONResponse(
                        content=result.model_dump(mode='json'),
                        status_code=_get_status_code_from_error(result)
                    )
                
                # Wrap the result in a StandardResponse
                return StandardResponse(
                    status=status,
                    data=result,
                    message=message,
                    request_id=request_id
                )
                
            except HTTPException as e:
                # Convert HTTP exceptions to standardized error format
                error_response = _http_exception_to_error_response(e, request, request_id)
                return JSONResponse(
                    content=error_response.model_dump(mode='json'),
                    status_code=e.status_code
                )
                
            except Exception as e:
                # Convert general exceptions to standardized error format
                error_response = _exception_to_error_response(e, request, request_id)
                return JSONResponse(
                    content=error_response.model_dump(mode='json'),
                    status_code=500
                )
        
        return wrapper
    return decorator