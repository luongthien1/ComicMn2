# app/logging/tracing.py
from contextvars import ContextVar

# Mỗi request có context riêng → an toàn async
trace_id_ctx: ContextVar[str | None] = ContextVar(
    "trace_id",
    default=None,
)

span_id_ctx: ContextVar[str | None] = ContextVar(
    "span_id",
    default=None,
)
