"""Shared RAG retriever initialization for chatbot and task services."""

from __future__ import annotations

import logging

from app.rag.data_loader import DataLoader
from app.rag.embedder import Embedder, VectorStoreConfig
from app.rag.retriever import Retriever

logger = logging.getLogger(__name__)

_retriever: Retriever | None = None
_embedder: Embedder | None = None


def reset_rag_retriever() -> None:
    """Clear cached retriever (mainly for tests or stale Chroma handles)."""
    global _retriever, _embedder
    _retriever = None
    _embedder = None


def _collection_is_healthy(retriever: Retriever) -> bool:
    try:
        retriever.collection.count()
        return True
    except Exception as exc:
        logger.warning("RAG collection health check failed: %s", exc)
        return False


def _build_retriever() -> Retriever:
    global _retriever, _embedder

    loader = DataLoader()
    docs = loader.load()
    if not docs:
        raise RuntimeError("No Islamic knowledge documents found in data/")

    _embedder = Embedder(VectorStoreConfig())
    rebuilt = _embedder.ensure_index(docs, data_signature=loader.source_signature())
    if rebuilt:
        logger.info("RAG index rebuilt with %s documents", len(docs))
    else:
        logger.info("RAG index is up to date with %s documents", len(docs))

    _retriever = Retriever(_embedder.as_retriever())
    return _retriever


def get_rag_retriever() -> Retriever:
    """Load data, sync the vector index, and return a healthy singleton retriever."""
    global _retriever

    if _retriever is not None and _collection_is_healthy(_retriever):
        return _retriever

    if _retriever is not None:
        logger.info("Refreshing stale RAG retriever")
        reset_rag_retriever()

    return _build_retriever()
