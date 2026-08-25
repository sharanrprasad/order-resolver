"""Synchronize embedded company policy documents with the database."""

from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from langchain_core.embeddings import Embeddings
from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.orm import Session, sessionmaker

from order_resolver.core.config import PROJECT_ROOT, settings
from order_resolver.db.models import CompanyPolicy
from order_resolver.db.session import SessionLocal
from order_resolver.dependencies.model_factory import build_embedding_model

POLICY_DOCUMENTS_PATH = PROJECT_ROOT / "docs"


def policy_document_id(source: str) -> UUID:
    """Return the stable UUID used for a policy source across environments."""
    return uuid5(NAMESPACE_URL, f"order-resolver/company-policies/{source}")


def load_policy_documents(documents_path: Path) -> dict[str, str]:
    paths = sorted(documents_path.glob("*.md"))
    if not paths:
        raise RuntimeError(f"No Markdown policy documents found in {documents_path}")

    documents: dict[str, str] = {}
    for path in paths:
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            raise RuntimeError(f"Policy document is empty: {path.name}")
        documents[path.name] = content

    return documents


def seed_policy_documents(
    documents_path: Path = POLICY_DOCUMENTS_PATH,
    embedding_model_name: str = settings.embedding_model,
    embedding_model: Embeddings | None = None,
    session_factory: sessionmaker[Session] = SessionLocal,
) -> None:
    if not embedding_model_name.strip():
        raise RuntimeError("EMBEDDING_MODEL must not be empty")

    documents = load_policy_documents(documents_path)

    with session_factory() as session:
        existing_rows = session.execute(
            select(
                CompanyPolicy.id,
                CompanyPolicy.source,
                CompanyPolicy.content,
                CompanyPolicy.embedding_model,
            )
        ).all()

    existing = {
        source: (policy_id, content, existing_model)
        for policy_id, source, content, existing_model in existing_rows
    }
    sources_to_embed = [
        source
        for source, content in documents.items()
        if source not in existing
        or existing[source][1:] != (content, embedding_model_name)
    ]
    sources_to_normalize = [
        source
        for source in documents
        if source in existing
        and source not in sources_to_embed
        and existing[source][0] != policy_document_id(source)
    ]
    stale_sources = sorted(existing.keys() - documents.keys())

    if not sources_to_embed and not sources_to_normalize and not stale_sources:
        print("Company policies are already up to date; policy seed skipped.")
        return

    embeddings: list[list[float]] = []
    if sources_to_embed:
        if embedding_model is None:
            if not settings.openai_api_key.strip():
                raise RuntimeError(
                    "OPENAI_API_KEY is required to embed company policies"
                )
            embedding_model = build_embedding_model(
                model_name=embedding_model_name,
                api_key=settings.openai_api_key,
            )

        embeddings = embedding_model.embed_documents(
            [documents[source] for source in sources_to_embed]
        )
        if len(embeddings) != len(sources_to_embed):
            raise RuntimeError(
                "Embedding model returned an unexpected number of embeddings"
            )

    with session_factory.begin() as session:
        for source, embedding in zip(sources_to_embed, embeddings, strict=True):
            values = {
                "id": policy_document_id(source),
                "content": documents[source],
                "embedding": embedding,
                "embedding_model": embedding_model_name,
            }
            if source in existing:
                statement = (
                    update(CompanyPolicy)
                    .where(CompanyPolicy.source == source)
                    .values(**values, updated_at=func.now())
                )
            else:
                statement = insert(CompanyPolicy).values(source=source, **values)
            session.execute(statement)

        for source in sources_to_normalize:
            session.execute(
                update(CompanyPolicy)
                .where(CompanyPolicy.source == source)
                .values(id=policy_document_id(source), updated_at=func.now())
            )

        if stale_sources:
            session.execute(
                delete(CompanyPolicy).where(CompanyPolicy.source.in_(stale_sources))
            )

    unchanged_count = len(documents) - len(sources_to_embed) - len(sources_to_normalize)
    print(
        "Company policy seed complete: "
        f"{len(sources_to_embed)} embedded, "
        f"{len(sources_to_normalize)} IDs normalized, "
        f"{len(stale_sources)} removed, "
        f"{unchanged_count} unchanged."
    )


if __name__ == "__main__":
    seed_policy_documents()
