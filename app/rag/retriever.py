from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any
import json


@dataclass
class RetrievedChunk:
    id: str
    text: str
    metadata: Dict[str, Any]
    distance: float | None


class Retriever:
    """Thin wrapper around a Chroma collection for kNN text retrieval."""

    def __init__(self, collection) -> None:
        self.collection = collection

    def query(self, question: str, k: int = 3) -> List[RetrievedChunk]:
        res = self.collection.query(query_texts=[question], n_results=k)
        ids = res.get("ids", [[]])[0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = (res.get("distances") or [[None] * len(ids)])[0]
        out: List[RetrievedChunk] = []
        for i in range(len(ids)):
            out.append(
                RetrievedChunk(
                    id=ids[i], text=docs[i], metadata=metas[i] if i < len(metas) else {}, distance=dists[i]
                )
            )
        return out

    @staticmethod
    def format_context(chunks: List[RetrievedChunk]) -> str:
        """Format retrieved chunks with proper Islamic source citations."""
        parts: List[str] = []
        for i, ch in enumerate(chunks, start=1):
            # Build detailed citation header
            citation_parts = []
            
            # Check if this is a scholar reference
            source_type = ch.metadata.get('source_type', '')
            if source_type == 'islamic_scholar':
                # Format: [Islamic Scholar | Book Title – Author | Topic]
                book = ch.metadata.get('book_title', '')
                author = ch.metadata.get('author', '')
                topic = ch.metadata.get('topic', '')
                
                citation_parts.append("Islamic Scholar")
                if book and author:
                    citation_parts.append(f"{book} – {author}")
                elif book:
                    citation_parts.append(book)
                if topic:
                    citation_parts.append(f"Topic: {topic}")
                
                header = f"[Source {i}: {' | '.join(citation_parts)}]"
                parts.append(f"{header}\n{ch.text}")
                continue
            
            # Original logic for Quran/Hadith/Stories
            category = ch.metadata.get('category', ch.metadata.get('type', 'unknown'))
            citation_parts.append(category)
            
            # Parse source information from metadata
            source_str = ch.metadata.get('source', '')
            if source_str:
                try:
                    # Try to parse as JSON if it looks like a JSON string
                    source_dict = json.loads(source_str) if isinstance(source_str, str) and source_str.startswith('{') else {}
                    
                    # Quranic verse citation
                    if 'surah' in source_dict and 'ayah' in source_dict:
                        surah = source_dict['surah']
                        ayah = source_dict['ayah']
                        citation_parts.append(f"Quran {surah}:{ayah}")
                        if 'book' in source_dict:
                            citation_parts.append(f"({source_dict['book']})")
                    
                    # Hadith citation
                    elif 'collection' in source_dict:
                        hadith_ref = source_dict['collection']
                        if 'hadith_number' in source_dict:
                            hadith_ref += f", {source_dict['hadith_number']}"
                        elif 'number' in source_dict: # fallback
                            hadith_ref += f", {source_dict['number']}"
                        citation_parts.append(hadith_ref)
                    
                    # Story or other source
                    elif 'book' in source_dict:
                        citation_parts.append(source_dict['book'])
                        
                except (json.JSONDecodeError, TypeError):
                    # If source is a simple string
                    if source_str and not source_str.startswith('{'):
                        citation_parts.append(source_str)
            
            # Hadith classification (Sahih, Hasan, Da'if, etc.)
            classification = ch.metadata.get('hadith_classification', '')
            if classification and classification.strip():
                citation_parts.append(f"[{classification}]")
            
            # Build the header
            header = f"[Source {i}: {' | '.join(citation_parts)}]"
            parts.append(f"{header}\n{ch.text}")
            
        return "\n\n".join(parts)
