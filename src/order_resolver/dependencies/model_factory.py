from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from order_resolver.core.config import settings


def build_chat_model(
    model_name: str = settings.openai_model,
    api_key: str = settings.openai_api_key,
) -> BaseChatModel:
    """Build the chat model shared by the support graph's nodes."""
    return ChatOpenAI(
        model=model_name,
        api_key=SecretStr(api_key),
    )
