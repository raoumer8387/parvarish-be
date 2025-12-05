"""Static task templates mapped by behavior category.

These templates are used to instantiate `ChildTask` entries. Keep titles short and actionable.
"""

TASK_TEMPLATES = {
    "emotional": [
        {"title": "Deep Breathing Exercise", "description": "Guide the child to take 5 slow deep breaths and relax shoulders."},
        {"title": "Feelings Talk", "description": "Discuss one emotion the child felt today and why."},
        {"title": "Calm Corner Setup", "description": "Help the child arrange a quiet spot with a book or soft toy."},
    ],
    "social": [
        {"title": "Sharing Activity", "description": "Encourage sharing a toy or snack with a sibling/friend."},
        {"title": "Kind Words Challenge", "description": "Ask the child to say three kind sentences to family members."},
    ],
    "moral": [
        {"title": "Truth Reflection", "description": "Talk about why telling the truth matters in daily life."},
        {"title": "Helping Task", "description": "Assign a small helpful chore (e.g., organizing books)."},
    ],
    "habitual": [
        {"title": "Bedtime Routine Review", "description": "Walk through tonight's routine steps (brush, book, sleep)."},
        {"title": "Morning Checklist", "description": "Create a 3-step checklist for tomorrow morning."},
    ],
    "cognitive": [
        {"title": "Focus Puzzle", "description": "Give a short puzzle or memory game (5 minutes)."},
        {"title": "Reading Minute", "description": "Read one page together and ask two comprehension questions."},
    ],
    "physical": [
        {"title": "Mini Stretch", "description": "Do a 2-minute stretch: arms, legs, neck gently."},
        {"title": "Active Break", "description": "Jumping jacks or a brisk walk for 3 minutes."},
    ],
}

ALLOWED_CATEGORIES = set(TASK_TEMPLATES.keys())
