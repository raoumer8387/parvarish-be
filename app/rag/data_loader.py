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

                text = "\n".join(parts)
                # Ensure all metadata values are str/int/float/bool
                import json as _json
                def fix_meta(val):
                    if val is None:
                        return ""
                    if isinstance(val, list):
                        return ", ".join(str(v) for v in val)
                    if isinstance(val, dict):
                        return _json.dumps(val, ensure_ascii=False)
                    return val
                metadata = {
                    "category": fix_meta(cat_name),
                    "type": fix_meta(entry.get("type")),
                    "tags": fix_meta(entry.get("tags")),
                    "age_range": fix_meta(entry.get("age_range")),
                    "source": fix_meta(entry.get("source")),
                    "hadith_classification": fix_meta(entry.get("hadith_classification")),
                }
                docs.append(Document(id=f"hadith:{entry_id}", text=text, metadata=metadata))
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
                "source": fix_meta(story.get("source")),
                "tags": fix_meta(story.get("tags")),
                "category": "Prophet Stories",
            }
            docs.append(Document(id=f"story:{sid}", text=full_text, metadata=metadata))
        return docs
