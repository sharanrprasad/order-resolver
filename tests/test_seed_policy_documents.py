from collections.abc import Callable
from pathlib import Path
from runpy import run_path
from typing import cast
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from langchain_core.embeddings import Embeddings

SEED_SCRIPT = run_path(
    str(Path(__file__).resolve().parents[1] / "scripts" / "seed_policy_documents.py"),
    run_name="seed_policy_documents",
)
policy_document_id = cast(
    Callable[[str], UUID],
    SEED_SCRIPT["policy_document_id"],
)
load_policy_documents = cast(
    Callable[[Path], dict[str, str]],
    SEED_SCRIPT["load_policy_documents"],
)
seed_policy_documents = cast(
    Callable[..., None],
    SEED_SCRIPT["seed_policy_documents"],
)


class StubEmbeddingModel(Embeddings):
    def __init__(self, document_embeddings: list[list[float]]) -> None:
        self.document_embeddings = document_embeddings
        self.document_inputs: list[str] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.document_inputs = texts
        return self.document_embeddings

    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError


def session_factory_with_existing(
    rows: list[tuple[UUID, str, str, str]],
) -> tuple[MagicMock, MagicMock]:
    session_factory = MagicMock()

    read_session = MagicMock()
    read_session.execute.return_value.all.return_value = rows
    read_context = MagicMock()
    read_context.__enter__.return_value = read_session
    session_factory.return_value = read_context

    write_session = MagicMock()
    write_context = MagicMock()
    write_context.__enter__.return_value = write_session
    session_factory.begin.return_value = write_context

    return session_factory, write_session


def write_policy(path: Path, name: str, content: str) -> None:
    path.joinpath(name).write_text(content, encoding="utf-8")


def test_policy_document_id_is_deterministic() -> None:
    refund_id = policy_document_id("refund-policy.md")

    assert refund_id == policy_document_id("refund-policy.md")
    assert refund_id != policy_document_id("cancellation-policy.md")


def test_load_policy_documents_rejects_empty_document(tmp_path: Path) -> None:
    write_policy(tmp_path, "empty.md", "   ")

    with pytest.raises(RuntimeError, match="Policy document is empty: empty.md"):
        load_policy_documents(tmp_path)


def test_unchanged_policies_are_not_written_or_embedded(tmp_path: Path) -> None:
    source = "refund-policy.md"
    content = "# Refund policy"
    write_policy(tmp_path, source, content)
    session_factory, _ = session_factory_with_existing(
        [(policy_document_id(source), source, content, "test-model")]
    )
    embedding_model = StubEmbeddingModel([])

    seed_policy_documents(
        documents_path=tmp_path,
        embedding_model_name="test-model",
        embedding_model=embedding_model,
        session_factory=session_factory,
    )

    assert embedding_model.document_inputs == []
    session_factory.begin.assert_not_called()


def test_existing_random_id_is_normalized_without_embedding(tmp_path: Path) -> None:
    source = "refund-policy.md"
    content = "# Refund policy"
    write_policy(tmp_path, source, content)
    session_factory, write_session = session_factory_with_existing(
        [(uuid4(), source, content, "test-model")]
    )
    embedding_model = StubEmbeddingModel([])

    seed_policy_documents(
        documents_path=tmp_path,
        embedding_model_name="test-model",
        embedding_model=embedding_model,
        session_factory=session_factory,
    )

    assert embedding_model.document_inputs == []
    statements = [str(call.args[0]) for call in write_session.execute.call_args_list]
    assert any("UPDATE company_policies" in statement for statement in statements)


def test_new_policy_is_inserted_with_deterministic_id(tmp_path: Path) -> None:
    source = "refund-policy.md"
    content = "# Refund policy"
    write_policy(tmp_path, source, content)
    session_factory, write_session = session_factory_with_existing([])

    seed_policy_documents(
        documents_path=tmp_path,
        embedding_model_name="test-model",
        embedding_model=StubEmbeddingModel([[0.1, 0.2]]),
        session_factory=session_factory,
    )

    statement = write_session.execute.call_args.args[0]
    assert "INSERT INTO company_policies" in str(statement)
    assert policy_document_id(source) in statement.compile().params.values()


@pytest.mark.parametrize(
    ("existing_content", "existing_model"),
    [
        ("Old cancellation policy", "test-model"),
        ("# Cancellation policy", "old-model"),
    ],
)
def test_changed_content_or_model_is_embedded(
    tmp_path: Path,
    existing_content: str,
    existing_model: str,
) -> None:
    source = "cancellation-policy.md"
    content = "# Cancellation policy"
    write_policy(tmp_path, source, content)
    session_factory, write_session = session_factory_with_existing(
        [
            (policy_document_id(source), source, existing_content, existing_model),
            (uuid4(), "deleted-policy.md", "Deleted policy", "test-model"),
        ]
    )
    embedding_model = StubEmbeddingModel([[0.1, 0.2]])

    seed_policy_documents(
        documents_path=tmp_path,
        embedding_model_name="test-model",
        embedding_model=embedding_model,
        session_factory=session_factory,
    )

    assert embedding_model.document_inputs == [content]
    statements = [str(call.args[0]) for call in write_session.execute.call_args_list]
    assert any("UPDATE company_policies" in statement for statement in statements)
    assert any("DELETE FROM company_policies" in statement for statement in statements)


def test_embedding_count_mismatch_does_not_write(tmp_path: Path) -> None:
    write_policy(tmp_path, "refund-policy.md", "# Refund policy")
    session_factory, _ = session_factory_with_existing([])

    with pytest.raises(RuntimeError, match="unexpected number of embeddings"):
        seed_policy_documents(
            documents_path=tmp_path,
            embedding_model_name="test-model",
            embedding_model=StubEmbeddingModel([]),
            session_factory=session_factory,
        )

    session_factory.begin.assert_not_called()
