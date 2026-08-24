from collections.abc import Awaitable
from typing import Annotated, Protocol, TypeAlias
from uuid import UUID

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import Runnable
from langgraph.graph.message import add_messages

from order_resolver.agent.state import (
    ParsedRequest,
    ProposedAction,
    SupportState,
    SupportStateBase,
)


class SupportNodeReturnType(SupportStateBase, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    customer_id: UUID


# Protocol here means any class that has this call method which also includes functions.
class SupportModelNode(Protocol):
    def __call__(
        self,
        state: SupportState,
    ) -> Awaitable[SupportNodeReturnType]: ...


IntentModel: TypeAlias = Runnable[LanguageModelInput, ParsedRequest]
InvestigationModel: TypeAlias = Runnable[LanguageModelInput, AIMessage]
ActionModel: TypeAlias = Runnable[LanguageModelInput, ProposedAction]
ResponseModel: TypeAlias = Runnable[LanguageModelInput, BaseMessage]
