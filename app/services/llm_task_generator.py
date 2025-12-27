"""LLM service for generating Islamic-oriented tasks based on lacking analysis.

This module uses the LLM with RAG (Islamic references) to:
1. Explain the lacking area to parents
2. Provide Islamic guidance (Quran, Hadith, Prophet stories)
3. Generate personalized tasks for the child
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import logging

from app.services.llm_client import generate_response
from app.rag.retriever import Retriever
from app.rag.embedder import Embedder, VectorStoreConfig
from app.rag.data_loader import DataLoader

logger = logging.getLogger(__name__)

# System prompts for different lacking areas
LACKING_GUIDANCE_PROMPTS = {
    "presence_of_mind": """You are an Islamic parenting advisor. A child is showing difficulty with presence of mind (focus and attention).

Child's Performance: {score}/100
Analysis: The child struggles with focus, attention, and cognitive tasks in memory games.

Using the Islamic references provided below, write a SHORT guidance (max 300 words) that covers:
1. Why presence of mind matters in Islam (1-2 sentences with ONE Quran/Hadith reference)
2. One practical Islamic method to improve focus (dhikr, salah, or dua)
3. Simple advice for parents (2-3 tips)

Keep it concise, warm, and bilingual (Urdu/English mixed). Use bullet points for clarity.

Islamic References:
{islamic_context}

Response (max 300 words):""",

    "mood_identification": """You are an Islamic parenting advisor. A child is showing difficulty with mood identification and emotional awareness.

Child's Performance: {score}/100
Analysis: The child has challenges identifying and managing emotions appropriately.

Using the Islamic references provided below, write a SHORT guidance (max 300 words) that covers:
1. Importance of emotional intelligence in Islam (1-2 sentences with ONE reference)
2. One Prophet's example of emotional control
3. Simple practical tips for parents (2-3 tips)

Keep it concise, warm, and bilingual (Urdu/English mixed). Use bullet points for clarity.

Islamic References:
{islamic_context}

Response (max 300 words):""",

    "learning_capability": """You are an Islamic parenting advisor. A child is showing difficulty with learning and retaining Islamic knowledge.

Child's Performance: {score}/100
Analysis: The child struggles with learning Islamic concepts and quiz performance.

Using the Islamic references provided below, write a SHORT guidance (max 300 words) that covers:
1. Value of seeking knowledge in Islam (1-2 sentences with ONE reference)
2. One practical method to make learning enjoyable
3. Simple tips and one dua for parents (2-3 tips total)

Keep it concise, warm, and bilingual (Urdu/English mixed). Use bullet points for clarity.

Islamic References:
{islamic_context}

Response (max 300 words):""",

    "behavior_identification": """You are an Islamic parenting advisor. A child is showing difficulty with behavior identification and moral decision-making.

Child's Performance: {score}/100
Analysis: The child has challenges making moral decisions and understanding appropriate behavior.

Using the Islamic references provided below, write a SHORT guidance (max 300 words) that covers:
1. Islamic teachings on good character/Akhlaq (1-2 sentences with ONE reference)
2. One Prophet's example as role model
3. Simple practical guidance for parents (2-3 tips)

Keep it concise, warm, and bilingual (Urdu/English mixed). Use bullet points for clarity.

Islamic References:
{islamic_context}

Response (max 300 words):"""
}

TASK_GENERATION_PROMPTS = {
    "presence_of_mind": """Based on the child's lacking in presence of mind, generate 3 age-appropriate Islamic tasks.

Child Age: {age} years
Current Score: {score}/100

Using the Islamic references below, create tasks that:
- Improve focus and attention through Islamic practices
- Are engaging and achievable
- Include Islamic elements (dua, dhikr, stories, etc.)

Return ONLY a JSON array with this exact format:
[
  {{
    "title": "Short task title (English)",
    "description": "Detailed description in Urdu/Roman Urdu with English mixed",
    "difficulty": 1-3,
    "xp_reward": 10-30,
    "islamic_reference": "Brief reference used"
  }}
]

Islamic References:
{islamic_context}

Tasks JSON:""",

    "mood_identification": """Based on the child's lacking in mood identification, generate 3 age-appropriate Islamic tasks.

Child Age: {age} years
Current Score: {score}/100

Using the Islamic references below, create tasks that:
- Help identify and manage emotions through Islamic teachings
- Include reflection and self-awareness activities
- Teach Islamic responses to different emotions

Return ONLY a JSON array with this exact format:
[
  {{
    "title": "Short task title (English)",
    "description": "Detailed description in Urdu/Roman Urdu with English mixed",
    "difficulty": 1-3,
    "xp_reward": 10-30,
    "islamic_reference": "Brief reference used"
  }}
]

