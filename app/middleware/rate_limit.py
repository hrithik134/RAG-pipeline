"""
Rate limiting middleware using SlowAPI.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from app.config import settings

logger = logging.getLogger(__name__)


def get_request_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.
    Uses IP address as the default identifier.
    Can be extended to use API keys, user IDs, etc.
    """
    # Get IP address
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Get first IP in X-Forwarded-For chain
        ip = forwarded.split(",")[0].strip()
    else:
        ip = get_remote_address(request)
    
    # Could be extended to check for API key in headers
    # api_key = request.headers.get("X-API-Key")
    # if api_key:
    #     return f"api_key:{api_key}"
    
    return f"ip:{ip}"


# Create limiter instance
limiter = Limiter(
    key_func=get_request_identifier,
    default_limits=[f"{settings.rate_limit_requests}/{settings.rate_limit_period}second"] if settings.rate_limit_enabled else [],
    storage_uri=settings.rate_limit_storage_url if settings.rate_limit_enabled else None,
    enabled=settings.rate_limit_enabled,
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    Returns a structured error response with retry information.
    """
    from uuid import uuid4
    
    # Extract retry-after from exception if available
    retry_after: Optional[int] = None
    if hasattr(exc, "detail") and isinstance(exc.detail, dict):
        retry_after = exc.detail.get("retry_after")
    
    # Calculate retry_after from rate limit if not provided
    if not retry_after:
        # Default to 60 seconds
        retry_after = 60
    
    # Get the rate limit that was exceeded
    limit_str = "See rate limit headers"
    if hasattr(exc, "detail"):
        if isinstance(exc.detail, str):
            limit_str = exc.detail
        elif isinstance(exc.detail, dict) and "limit" in exc.detail:
            limit_str = exc.detail["limit"]
    
    error_response = {
        "error": {
            "code": "RATE_LIMIT_EXCEEDED",
            "message": "Too many requests. Please try again later.",
            "details": {
                "endpoint": str(request.url.path),
                "limit": limit_str,
                "suggestion": "Please wait before making more requests"
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": str(uuid4())
        },
        "retry_after": retry_after,
        "limit": limit_str,
        "success": False
    }
    
    logger.warning(
        f"Rate limit exceeded for {get_request_identifier(request)} "
        f"on {request.url.path}"
    )
    
    return JSONResponse(
        status_code=429,
        content=error_response,
        headers={"Retry-After": str(retry_after)}
    )

