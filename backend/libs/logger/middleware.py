# middleware.py
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from .log import get_logger
from .tracing import span_id_ctx, trace_id_ctx

log = get_logger("http")

TRACE_HEADER = "x-trace-id"
HEALTH_PATHS = {"/health/live", "/health/ready"}


def _otel_trace_ids() -> tuple[str | None, str | None]:
    """
    Return (trace_id, span_id) from OpenTelemetry if available & valid.
    """
    return None, None


class TraceContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        skip_log = request.url.path in HEALTH_PATHS
        # --------------------------------------------------
        # 1. Try OpenTelemetry first
        # --------------------------------------------------
        trace_id, span_id = _otel_trace_ids()
        # --------------------------------------------------
        # 2. Fallback: header → uuid
        # --------------------------------------------------
        if not trace_id:
            trace_id = request.headers.get(TRACE_HEADER) or uuid.uuid4().hex
        if not span_id:
            span_id = uuid.uuid4().hex[:16]
        # --------------------------------------------------
        # 3. Bind contextvars
        # --------------------------------------------------
        trace_token = trace_id_ctx.set(trace_id)
        span_token = span_id_ctx.set(span_id)
        start_time = time.time()
        try:
            if not skip_log:
                log.info(
                    "request",
                    method=request.method,
                    path=request.url.path,
                )

            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            if not skip_log:
                log.info(
                    "response",
                    process_time=f"{process_time:.2f}ms",
                    status_code=response.status_code,
                )
            # 3. Gắn trace_id vào response header
            response.headers[TRACE_HEADER] = trace_id
            return response

        finally:
            trace_id_ctx.reset(trace_token)
            span_id_ctx.reset(span_token)
