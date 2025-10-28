"""
Security headers middleware for enhanced API security.
"""

import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    Headers added:
    - X-Content-Type-Options: Prevent MIME type sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable browser XSS protection
    - Strict-Transport-Security: Enforce HTTPS (in production)
    - Content-Security-Policy: Control resource loading
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Enable browser XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content Security Policy (allow CDN for Swagger UI)
        # Allow scripts and styles from CDN for API documentation
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com"
        )
        
        # Only add HSTS in production
        from app.config import settings
        if settings.is_production:
            # Enforce HTTPS for 1 year
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        
        # Add custom API version header
        response.headers["X-API-Version"] = settings.app_version
        
        return response


async def add_security_headers(request: Request, call_next: Callable) -> Response:
    """
    Simpler function-based middleware for security headers.
    Alternative to class-based middleware.
    """
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # Allow CDN for Swagger UI
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://fastapi.tiangolo.com"
    )
    
    # Add HSTS in production
    from app.config import settings
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    
    response.headers["X-API-Version"] = settings.app_version
    
    return response

