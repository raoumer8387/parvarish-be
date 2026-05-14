import json

def transform_data(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        new_verses = json.load(f)

    # Group verses by topic
    grouped_by_topic = {}
    for verse in new_verses:
        topic = verse.get('topic', 'Uncategorized')
        if topic not in grouped_by_topic:
            grouped_by_topic[topic] = []
        grouped_by_topic[topic].append(verse)

    # Create the final structure
    categories = []
    for topic, verses in grouped_by_topic.items():
        entries = []
        for verse in verses:
            # Parse reference
            surah, ayah = (verse.get('reference', '0:0').split(':') + [None, None])[:2]
            
            entry = {
                "id": verse.get("id"),
                "type": "ayat" if verse.get("source") == "Qur'an" else "unknown",
                "arabic": None,  # Not available in new file
                "transliteration": verse.get("text_roman_urdu"),
                "english_translation": verse.get("text_en"),
                "urdu_translation": verse.get("text_urdu"),
                "tags": verse.get("tags", []),
                "age_range": "all",  # Default value
                "source": {
                    "book": "Qur'an",
                    "surah": int(surah) if surah and surah.isdigit() else None,
                    "ayah": int(ayah) if ayah and ayah.isdigit() else None
                },
                "hadith_classification": None,
                "tafsir_excerpt": verse.get("parenting_insight"),
                "short_explanation": {
                    "en": verse.get("parenting_insight"),
                    "ur": "" # Not available
                },
                "practical_tip": {
                    "en": "", # Not available
                    "ur": ""  # Not available
                }
            }
            entries.append(entry)
        
        categories.append({
            "category": topic.replace('_', ' ').title(),
            "entries": entries
        })

    final_data = {
        "project": "Parawarish AI - Parenting (Islamic sources)",
        "language": "bilingual (English + Urdu)",
        "categories": categories,
        "meta": {
            "created_by": "Assistant (transformed from new_quranic_verse.json)",
            "entries_count": len(new_verses)
        }
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)

# Execute the transformation
input_path = 'd:\\\\FYP\\\\parvarish-be\\\\data\\\\new_quranic_verse.json'
output_path = 'd:\\\\FYP\\\\parvarish-be\\\\data\\\\quranic_verse.json'
transform_data(input_path, output_path)
print(f"Transformed data saved to {output_path}")
