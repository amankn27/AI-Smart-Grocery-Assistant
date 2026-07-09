"""Load the RAG corpus, embed it, and expose a retriever.

The index is built once (lru_cache) from the configured embedder + vector store, both of
which have zero-dependency fallbacks, so retrieval works out of the box and deterministically.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from app.config.providers import get_embedder
from app.config.settings import get_settings
from app.rag.store import Retrieved, build_store

logger = logging.getLogger(__name__)


def _resolve(configured: str) -> Path:
    """Resolve the corpus path from repo root or backend/ cwd (mirrors catalog resolution)."""
    p = Path(configured)
    for cand in (p, Path(__file__).resolve().parents[3] / configured):
        if cand.exists():
            return cand
    return p


def _load_corpus(path: str | Path) -> list[dict]:
    path = _resolve(str(path))
    if not path.exists():
        logger.warning("RAG corpus %s not found; retrieval will be empty", path)
        return []
    docs = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                docs.append(json.loads(line))
    return docs


@lru_cache
def get_retriever() -> "Retriever":
    s = get_settings()
    embedder = get_embedder()
    store = build_store(s.vector_store, s.chroma_path)
    docs = _load_corpus(s.rag_corpus_path)
    if docs and store.count() == 0:
        vectors = embedder.embed([d["text"] for d in docs])
        store.add(
            ids=[d["id"] for d in docs],
            texts=[d["text"] for d in docs],
            vectors=vectors,
            metadatas=[d.get("metadata", {}) for d in docs],
        )
    return Retriever(embedder, store)


class Retriever:
    def __init__(self, embedder, store) -> None:
        self._embedder = embedder
        self._store = store

    def retrieve(self, query: str, k: int = 3) -> list[Retrieved]:
        if self._store.count() == 0:
            return []
        vec = self._embedder.embed_one(query)
        return self._store.query(vec, k=k)
