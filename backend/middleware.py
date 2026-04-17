"""
Custom middleware for logging, error handling, and rate limiting.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from collections import defaultdict
import time
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging all requests and responses.
    
    Logs include:
    - Request method and path
    - Response status code
    - Processing time
    - Client IP address
    - Request ID for tracing
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(time.time())
        request.state.request_id = request_id
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"from {client_ip}"
        )
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            # Log response
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"{response.status_code} - {process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"ERROR - {process_time:.3f}s - {str(e)}",
                exc_info=True
            )
            raise


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling uncaught exceptions.
    
    Provides:
    - Consistent error response format
    - Error logging with stack traces
    - Request ID tracking
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
            
        except HTTPException as e:
            # FastAPI HTTPException - let it pass through
            raise
            
        except ValueError as e:
            # Validation errors
            logger.warning(f"Validation error: {e}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": str(e),
                    "error_type": "ValidationError",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unhandled error: {e}", exc_info=True)
            
            request_id = getattr(request.state, "request_id", "unknown")
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "An internal error occurred. Please try again later.",
                    "error_type": type(e).__name__,
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests.
    
    Implements sliding window rate limiting per IP address.
    Configurable limits per minute and per hour.
    """
    
    def __init__(self, app, per_minute: int = 20, per_hour: int = 100):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application
            per_minute: Max requests per minute per IP
            per_hour: Max requests per hour per IP
        """
        super().__init__(app)
        self.per_minute = per_minute
        self.per_hour = per_hour
        
        # Storage: {ip: [(timestamp, count), ...]}
        self.minute_requests: Dict[str, list] = defaultdict(list)
        self.hour_requests: Dict[str, list] = defaultdict(list)
        
        # Excluded paths (health checks, docs, and ALL admin endpoints)
        self.excluded_paths = {"/", "/api/health", "/api/docs", "/api/redoc", "/api/openapi.json"}
        self.excluded_prefixes = ("/api/admin/", "/api/admin")
    
    def _clean_old_requests(self, requests_list: list, time_window: timedelta):
        """Remove requests older than time window"""
        cutoff = datetime.utcnow() - time_window
        return [req for req in requests_list if req > cutoff]
    
    def _check_rate_limit(self, ip: str) -> Tuple[bool, str]:
        """
        Check if IP is within rate limits.
        
        Args:
            ip: Client IP address
            
        Returns:
            Tuple of (allowed, error_message)
        """
        now = datetime.utcnow()
        
        # Clean old requests
        self.minute_requests[ip] = self._clean_old_requests(
            self.minute_requests[ip],
            timedelta(minutes=1)
        )
        self.hour_requests[ip] = self._clean_old_requests(
            self.hour_requests[ip],
            timedelta(hours=1)
        )
        
        # Check per-minute limit
        if len(self.minute_requests[ip]) >= self.per_minute:
            return False, f"Rate limit exceeded: {self.per_minute} requests per minute"
        
        # Check per-hour limit
        if len(self.hour_requests[ip]) >= self.per_hour:
            return False, f"Rate limit exceeded: {self.per_hour} requests per hour"
        
        # Add current request
        self.minute_requests[ip].append(now)
        self.hour_requests[ip].append(now)
        
        return True, ""
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths and admin endpoints
        if request.url.path in self.excluded_paths or request.url.path.startswith(self.excluded_prefixes):
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        allowed, error_message = self._check_rate_limit(client_ip)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": error_message,
                    "retry_after": 60  # seconds
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit-Minute": str(self.per_minute),
                    "X-RateLimit-Limit-Hour": str(self.per_hour),
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            self.per_minute - len(self.minute_requests[client_ip])
        )
        response.headers["X-RateLimit-Limit-Hour"] = str(self.per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            self.per_hour - len(self.hour_requests[client_ip])
        )
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding security headers.
    
    Adds headers for:
    - XSS protection
    - Content type sniffing protection
    - Frame options
    - Content security policy (relaxed for Swagger UI)
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy - Relaxed for Swagger UI
        # Allow CDN resources for API documentation
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            "font-src 'self' data:; "
        )
        
        return response