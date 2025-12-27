from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any
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
        metadatas: List[Dict[str, Any]] = [d.metadata for d in docs]
        # Upsert in manageable batches
        batch_size = 128
        for i in range(0, len(docs), batch_size):
            self.collection.upsert(
                ids=ids[i : i + batch_size],
                documents=texts[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )

    def ensure_built(self) -> None:
        # NOP placeholder; Chroma persists automatically on upsert
        pass

    def as_retriever(self) -> chromadb.api.models.Collection.Collection:
        return self.collection
