import json

def transform_hadith_data(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        new_hadiths = json.load(f)

    grouped_by_topic = {}
    for hadith in new_hadiths:
        topic = hadith.get('topic', 'Uncategorized')
        if topic not in grouped_by_topic:
            grouped_by_topic[topic] = []
        grouped_by_topic[topic].append(hadith)

    categories = []
    for topic, hadiths in grouped_by_topic.items():
        entries = []
        for hadith in hadiths:
            entry = {
                "id": hadith.get("id"),
                "type": "hadith",
                "arabic": None,
                "transliteration": hadith.get("text_roman_urdu"),
                "english_translation": hadith.get("text_en"),
                "urdu_translation": hadith.get("text_urdu"),
                "tags": hadith.get("tags", []),
                "age_range": "all",
                "source": {
                    "collection": hadith.get("source"),
                    "hadith_number": None # Not available in new file
                },
                "hadith_classification": hadith.get("authenticity"),
                "tafsir_excerpt": hadith.get("parenting_insight"),
                "short_explanation": {
                    "en": hadith.get("parenting_insight"),
                    "ur": ""
                },
                "practical_tip": {
                    "en": "",
                    "ur": ""
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
            "created_by": "Assistant (transformed from new_hadith.json)",
            "entries_count": len(new_hadiths)
        }
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)

input_path = 'd:\\\\FYP\\\\parvarish-be\\\\data\\\\new_hadith.json'
output_path = 'd:\\\\FYP\\\\parvarish-be\\\\data\\\\hadith.json'
transform_hadith_data(input_path, output_path)
print(f"Transformed data saved to {output_path}")
