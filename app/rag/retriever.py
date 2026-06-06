from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any
import json
import re


@dataclass
class RetrievedChunk:
    id: str
    text: str
    metadata: Dict[str, Any]
    distance: float | None


class Retriever:
    """Thin wrapper around a Chroma collection for kNN text retrieval."""

    _HADITH_HINTS = ("hadith", "hadeeth", "sunnah", "prophet said", "nabi")
    _QURAN_HINTS = ("quran", "quranic", "verse", "ayat", "aya", "surah")

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
    def _content_type(chunk: RetrievedChunk) -> str:
        meta = chunk.metadata or {}
        explicit = meta.get("content_type") or meta.get("type") or meta.get("source_type") or ""
        if explicit in {"hadith", "ayat", "scholar", "prophet_story", "video", "guidance"}:
            return explicit
        if meta.get("source_type") == "islamic_scholar":
            return "scholar"
        if meta.get("source_type") == "prophet_story":
            return "prophet_story"
        return "other"

    @staticmethod
    def _behavior_query_from_context(child_context: str) -> str:
        """Turn child profile stats into retrieval keywords."""
        keywords: List[str] = []
        lower = child_context.lower()
        if "behavior level" in lower:
            keywords.extend(["behavior", "self control", "discipline", "akhlaaq"])
        if "islamic knowledge" in lower:
            keywords.extend(["islamic knowledge", "learning", "tarbiyah"])
        if "active" in lower:
            keywords.extend(["active child", "energy", "patience"])
        if "emotional" in lower:
            keywords.extend(["emotional intelligence", "anger", "mercy"])
        for match in re.findall(r"([A-Za-z_ ]+):\s*\d", child_context):
            label = match.strip().replace("_", " ")
            if label and label.lower() not in {"behavior level", "islamic knowledge", "total responses"}:
                keywords.append(label.lower())
        if not keywords:
            return ""
        return "islamic parenting " + " ".join(keywords[:6])

    def retrieve_parenting_context(
        self,
        question: str,
        *,
        child_context: str = "",
        k: int = 10,
    ) -> List[RetrievedChunk]:
        """Retrieve a balanced mix of hadith, Quran, scholar notes, and stories."""
        lower_q = question.lower()
        queries = [question]
        if any(h in lower_q for h in self._HADITH_HINTS):
            queries.append(f"hadith sunnah prophet parenting {question}")
        else:
            queries.append(f"hadith sunnah islamic parenting {question}")
        if any(h in lower_q for h in self._QURAN_HINTS):
            queries.append(f"quran ayat verse parenting {question}")
        else:
            queries.append(f"quran ayat verse islamic parenting guidance")

        behavior_query = self._behavior_query_from_context(child_context)
        if behavior_query:
            queries.append(behavior_query)

        per_query = max(4, k)
        seen: set[str] = set()
        buckets: Dict[str, List[RetrievedChunk]] = {
            "hadith": [],
            "ayat": [],
            "scholar": [],
            "prophet_story": [],
            "other": [],
        }

        for query in queries:
            for chunk in self.query(query, k=per_query):
                if chunk.id in seen:
                    continue
                if self._content_type(chunk) == "video":
                    continue
                seen.add(chunk.id)
                bucket = self._content_type(chunk)
                if bucket not in buckets:
                    bucket = "other"
                buckets[bucket].append(chunk)

        ordered: List[RetrievedChunk] = []
        for bucket_name, limit in (
            ("hadith", 3),
            ("ayat", 2),
            ("scholar", 2),
            ("prophet_story", 2),
            ("other", 2),
        ):
            ordered.extend(buckets[bucket_name][:limit])

        leftovers: List[RetrievedChunk] = []
        for bucket_name in ("hadith", "ayat", "scholar", "prophet_story", "other"):
            leftovers.extend(buckets[bucket_name][3 if bucket_name == "hadith" else 2 :])

        for chunk in leftovers:
            if chunk.id not in {c.id for c in ordered}:
                ordered.append(chunk)
            if len(ordered) >= k:
                break

        return ordered[:k]

    @staticmethod
    def format_context(chunks: List[RetrievedChunk]) -> str:
        """Format retrieved chunks with proper Islamic source citations."""
        parts: List[str] = []
        for i, ch in enumerate(chunks, start=1):
            citation_parts: List[str] = []
            meta = ch.metadata or {}
            content_type = Retriever._content_type(ch)

            if content_type == "scholar":
                book = meta.get("book_title", "")
                author = meta.get("author", "")
                topic = meta.get("topic", "")
                citation_parts.append("Islamic Scholar")
                if book and author:
                    citation_parts.append(f"{book} – {author}")
                elif meta.get("source_details"):
                    citation_parts.append(str(meta["source_details"]))
                elif book:
                    citation_parts.append(str(book))
                if topic:
                    citation_parts.append(f"Topic: {topic}")
                header = f"[Source {i}: {' | '.join(citation_parts)}]"
                parts.append(f"{header}\n{ch.text}")
                continue

            if content_type == "hadith":
                citation_parts.append("Hadith")
            elif content_type == "ayat":
                citation_parts.append("Quran")
            elif content_type == "prophet_story":
                citation_parts.append("Prophet Story")
            else:
                citation_parts.append(meta.get("category") or content_type.replace("_", " ").title())

            source_details = meta.get("source_details") or meta.get("source", "")
            if source_details and not str(source_details).startswith("{"):
                citation_parts.append(str(source_details))
            elif source_details:
                try:
                    source_dict = json.loads(source_details) if isinstance(source_details, str) else source_details
                    if isinstance(source_dict, dict):
                        if source_dict.get("book") == "Qur'an":
                            citation_parts.append(
                                f"Qur'an {source_dict.get('surah')}:{source_dict.get('ayah')}"
                            )
                        elif "collection" in source_dict:
                            ref = source_dict["collection"]
                            number = source_dict.get("hadith_number") or source_dict.get("number")
                            if number:
                                ref = f"{ref}, Hadith {number}"
                            citation_parts.append(ref)
                except (json.JSONDecodeError, TypeError):
                    pass

            if meta.get("quran_reference"):
                citation_parts.append(f"Qur'an {meta['quran_reference']}")

            classification = meta.get("hadith_classification", "")
            if classification and str(classification).strip():
                citation_parts.append(f"[{classification}]")

            if content_type == "prophet_story" and meta.get("title"):
                citation_parts.append(str(meta["title"]))

            header = f"[Source {i}: {' | '.join(citation_parts)}]"
            parts.append(f"{header}\n{ch.text}")

        return "\n\n".join(parts)
