import json

# Load the original hadith data
with open('d:\\\\FYP\\\\parvarish-be\\\\data\\\\hadith_quranic.json', 'r', encoding='utf-8') as f:
    hadith_data = json.load(f)

# Load the new quranic data
with open('d:\\\\FYP\\\\parvarish-be\\\\data\\\\quranic_verse.json', 'r', encoding='utf-8') as f:
    quranic_data = json.load(f)

# Merge categories
hadith_data['categories'].extend(quranic_data['categories'])

# Update meta
hadith_data['meta']['entries_count'] = sum(len(cat['entries']) for cat in hadith_data['categories'])


# Write back to the original file
with open('d:\\\\FYP\\\\parvarish-be\\\\data\\\\hadith_quranic.json', 'w', encoding='utf-8') as f:
    json.dump(hadith_data, f, indent=2, ensure_ascii=False)

print("Successfully merged quranic_verse.json into hadith_quranic.json")
