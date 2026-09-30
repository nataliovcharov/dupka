from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# counts per client IP, kept in memory. fine for one API process,
# several would need a shared store like Redis.
# behind a proxy, uvicorn has to trust its X-Forwarded-For header
# (--forwarded-allow-ips), otherwise every user looks like the proxy
limiter = Limiter(key_func=get_remote_address)


def rate_limit_exceeded(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Same error shape as the rest of the API, so the app can show it."""
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many reports from this device, try again later"},
    )