Islamic References:
{islamic_context}

Tasks JSON:""",

    "learning_capability": """Based on the child's lacking in learning capability, generate 3 age-appropriate Islamic tasks.

Child Age: {age} years
Current Score: {score}/100

Using the Islamic references below, create tasks that:
- Make Islamic learning fun and memorable
- Use storytelling and interactive methods
- Build confidence in learning

Return ONLY a JSON array with this exact format:
[
  {{
    "title": "Short task title (English)",
    "description": "Detailed description in Urdu/Roman Urdu with English mixed",
    "difficulty": 1-3,
    "xp_reward": 10-30,
    "islamic_reference": "Brief reference used"
  }}
]

Islamic References:
{islamic_context}

Tasks JSON:""",

    "behavior_identification": """Based on the child's lacking in behavior identification, generate 3 age-appropriate Islamic tasks.

Child Age: {age} years
Current Score: {score}/100

Using the Islamic references below, create tasks that:
- Teach moral decision-making through Islamic examples
- Include practical scenarios and role-playing
- Focus on Prophet's character traits

Return ONLY a JSON array with this exact format:
[
  {{
    "title": "Short task title (English)",
    "description": "Detailed description in Urdu/Roman Urdu with English mixed",
    "difficulty": 1-3,
    "xp_reward": 10-30,
    "islamic_reference": "Brief reference used"
  }}
]

Islamic References:
{islamic_context}

Tasks JSON:"""
}


def get_retriever() -> Retriever:
    """Initialize and return RAG retriever with Islamic knowledge."""
    try:
        logger.info("Initializing RAG retriever with Islamic knowledge...")
        
        # Initialize embedder with default config
        embedder = Embedder()
        logger.info("Embedder initialized successfully")
        
        # Check if collection has data, if not load it
        collection = embedder.as_retriever()
        count = collection.count()
        logger.info(f"Current collection document count: {count}")
        
        if count == 0:
            # Load and index data
            logger.info("No data in collection, loading Islamic knowledge...")
            data_loader = DataLoader()
            docs = data_loader.load()
            logger.info(f"Loaded {len(docs)} documents from data files")
            
            if len(docs) > 0:
                embedder.build_index(docs)
                logger.info(f"Successfully indexed {len(docs)} documents into vector store")
            else:
                logger.warning("No documents loaded from data files")
                return None
        else:
            logger.info(f"Using existing collection with {count} documents")
        
        retriever = Retriever(collection)
        logger.info("RAG retriever ready")
        return retriever
        
    except Exception as e:
        logger.error(f"Error initializing retriever: {e}", exc_info=True)
        return None


def generate_lacking_guidance(
    lacking_area: str,
    score: float,
    child_name: str,
    child_age: Optional[int] = None
) -> str:
    """Generate Islamic guidance for parents on how to address child's lacking.
    
    Args:
        lacking_area: One of presence_of_mind, mood_identification, learning_capability, behavior_identification
        score: Child's score in that area (0-100)
        child_name: Child's name
        child_age: Child's age (optional)
    
    Returns:
        Guidance text with Islamic references
    """
    if lacking_area not in LACKING_GUIDANCE_PROMPTS:
        logger.error(f"Unknown lacking area: {lacking_area}")
        return "Unable to generate guidance for this area."
    
    # Retrieve relevant Islamic context
    retriever = get_retriever()
    islamic_context = ""
    
    if retriever:
        try:
            # Query based on lacking area
            queries = {
                "presence_of_mind": "focus attention mindfulness concentration dhikr",
                "mood_identification": "emotions anger patience forgiveness emotional control",
                "learning_capability": "seeking knowledge learning education wisdom",
                "behavior_identification": "good character akhlaq morality prophet behavior"
            }
            
            query = queries.get(lacking_area, "Islamic guidance parenting")
            chunks = retriever.query(query, k=3)
            islamic_context = Retriever.format_context(chunks)
        except Exception as e:
            logger.error(f"Error retrieving Islamic context: {e}")
            islamic_context = "Unable to retrieve references at this time."
    
    # Generate guidance
    prompt_template = LACKING_GUIDANCE_PROMPTS[lacking_area]
    prompt = prompt_template.format(
        score=round(score, 1),
        child_name=child_name,
        islamic_context=islamic_context
    )
    
    try:
        messages = [{"role": "user", "content": prompt}]
        response = generate_response(messages)
        return response
    except Exception as e:
        logger.error(f"Error generating guidance: {e}")
        return "Unable to generate guidance at this time. Please try again."


def generate_islamic_tasks(
    db: Session,
    child_id: int,
    lacking_area: str,
    score: float,
    child_age: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Generate Islamic-oriented tasks using LLM based on lacking analysis.
    
    Args:
        db: Database session
        child_id: Child's ID
        lacking_area: The identified lacking area
        score: Child's score in that area
        child_age: Child's age (optional)
    
    Returns:
        List of task dictionaries
    """
    if lacking_area not in TASK_GENERATION_PROMPTS:
        logger.error(f"Unknown lacking area: {lacking_area}")
        return []
    
    # Retrieve relevant Islamic context
    retriever = get_retriever()
    islamic_context = ""
    
    if retriever:
        try:
            queries = {
                "presence_of_mind": "focus dhikr mindfulness concentration Islamic practice",
                "mood_identification": "emotions patience forgiveness self-control",
                "learning_capability": "seeking knowledge Quran memorization learning",
                "behavior_identification": "good character Prophet Muhammad akhlaq morality"
            }
            
            query = queries.get(lacking_area, "Islamic tasks for children")
            chunks = retriever.query(query, k=4)
            islamic_context = Retriever.format_context(chunks)
        except Exception as e:
            logger.error(f"Error retrieving Islamic context: {e}")
            islamic_context = "Islamic teachings and guidance"
    
    # Generate tasks
    prompt_template = TASK_GENERATION_PROMPTS[lacking_area]
    prompt = prompt_template.format(
        age=child_age or 10,
        score=round(score, 1),
        islamic_context=islamic_context
    )
    
    try:
        messages = [{"role": "user", "content": prompt}]
        response = generate_response(messages)
        
        # Parse JSON response
        import json
        # Try to extract JSON array from response
        response = response.strip()
        
        # Find JSON array in response
        start_idx = response.find('[')
        end_idx = response.rfind(']') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_str = response[start_idx:end_idx]
            tasks = json.loads(json_str)
            
            # Validate and enhance tasks
            validated_tasks = []
            for task in tasks:
                if isinstance(task, dict) and "title" in task and "description" in task:
                    validated_tasks.append({
                        "title": task.get("title", "Islamic Task"),
                        "description": task.get("description", ""),
                        "difficulty": task.get("difficulty", 2),
                        "xp_reward": task.get("xp_reward", 20),
                        "islamic_reference": task.get("islamic_reference", ""),
                        "category": _map_lacking_to_category(lacking_area)
                    })
            
            return validated_tasks[:3]  # Return max 3 tasks
        else:
            logger.error(f"No JSON array found in response: {response[:200]}")
            return _get_fallback_tasks(lacking_area, child_age)
            
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON tasks: {e}")
        return _get_fallback_tasks(lacking_area, child_age)
    except Exception as e:
        logger.error(f"Error generating tasks: {e}")
        return _get_fallback_tasks(lacking_area, child_age)


