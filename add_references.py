import json

hadith_file_path = 'd:\\FYP\\parvarish-be\\data\\new_hadith.json'

# Data for the first 10 hadiths
update_data = {
    "H001": {"source": "Sahih al-Bukhari", "reference": "5997"},
    "H002": {"source": "Sahih al-Bukhari", "reference": "6114"},
    "H003": {"source": "Sahih Muslim", "reference": "2593"},
    "H004": {"source": "Sahih al-Bukhari", "reference": "2587"},
    "H005": {"source": "Jami at-Tirmidhi", "reference": "1952"},
    "H006": {"source": "Sahih Muslim", "reference": "675"},
    "H007": {"source": "Sahih al-Bukhari", "reference": "893"},
    "H008": {"source": "Sahih al-Bukhari", "reference": "6138"},
    "H009": {"source": "Jami at-Tirmidhi", "reference": "1919"},
    "H010": {"source": "Sahih al-Bukhari", "reference": "6094"},
    "H011": {"source": "Sahih al-Bukhari", "reference": "6094"},
    "H012": {"source": "Jami at-Tirmidhi", "reference": "1956"},
    "H013": {"source": "Sahih al-Bukhari", "reference": "13"},
    "H014": {"source": "Sahih Muslim", "reference": "223"},
    "H015": {"source": "Sahih al-Bukhari", "reference": "1283"},
    "H016": {"source": "Sahih Muslim", "reference": "2699"},
    "H017": {"source": "Jami at-Tirmidhi", "reference": "1955"},
    "H018": {"source": "Sahih al-Bukhari", "reference": "9"},
    "H019": {"source": "Sahih al-Bukhari", "reference": "6125"},
    "H020": {"source": "Al-Adab Al-Mufrad", "reference": "594"},
    "H021": {"source": "Jami at-Tirmidhi", "reference": "3895"},
    "H022": {"source": "Jami at-Tirmidhi", "reference": "2317"},
    "H023": {"source": "Sahih al-Bukhari", "reference": "10"},
    "H024": {"source": "Jami at-Tirmidhi", "reference": "1987"},
    "H025": {"source": "Jami at-Tirmidhi", "reference": "1987"},
    "H026": {"source": "Jami at-Tirmidhi", "reference": "1924"},
    "H027": {"source": "Sahih Muslim", "reference": "54"},
    "H028": {"source": "Sahih al-Bukhari", "reference": "6064"},
    "H029": {"source": "Sahih al-Bukhari", "reference": "6065"},
    "H030": {"source": "At-Tabarani (Al-Kabir)", "reference": "10307"},
    "H031": {"source": "Sahih Muslim", "reference": "2563"},
    "H032": {"source": "Sahih al-Bukhari", "reference": "6125"},
    "H033": {"source": "Sahih al-Bukhari", "reference": "6094"},
    "H034": {"source": "Sahih al-Bukhari", "reference": "5985"},
    "H035": {"source": "Quranic Basis / Hadith", "reference": "(Surah Al-A'raf 7:26)"},
    "H036": {"source": "Sahih al-Bukhari", "reference": "6473 (General Prohibition)"},
    "H037": {"source": "Sahih al-Bukhari", "reference": "1469"},
    "H038": {"source": "Jami at-Tirmidhi", "reference": "1924"},
    "H039": {"source": "Sahih Muslim", "reference": "1914"},
    "H040": {"source": "Sahih Muslim", "reference": "55"},
    "H041": {"source": "Sahih Muslim", "reference": "101"},
    "H042": {"source": "Sahih al-Bukhari", "reference": "6063"},
    "H043": {"source": "Sunan Ibn Majah", "reference": "224"},
    "H044": {"source": "Sahih al-Bukhari", "reference": "1"},
    "H045": {"source": "Jami at-Tirmidhi", "reference": "1919"},
    "H046": {"source": "Sahih al-Bukhari", "reference": "5997"},
    "H047": {"source": "Sunan Abi Dawud", "reference": "4833"},
    "H048": {"source": "At-Tabarani (Al-Awsat)", "reference": "5787"},
    "H049": {"source": "Sahih al-Bukhari", "reference": "2989"},
    "H050": {"source": "Musnad Ahmad", "reference": "7047"}
}

with open(hadith_file_path, 'r', encoding='utf-8') as f:
    hadiths = json.load(f)

for hadith in hadiths:
    hadith_id = hadith.get("id")
    if hadith_id in update_data:
        hadith["source"] = update_data[hadith_id]["source"]
        hadith["reference"] = update_data[hadith_id]["reference"]
    else:
        if "source" not in hadith:
            hadith["source"] = None
        if "reference" not in hadith:
            hadith["reference"] = None

with open(hadith_file_path, 'w', encoding='utf-8') as f:
    json.dump(hadiths, f, indent=2, ensure_ascii=False)

print(f"Updated sources and references in {hadith_file_path}")
