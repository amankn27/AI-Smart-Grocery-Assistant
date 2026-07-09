"""Tests for the RAG edge using the deterministic hashing embedder + in-memory store.

No model download or network — the hashing embedder makes retrieval reproducible.
"""

from app.providers.embeddings.embedders import HashingEmbedder
from app.rag.index import Retriever
from app.rag.store import InMemoryStore


def _retriever_with_docs(docs):
    emb = HashingEmbedder(dim=256)
    store = InMemoryStore()
    store.add(
        ids=[d["id"] for d in docs],
        texts=[d["text"] for d in docs],
        vectors=emb.embed([d["text"] for d in docs]),
        metadatas=[d.get("metadata", {}) for d in docs],
    )
    return Retriever(emb, store)


DOCS = [
    {"id": "sugar", "text": "reduce free sugars sugary soft drinks biscuits chocolate", "metadata": {"topic": "sugar"}},
    {"id": "sodium", "text": "lower sodium salt chips namkeen instant noodles blood pressure", "metadata": {"topic": "sodium"}},
    {"id": "fibre", "text": "dietary fibre whole grains oats millet pulses vegetables", "metadata": {"topic": "fibre"}},
]


def test_embedder_is_deterministic_and_normalized():
    emb = HashingEmbedder(dim=64)
    v1 = emb.embed_one("hello world")
    v2 = emb.embed_one("hello world")
    assert v1 == v2
    assert abs(sum(x * x for x in v1) - 1.0) < 1e-9  # L2 normalized


def test_retrieval_ranks_relevant_doc_first():
    r = _retriever_with_docs(DOCS)
    hits = r.retrieve("too much salt and sodium in namkeen", k=3)
    assert hits[0].id == "sodium"
    assert hits[0].score >= hits[-1].score  # sorted descending


def test_empty_store_returns_nothing():
    r = Retriever(HashingEmbedder(), InMemoryStore())
    assert r.retrieve("anything") == []
