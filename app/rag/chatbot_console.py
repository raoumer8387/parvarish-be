from __future__ import annotations

import os
from typing import List

from .data_loader import DataLoader
from .embedder import Embedder, VectorStoreConfig
from .retriever import Retriever
from app.services.llm_client import generate_response


SYSTEM_PROMPT = (
    "You are Parvarish AI — an Islamic parenting assistant. Use the provided Quranic verses, Hadith, and Prophet stories to guide the parent. "
    "If no relevant reference is found, reply respectfully that the topic is outside your current knowledge."
)


def bootstrap_index(reset: bool = False) -> Retriever:
    # Prepare documents and vector store
    loader = DataLoader()
    docs = loader.load()
    store = Embedder(VectorStoreConfig())
    # Only (re)build if reset requested or collection is empty
    needs_build = reset
    if not needs_build:
        # Probe collection size cheaply
        try:
            stats = store.collection.count()
            if not stats or stats == 0:
                needs_build = True
        except Exception:
            needs_build = True
    if needs_build:
        store.build_index(docs, reset=True)
    return Retriever(store.as_retriever())


def chat_loop():
    print("Parvarish AI (RAG) — console mode. Type 'exit' to quit.")
    retriever = bootstrap_index(reset=os.getenv("PARVARISH_REBUILD", "0") == "1")

    while True:
        try:
            user_q = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break
        if not user_q:
            continue
        if user_q.lower() in {"exit", "quit", ":q"}:
            print("Goodbye.")
            break

        # Retrieve context
        chunks = retriever.query(user_q, k=3)
        
        if chunks:
            # Format context more cleanly
            context_parts = []
            for i, ch in enumerate(chunks, start=1):
                # Get category/type from metadata
                source_type = ch.metadata.get('category') or ch.metadata.get('type') or 'Islamic Reference'
                # Clean and limit each chunk text
                chunk_text = ch.text.strip()[:500]  # Limit each chunk to 500 chars
                context_parts.append(f"Reference {i} ({source_type}):\n{chunk_text}")
            context = "\n\n".join(context_parts)
        else:
            context = "No specific references found in the database."

        # Build a simpler, cleaner prompt for POE
        full_prompt = f"""You are Parvarish AI, an Islamic parenting assistant.

Islamic References:
{context}

Parent's Question: {user_q}

Please provide guidance based on the Islamic references above. If the references don't cover this topic, politely explain that."""

        messages: List[dict] = [
            {"role": "user", "content": full_prompt},
        ]

        try:
            answer = generate_response(messages)
        except Exception as e:
            print(f"Error from LLM: {e}")
            continue

        print(f"\nParvarish AI: {answer}")


if __name__ == "__main__":
    chat_loop()
