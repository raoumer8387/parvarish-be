import json

# Load the original hadith data
with open('d:\\\\FYP\\\\parvarish-be\\\\data\\\\hadith_quranic.json', 'r', encoding='utf-8') as f:
    hadith_quranic_data = json.load(f)

# Load the new hadith data
with open('d:\\\\FYP\\\\parvarish-be\\\\data\\\\hadith.json', 'r', encoding='utf-8') as f:
    hadith_data = json.load(f)

# Merge categories
hadith_quranic_data['categories'].extend(hadith_data['categories'])

# Update meta
hadith_quranic_data['meta']['entries_count'] = sum(len(cat['entries']) for cat in hadith_quranic_data['categories'])


# Write back to the original file
with open('d:\\\\FYP\\\\parvarish-be\\\\data\\\\hadith_quranic.json', 'w', encoding='utf-8') as f:
    json.dump(hadith_quranic_data, f, indent=2, ensure_ascii=False)

print("Successfully merged hadith.json into hadith_quranic.json")
