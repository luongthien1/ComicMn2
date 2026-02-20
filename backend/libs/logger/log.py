import json
import logging
import logging.config
import os
from collections.abc import Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from .tracing import span_id_ctx, trace_id_ctx

# --------------------------------------------------
# Logging bootstrap
# --------------------------------------------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LOGGING_CONFIG_FILE = os.path.join(BASE_DIR, "logging.ini")

logging.config.fileConfig(LOGGING_CONFIG_FILE, disable_existing_loggers=False)


# --------------------------------------------------
# Types
# --------------------------------------------------
LogEventContext = dict[str, Any]
_log_context: ContextVar[LogEventContext] = ContextVar(
    "log_context",
    default={},
)

# --------------------------------------------------
# Helpers
# --------------------------------------------------


def _json_default(obj: Any) -> str:
    """Safe JSON fallback (datetime, enum, etc)."""
    try:
        return str(obj)
    except Exception:
        return "<unserializable>"


class StructuredLogEvent:
    __slots__ = ("event", "data")

    def __init__(self, event: str, data: Mapping[str, Any]) -> None:
        self.event = event
        self.data = {
            "_event": event,
            **data,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.data,
            sort_keys=True,
            default=_json_default,
            ensure_ascii=False,
        )

    def __str__(self) -> str:
        return self.to_json()


class StructuredLogger:
    __slots__ = ("_logger",)

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    # ------------------------------
    # Context handling
    # ------------------------------
    def update_context(self, **fields: Any) -> None:
        ctx = _log_context.get().copy()
        ctx.update(fields)
        _log_context.set(ctx)

    @contextmanager
    def context(self, **fields: Any):
        token = _log_context.set({**_log_context.get(), **fields})
        try:
            yield
        finally:
            _log_context.reset(token)

    # ------------------------------
    # Core logging
    # ------------------------------
    def _log(
        self,
        level: int,
        msg: str,
        *,
        exc_info: bool = False,
        stack_info: bool = False,
        stacklevel: int = 2,  # log theo caller
        **event_fields: Any,
    ) -> None:
        trace_id = trace_id_ctx.get()
        span_id = span_id_ctx.get()

        data = {
            **_log_context.get(),
            **event_fields,
        }

        if trace_id:
            data["trace_id"] = trace_id
        if span_id:
            data["span_id"] = span_id

        event = StructuredLogEvent(msg, data)

        self._logger.log(
            level,
            event,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel + 1,
            extra=data,
        )

    # ------------------------------
    # Public API
    # ------------------------------

    def debug(self, msg: str, **kw: Any) -> None:
        self._log(logging.DEBUG, msg, **kw)

    def info(self, msg: str, **kw: Any) -> None:
        self._log(logging.INFO, msg, **kw)

    def warning(self, msg: str, **kw: Any) -> None:
        self._log(logging.WARNING, msg, **kw)

    def error(self, msg: str, **kw: Any) -> None:
        self._log(logging.ERROR, msg, **kw)

    def exception(self, msg: str, **kw: Any) -> None:
        self._log(
            logging.ERROR,
            msg,
            exc_info=True,
            stack_info=True,
            **kw,
        )

    def critical(self, msg: str, **kw: Any) -> None:
        self._log(logging.CRITICAL, msg, **kw)


logger = StructuredLogger(logging.getLogger())


# --------------------------------------------------
# Factory
# --------------------------------------------------
def get_logger(name: str) -> StructuredLogger:
    return StructuredLogger(logging.getLogger(name))
