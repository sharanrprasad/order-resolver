import logging
from collections.abc import Awaitable, Callable
from typing import Any

from order_resolver.services import ResourceNotFoundError

logger = logging.getLogger(__name__)

ToolResult = dict[str, Any]


async def call_service(
    operation: Callable[[], Awaitable[Any]],
) -> ToolResult:
    """Execute a service operation and map failures to a stable tool response."""
    try:
        data = await operation()
        if hasattr(data, "model_dump"):
            data = data.model_dump(mode="json")
        elif isinstance(data, list):
            data = [
                item.model_dump(mode="json")
                if hasattr(item, "model_dump")
                else item
                for item in data
            ]
        return {"ok": True, "data": data}
    except ResourceNotFoundError as exc:
        return {
            "ok": False,
            "error": {"code": "not_found", "message": str(exc)},
        }
    except ValueError as exc:
        return {
            "ok": False,
            "error": {"code": "invalid_request", "message": str(exc)},
        }
    except Exception:
        logger.exception("Tool service operation failed")
        return {
            "ok": False,
            "error": {
                "code": "service_unavailable",
                "message": "The requested data is temporarily unavailable.",
            },
        }
