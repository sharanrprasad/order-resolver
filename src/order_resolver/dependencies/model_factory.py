from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
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


def build_embedding_model(
    model_name: str = settings.embedding_model,
    api_key: str = settings.openai_api_key,
) -> Embeddings:
    """Build the embedding model used to ingest company policy documents."""
    return OpenAIEmbeddings(
        model=model_name,
        api_key=SecretStr(api_key),
    )