def _map_lacking_to_category(lacking_area: str) -> str:
    """Map lacking area to task category."""
    mapping = {
        "presence_of_mind": "cognitive",
        "mood_identification": "emotional",
        "learning_capability": "cognitive",
        "behavior_identification": "moral"
    }
    return mapping.get(lacking_area, "habitual")


def _get_fallback_tasks(lacking_area: str, child_age: Optional[int]) -> List[Dict[str, Any]]:
    """Return fallback tasks if LLM generation fails."""
    fallback_tasks = {
        "presence_of_mind": [
            {
                "title": "Morning Dhikr Focus",
                "description": "Har subah SubhanAllah, Alhamdulillah, Allahu Akbar 10 baar dhyan se kaho. Focus practice ke liye bohot acha hai.",
                "difficulty": 1,
                "xp_reward": 15,
                "category": "cognitive",
                "islamic_reference": "Dhikr/Remembrance of Allah"
            }
        ],
        "mood_identification": [
            {
                "title": "Emotion Journal",
                "description": "Din mein apne jazbat likho aur Quran ki koi ayat yaad karo jo us feeling se related ho.",
                "difficulty": 2,
                "xp_reward": 20,
                "category": "emotional",
                "islamic_reference": "Self-reflection in Islam"
            }
        ],
        "learning_capability": [
            {
                "title": "Daily Surah Learning",
                "description": "Har din ek choti surah ya 3 ayat yaad karo aur family ko sunao.",
                "difficulty": 2,
                "xp_reward": 25,
                "category": "cognitive",
                "islamic_reference": "Quran memorization"
            }
        ],
        "behavior_identification": [
            {
                "title": "Prophet's Character Practice",
                "description": "Prophet Muhammad (PBUH) ki ek achi adat choose karo aur aaj us pe amal karo.",
                "difficulty": 2,
                "xp_reward": 20,
                "category": "moral",
                "islamic_reference": "Following Sunnah"
            }
        ]
    }
    
    return fallback_tasks.get(lacking_area, [])
