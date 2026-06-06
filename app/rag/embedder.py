from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any
import hashlib
import json
import logging

import os

# External deps expected in requirements: sentence-transformers, chromadb
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions

from .data_loader import Document

logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_DB_DIR = Path(os.getenv("PARVARISH_CHROMA_DIR", Path.home() / ".parvarish_chroma"))
DEFAULT_COLLECTION = "parvarish_islamic_parenting"
INDEX_MANIFEST = "index_manifest.json"
RAG_INDEX_VERSION = 2


@dataclass
class VectorStoreConfig:
    persist_directory: Path = DEFAULT_DB_DIR
    collection_name: str = DEFAULT_COLLECTION
    model_name: str = DEFAULT_MODEL_NAME


class Embedder:
    """Handles embedding generation and Chroma collection persistence."""

    def __init__(self, config: VectorStoreConfig | None = None) -> None:
        self.config = config or VectorStoreConfig()
        self.config.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize model with device handling for PyTorch compatibility
        try:
            import torch
            # Force CPU device to avoid meta tensor issues
            device = 'cpu'
            self.model = SentenceTransformer(self.config.model_name, device=device)
            logger.info(f"Loaded SentenceTransformer model: {self.config.model_name} on {device}")
        except Exception as e:
            logger.warning(f"Error loading SentenceTransformer with device: {e}, trying default initialization")
            try:
                self.model = SentenceTransformer(self.config.model_name)
            except Exception as e2:
                logger.error(f"Failed to load SentenceTransformer: {e2}")
                raise RuntimeError(f"Could not initialize embeddings model: {e2}")
        
        self.client = chromadb.PersistentClient(path=str(self.config.persist_directory))
        
        # Use ChromaDB's embedding function with device specification
        try:
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.config.model_name,
                device='cpu'  # Force CPU to avoid GPU tensor issues
            )
        except TypeError:
            # Fallback if device parameter not supported in older versions
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.config.model_name
            )
        
        # attempt to get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.config.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def build_index(self, docs: List[Document], reset: bool = False) -> None:
        if reset:
            try:
                self.client.delete_collection(self.config.collection_name)
            except Exception:
                pass
            self.collection = self.client.get_or_create_collection(
                name=self.config.collection_name,
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
        if not docs:
            return
        ids = [d.id for d in docs]
        texts = [d.text for d in docs]
        metadatas: List[Dict[str, Any]] = [self._sanitize_metadata(d.metadata) for d in docs]
        batch_size = 128
        for i in range(0, len(docs), batch_size):
            self.collection.upsert(
                ids=ids[i : i + batch_size],
                documents=texts[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )

    @staticmethod
    def _sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Chroma metadata values must be str, int, float, or bool."""
        clean: Dict[str, Any] = {}
        for key, value in metadata.items():
            if value is None:
                continue
            if isinstance(value, (str, int, float, bool)):
                clean[key] = value
            elif isinstance(value, list):
                clean[key] = ", ".join(str(v) for v in value)
            else:
                clean[key] = str(value)
        return clean

    @staticmethod
    def doc_signature(docs: List[Document]) -> str:
        payload = "|".join(sorted(d.id for d in docs))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def ensure_index(self, docs: List[Document], *, data_signature: str | None = None) -> bool:
        """Rebuild the vector index when data files change or the collection is incomplete."""
        manifest_path = self.config.persist_directory / INDEX_MANIFEST
        signature = self.doc_signature(docs)
        expected_count = len(docs)
        current_count = self.collection.count()
        stored_signature = None
        stored_data_signature = None
        stored_version = None
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                stored_signature = manifest.get("signature")
                stored_data_signature = manifest.get("data_signature")
                stored_version = manifest.get("version")
            except (OSError, json.JSONDecodeError):
                stored_signature = None
                stored_data_signature = None
                stored_version = None

        needs_rebuild = (
            expected_count == 0
            or current_count != expected_count
            or stored_signature != signature
            or stored_version != RAG_INDEX_VERSION
            or (data_signature is not None and stored_data_signature != data_signature)
        )
        if not needs_rebuild:
            try:
                self.collection.count()
            except Exception:
                logger.warning("Chroma collection handle is stale; forcing rebuild")
                needs_rebuild = True

        if not needs_rebuild:
            return False

        logger.info(
            "Rebuilding RAG index (%s docs in store, %s expected)",
            current_count,
            expected_count,
        )
        self.build_index(docs, reset=True)
        manifest_path.write_text(
            json.dumps(
                {
                    "signature": signature,
                    "data_signature": data_signature,
                    "count": expected_count,
                    "version": RAG_INDEX_VERSION,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return True

    def refresh_collection(self) -> chromadb.api.models.Collection.Collection:
        """Re-bind to the persisted collection (fixes stale UUID handles after rebuild)."""
        self.collection = self.client.get_or_create_collection(
            name=self.config.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
        return self.collection

    def as_retriever(self) -> chromadb.api.models.Collection.Collection:
        return self.collection
