"""A pretend chat model that gives fixed answers instead of calling OpenAI.

The integration tests check the support workflow itself - the validation rules,
the database writes, the approval pause - not the AI. So we hand the workflow
this fake model, which just reads its answers off a script. Every test run then
behaves the same way, with no network call.

During one support request the workflow asks the model for four things:

1. what the customer wants, and which order   -> with_structured_output(ParsedRequest)
2. a summary of what it "found"               -> bind_tools(...)
3. what to do: refund / cancel / nothing      -> with_structured_output(ProposedAction)
4. the reply text to send to the customer     -> ainvoke(...)

``LLMScript`` holds the answer to each of those four questions.
``DeterministicChatModel`` hands them back when the workflow asks.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from langchain_core.messages import AIMessage

from order_resolver.agent.state import ParsedRequest, ProposedAction, SupportIntent


@dataclass(frozen=True)
class LLMScript:
    """The fixed AI answers for one support request.

    One field per question the workflow asks the model (see the module docstring).
    """

    intent: SupportIntent  # what the customer wants: refund, cancel, track, ...
    proposed_action: ProposedAction  # what to do about it: refund/cancel/no_action (+ amount)
    order_id: UUID | None = None  # which order, when the message names one
    investigation_summary: str = "Investigation complete."  # free text; tests don't assert on it
    customer_reply: str = "Here is an update on your request."  # the message sent back

    @property
    def parsed_request(self) -> ParsedRequest:
        # Packs `intent` + `order_id` into the object the first node expects.
        return ParsedRequest(
            intent=self.intent,
            order_id=self.order_id,
            explanation=self.investigation_summary,
        )


def scripted_action(
    action: str,
    *,
    amount: Decimal | None = None,
    reason: str = "scripted decision",
    confidence: float = 0.9,
) -> ProposedAction:
    """Short helper for building a ProposedAction in a test."""
    return ProposedAction(
        action=action,  # type: ignore[arg-type]
        reason=reason,
        amount=amount,
        confidence=confidence,
    )


class _StructuredRunnable:
    """Returned by ``with_structured_output``. Every call hands back the one
    scripted value it was created with."""

    def __init__(self, payload: ParsedRequest | ProposedAction) -> None:
        self._payload = payload

    async def ainvoke(
        self,
        _input: Any,
        _config: Any = None,
        **_kwargs: Any,
    ) -> ParsedRequest | ProposedAction:
        return self._payload


class _InvestigationRunnable:
    """Returned by ``bind_tools``. Gives back one message with no tool calls,
    which tells the investigator node "nothing more to look up" so it moves
    straight on to asking for the proposed action.
    """

    def __init__(self, summary: str) -> None:
        self._summary = summary

    async def ainvoke(
        self,
        _input: Any,
        _config: Any = None,
        **_kwargs: Any,
    ) -> AIMessage:
        return AIMessage(content=self._summary)


class DeterministicChatModel:
    """Stands in for ``ChatOpenAI`` in tests. Never uses the network - every
    answer comes from the ``LLMScript`` it was built with."""

    def __init__(self, script: LLMScript) -> None:
        self._script = script

    def with_structured_output(
        self,
        schema: type,
        **_kwargs: Any,
    ) -> _StructuredRunnable:
       if schema == ParsedRequest:
           return _StructuredRunnable(self._script.parsed_request)
       if schema == ProposedAction:
           return _StructuredRunnable(self._script.proposed_action)
       else:
            raise NotImplementedError("Unknown structured output")

    def bind_tools(self, _tools: Any, **_kwargs: Any) -> _InvestigationRunnable:
        return _InvestigationRunnable(self._script.investigation_summary)

    async def ainvoke(
        self,
        _input: Any,
        _config: Any = None,
        **_kwargs: Any,
    ) -> AIMessage:
        return AIMessage(content=self._script.customer_reply)
