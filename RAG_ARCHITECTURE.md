# RAG System Architecture - With Islamic Scholar References

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                                 │
│  "My child is not listening and using too much mobile.               │
│   What should I do?"                                                 │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   CHATBOT ENDPOINT (/chat)                           │
│                   [app/routes/chatbot.py]                            │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA LOADER                                     │
│                  [app/rag/data_loader.py]                            │
│                                                                      │
│  Loads 3 JSON files:                                                 │
│  ┌────────────────────────────────────────────────────────┐         │
│  │ 1. hadith_quranic.json      → 23 documents             │         │
│  │    [Quran verses + Hadith + Tafsir]                    │         │
│  ├────────────────────────────────────────────────────────┤         │
│  │ 2. prophet_stories.json     → 100 documents            │         │
│  │    [Stories of Prophet Muhammad PBUH]                  │         │
│  ├────────────────────────────────────────────────────────┤         │
│  │ 3. islamic_refrences.json   → 53 documents   ⭐ NEW    │         │
│  │    [Classical Islamic Scholar References]               │         │
│  │    • Ihya Ulum ad-Din (Imam Al-Ghazali)                │         │
│  │    • Tafsir Ibn Kathir                                 │         │
│  │    • Adab al-Mufrad (Imam Bukhari)                     │         │
│  │    • Tarbiyat al-Awlad (Abdullah Nasih Ulwan)          │         │
│  │    • Many more...                                      │         │
│  └────────────────────────────────────────────────────────┘         │
│                                                                      │
│  Each document has:                                                  │
│  • id: "scholar:ref-001"                                             │
│  • text: "EN: ...\nUR: ...\nRM: ..."     ⭐ Multilingual           │
│  • metadata: {book, author, topic, tags, age_range}                 │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EMBEDDER                                        │
│                  [app/rag/embedder.py]                               │
│                                                                      │
│  Converts 176 documents into vector embeddings                       │
│  Using: sentence-transformers/all-MiniLM-L6-v2                       │
│  Stores in: ChromaDB (in-memory vector database)                     │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      RETRIEVER                                       │
│                  [app/rag/retriever.py]                              │
│                                                                      │
│  Performs semantic search (k=4)    ⭐ Increased from k=2             │
│  Returns top 4 most relevant chunks                                  │
│                                                                      │
│  Example Results:                                                    │
│  ┌──────────────────────────────────────────────────┐               │
│  │ Chunk 1: Islamic Scholar - Communication         │               │
│  │          Distance: 0.66 (most relevant)          │               │
│  ├──────────────────────────────────────────────────┤               │
│  │ Chunk 2: Islamic Scholar - Social Behavior       │               │
│  │          Book: Tarbiyat al-Awlad                 │               │
│  │          Author: Abdullah Nasih Ulwan            │               │
│  ├──────────────────────────────────────────────────┤               │
│  │ Chunk 3: Hadith - Kindness to Children          │               │
│  │          Source: Sahih Bukhari [Sahih]           │               │
│  ├──────────────────────────────────────────────────┤               │
│  │ Chunk 4: Quran - Parental Responsibility        │               │
│  │          Surah 17:23-24                          │               │
│  └──────────────────────────────────────────────────┘               │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   CONTEXT FORMATTER                                  │
│              [Retriever.format_context()]                            │
│                                                                      │
│  Formats chunks with proper citations:   ⭐ Enhanced                 │
│                                                                      │
│  [Source 1: Islamic Scholar | Topic: Communication]                  │
│  EN: Listening to a child builds trust...                            │
│  UR: بچے کی بات سننا اس کا اعتماد...                                │
│  RM: Bachay ki baat sunna uska itimad...                             │
│                                                                      │
│  [Source 2: Islamic Scholar | Tarbiyat al-Awlad – Abdullah Nasih     │
│   Ulwan | Topic: Social Behavior]                                    │
│  EN: Teaching children how to behave...                              │
│  UR: بچوں کو لوگوں کے ساتھ...                                       │
│  RM: Bachon ko logon ke sath...                                      │
│                                                                      │
│  [Source 3: hadith | Sahih Bukhari | Book 78 | Hadith #5997 [Sahih]] │
│  AR: ...                                                             │
│  EN: The Prophet (PBUH) said...                                      │
│  UR: رسول اللہ ﷺ نے فرمایا...                                         │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      LLM CLIENT                                      │
│                [app/services/llm_client.py]                          │
│                                                                      │
│  Model: google/gemini-2.5-flash (via OpenRouter)                    │
│  Max Tokens: 800   ⭐ Increased from 300                             │
│                                                                      │
│  System Prompt:    ⭐ Enhanced for multilingual + scholars           │
│  ┌────────────────────────────────────────────────────────┐         │
│  │ "You are Parvarish AI..."                              │         │
│  │ "Use Quran + Hadith + Stories + Scholars..."  ⭐ NEW   │         │
│  │ "Provide response in EN + UR + RM..."         ⭐ NEW   │         │
│  │ "Include book & author citations..."           ⭐ NEW   │         │
│  └────────────────────────────────────────────────────────┘         │
│                                                                      │
│  User Prompt:                                                        │
│  ┌────────────────────────────────────────────────────────┐         │
│  │ [CONTEXT with 4 sources]                               │         │
│  │ Question: My child is not listening...                 │         │
│  │ Provide answer in THREE LANGUAGES:   ⭐ NEW            │         │
│  │ ## English (EN): ...                                   │         │
│  │ ## Urdu (UR): ...                                      │         │
│  │ ## Roman Urdu (RM): ...                                │         │
│  └────────────────────────────────────────────────────────┘         │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      RESPONSE                                        │
│                                                                      │
│  ## English (EN):                                                    │
│  As Abdullah Nasih Ulwan mentions in Tarbiyat al-Awlad, teaching    │
│  children proper behavior with others is one of the most important  │
│  parental responsibilities. The Prophet (PBUH) said in Sahih        │
│  Bukhari that gentleness beautifies everything...                   │
│                                                                      │
│  Actionable tips:                                                    │
│  1. Set clear screen time limits                                    │
│  2. Create phone-free family time                                   │
│  3. Model good listening behavior                                   │
│                                                                      │
│  ## Urdu (UR):                                                       │
│  جیسا کہ عبداللہ ناصح علوان نے تربیت الاولاد میں ذکر کیا ہے...      │
│  [Same content in Urdu]                                              │
│                                                                      │
│  ## Roman Urdu (RM):                                                 │
│  Jaise ke Abdullah Nasih Ulwan ne Tarbiyat al-Awlad mein...         │
│  [Same content in Roman Urdu]                                        │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow Summary

```
JSON Files (3)  →  Data Loader  →  176 Documents
                                        ↓
                                   Embedder
                                        ↓
                              Vector Store (Chroma)
                                        ↓
User Query  →  Retriever (k=4)  →  4 Relevant Chunks
                                        ↓
                                Context Formatter
                                        ↓
                   [Formatted Context with Citations]
                                        ↓
                   LLM (with System + User Prompt)
                                        ↓
               Multilingual Response (EN + UR + RM)
```

## Key Improvements ⭐

1. **More Sources**: 23 + 100 + 53 = 176 total documents
2. **Better Retrieval**: k=4 instead of k=2 (more diverse)
3. **Multilingual**: All responses in 3 languages
4. **Better Citations**: Scholar names + book titles
5. **More Tokens**: 800 instead of 300 (supports longer multilingual answers)

## Document Count Breakdown

```
┌─────────────────────────┬───────┬──────────────────────────┐
│ Source Type             │ Count │ ID Prefix                │
├─────────────────────────┼───────┼──────────────────────────┤
│ Quran & Hadith          │  23   │ hadith:*                 │
│ Prophet Stories         │ 100   │ story:*                  │
│ Islamic Scholars ⭐     │  53   │ scholar:*                │
├─────────────────────────┼───────┼──────────────────────────┤
│ TOTAL                   │ 176   │                          │
└─────────────────────────┴───────┴──────────────────────────┘
```

## Scholar References Breakdown

Top Islamic Books Included:
- Ihya Ulum ad-Din (Imam Al-Ghazali)
- Tafsir Ibn Kathir
- Adab al-Mufrad (Imam Bukhari)
- Tarbiyat al-Awlad (Abdullah Nasih Ulwan)
- Usul al-Tarbiyah al-Islamiyyah
- Bidayat al-Mujtahid (Ibn Rushd)
- Sharh Sahih Muslim (Imam An-Nawawi)
- And many more...

Topics Covered:
- Mercy in Parenting
- Respect for Parents
- Teaching Manners
- Discipline Balance
- Gentleness with Children
- Communication Skills
- Social Behavior
- Role Modeling
- Teaching Prayer
- Screen Time Management
- Honesty & Truthfulness
- Emotional Intelligence
- And many more...

Age Ranges:
- All ages
- 6-10 years
- 6-14 years
- 7-14 years
- 10-14 years

---

**Last Updated**: December 8, 2025
