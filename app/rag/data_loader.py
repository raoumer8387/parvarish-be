from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib


@dataclass
class Document:
    id: str
    text: str
    metadata: Dict[str, Any]


class DataLoader:
    """Loads and normalizes Islamic parenting content from JSON datasets.

    Expected JSON formats:
    - hadith_quranic.json: top-level keys with categories and entries (as provided)
    - prophet_stories.json: assumed to contain a list of story objects with fields like id, title, text, and optional source/metadata
    """

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        # Locate data directory robustly without restructuring the project.
        # Prefer app/data if present, otherwise fall back to root-level data/.
        if base_dir is not None:
            base = Path(base_dir)
        else:
            app_dir = Path(__file__).resolve().parents[1]
            root_dir = app_dir.parent
            app_data = app_dir / "data"
            root_data = root_dir / "data"
            base = app_data if app_data.exists() else root_data
        self.base_dir = base
        self.hadith_file = self.base_dir / "hadith_quranic.json"
        self.new_hadith_file = self.base_dir / "new_hadith.json"
        self.new_quranic_file = self.base_dir / "new_quranic_verse.json"
        self.stories_file = self.base_dir / "prophet_stories.json"
        self.scholars_file = self.base_dir / "islamic_refrences.json"
        self.playlist_file = self.base_dir / "parvarish_playlist_tagged.json"

    def load(self) -> List[Document]:
        docs: List[Document] = []
        if self.hadith_file.exists():
            with self.hadith_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            docs.extend(self._normalize_hadith_quranic(data))
        if self.new_hadith_file.exists():
            with self.new_hadith_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            docs.extend(self._normalize_new_hadith(data))
        if self.new_quranic_file.exists():
            with self.new_quranic_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            docs.extend(self._normalize_new_quranic(data))
        if self.stories_file.exists():
            with self.stories_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            docs.extend(self._normalize_prophet_stories(data))
        if self.scholars_file.exists():
            with self.scholars_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            docs.extend(self._load_islamic_scholars(data))
        if self.playlist_file.exists():
            with self.playlist_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            docs.extend(self._normalize_playlist(data))

        return self._dedupe_documents(docs)

    def source_signature(self) -> str:
        """Fingerprint data files so the vector index rebuilds when JSON changes."""
        parts: List[str] = []
        for path in (
            self.hadith_file,
            self.new_hadith_file,
            self.new_quranic_file,
            self.stories_file,
            self.scholars_file,
            self.playlist_file,
        ):
            if path.exists():
                stat = path.stat()
                parts.append(f"{path.name}:{stat.st_mtime_ns}:{stat.st_size}")
        return hashlib.sha256("|".join(sorted(parts)).encode("utf-8")).hexdigest()

    @staticmethod
    def _dedupe_documents(docs: List[Document]) -> List[Document]:
        """Ensure every document id is unique before indexing."""
        seen: Dict[str, int] = {}
        unique: List[Document] = []
        for doc in docs:
            doc_id = doc.id
            if doc_id in seen:
                seen[doc_id] += 1
                doc_id = f"{doc_id}__{seen[doc_id]}"
            else:
                seen[doc_id] = 1
            unique.append(Document(id=doc_id, text=doc.text, metadata=doc.metadata))
        return unique

    def _format_source(self, source: Optional[Dict[str, Any]]) -> str:
        if not source:
            return ""
        
        parts = []
        if "book" in source and source["book"] == "Qur'an":
            parts.append(f"Qur'an {source.get('surah')}:{source.get('ayah')}")
        elif "collection" in source:
            collection = source.get("collection") or "Hadith"
            number = source.get("hadith_number") or source.get("number")
            if number:
                parts.append(f"{collection}, Hadith {number}")
            else:
                parts.append(collection)
        elif "note" in source:
            parts.append(source.get("note"))
            
        return ", ".join(parts)

    def _normalize_playlist(self, data: List[Dict[str, Any]]) -> List[Document]:
        """Normalizes playlist data into Document objects."""
        docs: List[Document] = []
        for item in data:
            video_id = item.get("Video Number")
            title = item.get("Title")
            url = item.get("URL")
            tags = item.get("tags", [])

            if not all([video_id, title, url]):
                continue

            text = f"Video for kids: '{title}'. It teaches about {', '.join(tags)}."
            
            metadata = {
                "source": "Parvarish Playlist",
                "type": "video",
                "content_type": "video",
                "title": title,
                "url": url,
                "tags": tags,
            }
            
            docs.append(Document(id=f"vid_{video_id}", text=text, metadata=metadata))
        return docs

    def _normalize_hadith_quranic(self, data: Dict[str, Any]) -> List[Document]:
        docs: List[Document] = []
        categories = data.get("categories", [])
        for cat in categories:
            cat_name = cat.get("category")
            for entry in cat.get("entries", []):
                entry_id = entry.get("id") or f"{cat_name}-unknown"
                parts: List[str] = []
                # Combine bilingual content succinctly
                source_info = self._format_source(entry.get("source"))
                if source_info:
                    parts.append(f"Source: {source_info}")
                if entry.get("type") in {"ayat", "hadith"}:
                    arabic = entry.get("arabic")
                    if arabic:
                        parts.append(f"AR: {arabic}")
                en = (
                    entry.get("english_translation")
                    or entry.get("english_text")
                    or entry.get("short_explanation", {}).get("en")
                )
                ur = (
                    entry.get("urdu_translation")
                    or entry.get("urdu_text")
                    or entry.get("short_explanation", {}).get("ur")
                )
                if en:
                    parts.append(f"EN: {en}")
                if ur:
                    parts.append(f"UR: {ur}")
                tafsir = entry.get("tafsir_excerpt")
                if tafsir:
                    parts.append(f"Tafsir: {tafsir}")
                practical = entry.get("practical_tip", {})
                if isinstance(practical, dict):
                    pen = practical.get("en")
                    pur = practical.get("ur")
                    tips = []
                    if pen:
                        tips.append(f"Tip(EN): {pen}")
                    if pur:
                        tips.append(f"Tip(UR): {pur}")
                    if tips:
                        parts.append(" ".join(tips))
                elif isinstance(practical, str):
                    parts.append(f"Tip: {practical}")
                
                text = " | ".join(parts)
                
                entry_type = entry.get("type") or "unknown"
                source_details = self._format_source(entry.get("source"))
                metadata = {
                    "id": entry_id,
                    "category": cat_name,
                    "type": entry_type,
                    "content_type": entry_type if entry_type in {"hadith", "ayat"} else "guidance",
                    "source_details": source_details,
                    "tags": entry.get("tags", []),
                    "age_range": entry.get("age_range"),
                    "hadith_classification": entry.get("hadith_classification") or "",
                }
                docs.append(Document(id=f"hq:{cat_name}:{entry_id}", text=text, metadata=metadata))
        return docs

    def _normalize_new_hadith(self, data: List[Dict[str, Any]]) -> List[Document]:
        docs: List[Document] = []
        if not isinstance(data, list):
            return docs
        for entry in data:
            entry_id = entry.get("id") or f"nh-{len(docs) + 1}"
            source = entry.get("source") or "Hadith"
            reference = entry.get("reference") or ""
            source_details = f"{source}, Hadith {reference}" if reference else source
            parts: List[str] = []
            if entry.get("embedding_text"):
                parts.append(entry["embedding_text"])
            topic = entry.get("topic")
            subtopic = entry.get("subtopic")
            if topic:
                parts.append(f"Topic: {topic}" + (f" / {subtopic}" if subtopic else ""))
            parts.append(f"Source: {source_details}")
            if entry.get("text_en"):
                parts.append(f"EN: {entry['text_en']}")
            if entry.get("text_urdu"):
                parts.append(f"UR: {entry['text_urdu']}")
            if entry.get("text_roman_urdu"):
                parts.append(f"RM: {entry['text_roman_urdu']}")
            if entry.get("parenting_insight"):
                parts.append(f"Parenting insight: {entry['parenting_insight']}")
            docs.append(
                Document(
                    id=f"new_hadith:{entry_id}",
                    text=" | ".join(parts),
                    metadata={
                        "id": entry_id,
                        "type": "hadith",
                        "content_type": "hadith",
                        "category": topic or "Parenting Hadith",
                        "source_details": source_details,
                        "collection": source,
                        "hadith_number": str(reference),
                        "hadith_classification": entry.get("authenticity") or "",
                        "tags": entry.get("tags", []),
                        "topic": topic or "",
                    },
                )
            )
        return docs

    def _normalize_new_quranic(self, data: List[Dict[str, Any]]) -> List[Document]:
        docs: List[Document] = []
        if not isinstance(data, list):
            return docs
        for entry in data:
            entry_id = entry.get("id") or f"nq-{len(docs) + 1}"
            reference = entry.get("reference") or ""
            source_details = f"Qur'an {reference}" if reference else "Qur'an"
            parts: List[str] = []
            if entry.get("embedding_text"):
                parts.append(entry["embedding_text"])
            topic = entry.get("topic")
            subtopic = entry.get("subtopic")
            if topic:
                parts.append(f"Topic: {topic}" + (f" / {subtopic}" if subtopic else ""))
            parts.append(f"Source: {source_details}")
            if entry.get("text_en"):
                parts.append(f"EN: {entry['text_en']}")
            if entry.get("text_urdu"):
                parts.append(f"UR: {entry['text_urdu']}")
            if entry.get("text_roman_urdu"):
                parts.append(f"RM: {entry['text_roman_urdu']}")
            if entry.get("parenting_insight"):
                parts.append(f"Parenting insight: {entry['parenting_insight']}")
            docs.append(
                Document(
                    id=f"new_quran:{entry_id}",
                    text=" | ".join(parts),
                    metadata={
                        "id": entry_id,
                        "type": "ayat",
                        "content_type": "ayat",
                        "category": topic or "Parenting Quran",
                        "source_details": source_details,
                        "quran_reference": reference,
                        "tags": entry.get("tags", []),
                        "topic": topic or "",
                    },
                )
            )
        return docs

    def _normalize_prophet_stories(self, data: Any) -> List[Document]:
        docs: List[Document] = []
        # Accept either { stories: [...] } or a top-level list
        stories = data.get("stories") if isinstance(data, dict) else data
        if not isinstance(stories, list):
            return docs
        import json as _json
        def fix_meta(val):
            if val is None:
                return ""
            if isinstance(val, list):
                return ", ".join(str(v) for v in val)
            if isinstance(val, dict):
                return _json.dumps(val, ensure_ascii=False)
            return val
        for idx, story in enumerate(stories):
            sid = story.get("id") or f"S{idx+1}"
            title = story.get("title") or story.get("name") or ""
            english = story.get("english_text") or story.get("text") or story.get("story") or ""
            urdu = story.get("urdu_text") or ""
            lesson_en = story.get("lesson_english") or ""
            lesson_ur = story.get("lesson_urdu") or ""
            key_points = story.get("key_points") or []
            parts: List[str] = []
            if title:
                parts.append(f"TITLE: {title}")
            if english:
                parts.append(f"EN: {english}")
            if urdu:
                parts.append(f"UR: {urdu}")
            if lesson_en:
                parts.append(f"Lesson(EN): {lesson_en}")
            if lesson_ur:
                parts.append(f"Lesson(UR): {lesson_ur}")
            if key_points:
                parts.append("Key Points: " + "; ".join(key_points))
            full_text = "\n".join(parts)
            metadata = {
                "source_type": "prophet_story",
                "content_type": "prophet_story",
                "source_details": f"Prophet Story: {title}" if title else "Prophet Story",
                "title": title,
                "source": fix_meta(story.get("source")),
                "tags": fix_meta(story.get("tags")),
                "category": "Prophet Stories",
            }
            docs.append(Document(id=f"story:{sid}", text=full_text, metadata=metadata))
        return docs

    def _load_islamic_scholars(self, data: Any) -> List[Document]:
        """Load Islamic scholarly references on Tarbiyah and Parenting.
        
        Combines English + Urdu + Roman Urdu texts for multilingual support.
        Each reference becomes a Document with rich metadata for citations.
        """
        docs: List[Document] = []
        if not isinstance(data, list):
            return docs
        
        import json as _json
        def fix_meta(val):
            if val is None:
                return ""
            if isinstance(val, list):
                return ", ".join(str(v) for v in val)
            if isinstance(val, dict):
                return _json.dumps(val, ensure_ascii=False)
            return val
        
        for ref in data:
            ref_id = ref.get("id") or f"scholar-{len(docs)+1}"
            
            # Combine multilingual texts into one field for embeddings
            parts: List[str] = []
            
            text_en = ref.get("text_en", "")
            text_ur = ref.get("text_ur", "")
            text_roman = ref.get("text_roman", "")
            
            if text_en:
                parts.append(f"EN: {text_en}")
            if text_ur:
                parts.append(f"UR: {text_ur}")
            if text_roman:
                parts.append(f"RM: {text_roman}")
            
            # Combine all text
            combined_text = "\n".join(parts)
            
            # Build metadata with all relevant fields
            book = fix_meta(ref.get("book_title"))
            author = fix_meta(ref.get("author"))
            topic = fix_meta(ref.get("topic"))
            source_details = f"{book} – {author}" if book and author else (book or author or "Islamic Scholar")
            metadata = {
                "source_type": "islamic_scholar",
                "content_type": "scholar",
                "source_details": source_details,
                "book_title": book,
                "author": author,
                "topic": topic,
                "tags": fix_meta(ref.get("tags")),
                "age_range": fix_meta(ref.get("age_range")),
                "language_support": "en, ur, rm",
                "category": "Islamic Scholar Reference",
            }
            
            docs.append(Document(id=f"scholar:{ref_id}", text=combined_text, metadata=metadata))
        
        return docs
