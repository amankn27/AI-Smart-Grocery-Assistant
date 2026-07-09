"""Vector store behind one interface: pure-python in-memory (default) or Chroma (optional).

Per the brief we ship exactly one real store — **Chroma** — as the optional persistent
backend, plus a dependency-free :class:`InMemoryStore` (cosine over normalized vectors) so
retrieval works and is deterministic in tests without installing anything.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Retrieved:
    id: str
    text: str
    score: float
    metadata: dict


class VectorStore(ABC):
    name: str = "base"

    @abstractmethod
    def add(self, ids: list[str], texts: list[str], vectors: list[list[float]], metadatas: list[dict]) -> None: ...

    @abstractmethod
    def query(self, vector: list[float], k: int = 3) -> list[Retrieved]: ...

    @abstractmethod
    def count(self) -> int: ...


class InMemoryStore(VectorStore):
    name = "memory"

    def __init__(self) -> None:
        self._ids: list[str] = []
        self._texts: list[str] = []
        self._vectors: list[list[float]] = []
        self._metas: list[dict] = []

    def add(self, ids, texts, vectors, metadatas) -> None:
        self._ids += ids
        self._texts += texts
        self._vectors += vectors
        self._metas += metadatas

    @staticmethod
    def _dot(a: list[float], b: list[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    def query(self, vector, k=3) -> list[Retrieved]:
        # Vectors are L2-normalized by the embedder, so dot product == cosine similarity.
        scored = [
            Retrieved(id=i, text=t, score=self._dot(vector, v), metadata=m)
            for i, t, v, m in zip(self._ids, self._texts, self._vectors, self._metas)
        ]
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:k]

    def count(self) -> int:
        return len(self._ids)


class ChromaStore(VectorStore):
    name = "chroma"

    def __init__(self, path: str, collection: str = "grocery_rag") -> None:
        import chromadb  # lazy

        self._client = chromadb.PersistentClient(path=path)
        self._col = self._client.get_or_create_collection(collection)

    def add(self, ids, texts, vectors, metadatas) -> None:
        self._col.upsert(ids=ids, documents=texts, embeddings=vectors, metadatas=metadatas)

    def query(self, vector, k=3) -> list[Retrieved]:
        res = self._col.query(query_embeddings=[vector], n_results=k)
        out: list[Retrieved] = []
        for id_, doc, meta, dist in zip(
            res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]
        ):
            out.append(Retrieved(id=id_, text=doc, score=1.0 - float(dist), metadata=meta or {}))
        return out

    def count(self) -> int:
        return self._col.count()


def build_store(kind: str, chroma_path: str) -> VectorStore:
    if kind == "chroma":
        try:
            return ChromaStore(chroma_path)
        except Exception as exc:  # noqa: BLE001
            logger.info("Chroma unavailable (%s); using in-memory vector store", exc)
    return InMemoryStore()
