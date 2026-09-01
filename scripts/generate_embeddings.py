"""Generate an embedding for an ad-hoc input string.

Prints the vector in pgvector's ``[v1,v2,...]`` text format so it can be pasted
into a ``psql`` console for manual similarity queries against ``company_policies``.

Usage:
    uv run python scripts/generate_embeddings.py "customer wants a refund for a damaged item"
    uv run python scripts/generate_embeddings.py        # falls back to INPUT_TEXT below
"""

import sys

from langchain_core.embeddings import Embeddings

from order_resolver.core.config import settings
from order_resolver.dependencies.model_factory import build_embedding_model

# Used when no text is passed on the command line.
INPUT_TEXT = "customer wants a refund for a damaged item"


def generate_embedding(
    text: str,
    embedding_model_name: str = settings.embedding_model,
    embedding_model: Embeddings | None = None,
) -> list[float]:
    """Return the embedding vector for ``text`` using the configured model."""
    normalized_text = text.strip()
    if not normalized_text:
        raise RuntimeError("Input text must not be empty")
    if not embedding_model_name.strip():
        raise RuntimeError("EMBEDDING_MODEL must not be empty")

    if embedding_model is None:
        if not settings.openai_api_key.strip():
            raise RuntimeError("OPENAI_API_KEY is required to generate embeddings")
        embedding_model = build_embedding_model(
            model_name=embedding_model_name,
            api_key=settings.openai_api_key,
        )

    return embedding_model.embed_query(normalized_text)


def format_pgvector(embedding: list[float]) -> str:
    """Render an embedding as a pgvector ``[v1,v2,...]`` literal."""
    return "[" + ",".join(repr(value) for value in embedding) + "]"


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) or INPUT_TEXT
    vector = generate_embedding(text)
    print(
        f"-- model={settings.embedding_model} dims={len(vector)} text={text!r}",
        file=sys.stderr,
    )
    print(format_pgvector(vector))
