from collections.abc import Awaitable, Callable
from typing import Any

from order_resolver.agent.state import SupportState

SupportModelNode = Callable[
    [SupportState],
    Awaitable[dict[str, Any]]
]