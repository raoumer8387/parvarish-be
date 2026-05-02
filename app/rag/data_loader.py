from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional


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
        self.stories_file = self.base_dir / "prophet_stories.json"
        self.scholars_file = self.base_dir / "islamic_refrences.json"
        self.playlist_file = self.base_dir / "parvarish_playlist_tagged.json"

    def load(self) -> List[Document]:
        docs: List[Document] = []
        # hadith_quranic
        if self.hadith_file.exists():
            with self.hadith_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            docs.extend(self._normalize_hadith_quranic(data))
        # prophet_stories
        if self.stories_file.exists():
            with self.stories_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            docs.extend(self._normalize_prophet_stories(data))
        # islamic_scholars (NEW)
        if self.scholars_file.exists():
            with self.scholars_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            docs.extend(self._load_islamic_scholars(data))
        
        # Load playlist data
        if self.playlist_file.exists():
            with self.playlist_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            docs.extend(self._normalize_playlist(data))
            
        return docs

    def _format_source(self, source: Optional[Dict[str, Any]]) -> str:
        if not source:
            return ""
        
        parts = []
        if "book" in source and source["book"] == "Qur'an":
            parts.append(f"Qur'an {source.get('surah')}:{source.get('ayah')}")
        elif "collection" in source:
            parts.append(f"{source.get('collection')}, Hadith {source.get('hadith_number')}")
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
                
                metadata = {
                    "id": entry_id,
                    "category": cat_name,
                    "type": entry.get("type"),
                    "source_details": self._format_source(entry.get("source")),
                    "tags": entry.get("tags", []),
                    "age_range": entry.get("age_range"),
                }
                docs.append(Document(id=entry_id, text=text, metadata=metadata))
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
            title = story.get("title") or story.get("name")
            text = story.get("text") or story.get("story") or ""
            key_points = story.get("key_points") or []
            parts: List[str] = []
            if title:
                parts.append(f"TITLE: {title}")
            if text:
                parts.append(text)
            if key_points:
                parts.append("Key Points: " + "; ".join(key_points))
            full_text = "\n".join(parts)
            metadata = {
                "source_type": "prophet_story",  # Add this field for retriever
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
            metadata = {
                "source_type": "islamic_scholar",
                "book_title": fix_meta(ref.get("book_title")),
                "author": fix_meta(ref.get("author")),
                "topic": fix_meta(ref.get("topic")),
                "tags": fix_meta(ref.get("tags")),
                "age_range": fix_meta(ref.get("age_range")),
                "language_support": "en, ur, rm",
                "category": "Islamic Scholar Reference"
            }
            
            docs.append(Document(id=f"scholar:{ref_id}", text=combined_text, metadata=metadata))
        
        return docs
