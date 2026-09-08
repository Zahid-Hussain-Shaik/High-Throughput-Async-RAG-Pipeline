import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("requests")


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info("request_complete request_id=%s method=%s path=%s status_code=%s duration_ms=%.2f", request_id, request.method, request.url.path, response.status_code, (time.perf_counter()-start)*1000)
        return response
