import asyncio
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PolicyMatch:
    source: str
    content: str
    score: float


class LocalPolicyRepository:
    """Read and rank the small local policy corpus.

    This adapter intentionally keeps retrieval behind a repository interface so a
    pgvector-backed implementation can replace it without changing tools/services.
    """

    _TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
    _STOP_WORDS = frozenset({
        "a",
        "an",
        "and",
        "are",
        "be",
        "for",
        "is",
        "of",
        "or",
        "the",
        "to",
        "with",
    })

    def __init__(self, documents_path: Path) -> None:
        self._documents_path = documents_path

    async def search(self, query: str, limit: int) -> list[PolicyMatch]:
        return await asyncio.to_thread(self._search_sync, query, limit)

    def _search_sync(self, query: str, limit: int) -> list[PolicyMatch]:
        query_tokens = set(self._TOKEN_PATTERN.findall(query.casefold()))
        query_tokens -= self._STOP_WORDS
        matches: list[PolicyMatch] = []

        for path in sorted(self._documents_path.glob("*.md")):
            content = path.read_text(encoding="utf-8").strip()
            title_tokens = set(
                self._TOKEN_PATTERN.findall(path.stem.casefold())
            )
            content_tokens = set(
                self._TOKEN_PATTERN.findall(content.casefold())
            )
            title_overlap = len(query_tokens & title_tokens)
            content_overlap = len(query_tokens & content_tokens)
            weighted_overlap = (2 * title_overlap) + content_overlap
            if weighted_overlap == 0:
                continue
            score = weighted_overlap / max(3 * len(query_tokens), 1)
            matches.append(
                PolicyMatch(source=path.name, content=content, score=score)
            )

        matches.sort(key=lambda match: (-match.score, match.source))
        return matches[:limit]
