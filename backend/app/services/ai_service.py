"""AI-powered meal plan generation service.

Streams meal plan suggestions from OpenAI's GPT-4o-mini via Server-Sent Events (SSE).
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.nutrition import MealPlanRequest

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an expert South Asian fitness nutritionist. Generate detailed,
practical meal plans based on the user's requirements. Focus on foods commonly
available in South Asian cuisine (Pakistan, India, Bangladesh, Nepal, Sri Lanka).

For each meal, provide:
- Meal name and type (breakfast, lunch, dinner, snack)
- Specific foods with portion sizes
- Approximate calories, protein, carbs, and fat per food
- Daily totals

Format your response as structured JSON inside a Markdown code block:
```json
{
  "meals": [
    {
      "type": "breakfast",
      "name": "...",
      "foods": [
        {"name": "...", "portion": "...", "calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
      ],
      "meal_calories": 0,
      "meal_protein_g": 0,
      "meal_carbs_g": 0,
      "meal_fat_g": 0
    }
  ],
  "daily_totals": {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0},
  "tips": ["..."]
}
```

Be specific with portions (e.g., "1 cup cooked rice", "150g chicken breast").
Always include at least one meal of each type: breakfast, lunch, dinner.
"""


def _build_user_message(payload: MealPlanRequest) -> str:
    """Build the user prompt from the request payload."""
    parts: list[str] = ["Create a 1-day meal plan with the following requirements:\n"]

    if payload.target_calories is not None:
        parts.append(f"- Target calories: {payload.target_calories:.0f} kcal/day")
    else:
        parts.append("- Target calories: calculate based on general fitness goals")

    if payload.protein_g is not None:
        parts.append(f"- Target protein: {payload.protein_g:.0f}g/day")

    if payload.dietary_preferences:
        parts.append(f"- Dietary preferences: {', '.join(payload.dietary_preferences)}")

    if payload.allergies:
        parts.append(f"- Allergies to exclude: {', '.join(payload.allergies)}")

    if payload.cuisine_type:
        parts.append(f"- Preferred cuisine: {payload.cuisine_type}")

    parts.append("\nProvide realistic South Asian foods with accurate nutrition data.")
    return "\n".join(parts)


async def generate_meal_plan_stream(
    payload: MealPlanRequest,
) -> AsyncGenerator[str, None]:
    """Generate a meal plan using OpenAI GPT-4o-mini with streaming.

    Yields SSE-formatted chunks:
        data: {"text": "<chunk>"}\n\n
    Ends with:
        data: [DONE]\n\n
    """
    api_key = settings.openai_api_key
    model = settings.openai_model

    if not api_key:
        logger.error("OPENAI_API_KEY is not configured")
        yield _sse_chunk({"error": "AI service is not configured. Set OPENAI_API_KEY."})
        yield "data: [DONE]\n\n"
        return

    client = AsyncOpenAI(api_key=api_key)
    user_message = _build_user_message(payload)

    logger.info(
        "Streaming AI meal plan: calories=%s protein=%s cuisine=%s",
        payload.target_calories,
        payload.protein_g,
        payload.cuisine_type,
    )

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            stream=True,
            temperature=0.7,
            max_tokens=2000,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield _sse_chunk({"text": delta.content})

    except Exception:
        logger.exception("OpenAI streaming failed")
        yield _sse_chunk({"error": "Failed to generate meal plan. Please try again."})

    yield "data: [DONE]\n\n"


def _sse_chunk(data: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


# ═══════════════════════════════════════════════════════════════════════
# Workout Generation
# ═══════════════════════════════════════════════════════════════════════

WORKOUT_SYSTEM_PROMPT = """You are an expert South Asian fitness coach and strength & conditioning specialist.
Generate detailed, progressive-overload workout routines tailored to the user's
experience level, goals, available equipment, and training split.

For each workout day, provide:
- Day name and focus (e.g., "Day 1 — Push")
- Each exercise with:
  - Exercise name (use standard gym terminology)
  - Sets × Reps (e.g., 4 × 8-10)
  - Rest interval (e.g., 90s, 2 min)
  - Tempo if relevant (e.g., 3-1-2-0)
  - Optional notes (e.g., "focus on mind-muscle connection")
- Warm-up and cool-down for each day
- Progressive overload notes for week-over-week progression

Format your response as clean Markdown with clear headers, tables where
appropriate, and bullet points. Use this structure:

# [Goal] Workout Program
## Overview
- Split type, duration, frequency
- Progressive overload strategy
## Day 1 — [Focus]
### Warm-up
### Working Sets
| Exercise | Sets × Reps | Rest | Notes |
|----------|-------------|------|-------|
| ... | ... | ... | ... |
### Cool-down
## Day 2 — [Focus]
...
## Weekly Progression Notes
- Week 1: ... (introduction)
- Week 2: ... (volume increase)
- Week 3: ... (intensity increase)
- Week 4: ... (deload)

Be specific, practical, and evidence-based. Include rep ranges that match
the user's experience level.
"""


def _build_workout_user_message(
    goal: str,
    experience_level: str,
    split: str,
    equipment: str,
) -> str:
    """Build the user prompt for workout generation."""
    goal_labels = {
        "strength": "Maximum Strength",
        "hypertrophy": "Muscle Hypertrophy",
        "endurance": "Muscular Endurance",
        "fat_loss": "Fat Loss & Conditioning",
    }
    split_labels = {
        "upper_lower": "Upper/Lower Split",
        "push_pull_legs": "Push/Pull/Legs Split",
        "full_body": "Full Body Training",
    }
    equipment_labels = {
        "gym": "Full Gym (barbells, cables, machines)",
        "bodyweight": "Bodyweight Only",
        "dumbbells": "Dumbbells + Basic Equipment",
    }

    return (
        f"Generate a complete workout program with the following specifications:\n\n"
        f"- Primary Goal: {goal_labels.get(goal, goal)}\n"
        f"- Experience Level: {experience_level.capitalize()}\n"
        f"- Training Split: {split_labels.get(split, split)}\n"
        f"- Equipment Available: {equipment_labels.get(equipment, equipment)}\n\n"
        f"Create a detailed, structured program with specific exercises, sets, reps, "
        f"rest intervals, and progressive overload notes. Make it practical and "
        f"achievable for the stated experience level."
    )


async def generate_workout_stream(
    goal: str,
    experience_level: str,
    split: str,
    equipment: str,
) -> AsyncGenerator[str, None]:
    """Generate a workout plan using OpenAI GPT-4o-mini with streaming.

    Yields SSE-formatted chunks matching the meal plan streaming pattern.
    """
    api_key = settings.openai_api_key
    model = settings.openai_model

    if not api_key:
        logger.error("OPENAI_API_KEY is not configured")
        yield _sse_chunk({"error": "AI service is not configured. Set OPENAI_API_KEY."})
        yield "data: [DONE]\n\n"
        return

    client = AsyncOpenAI(api_key=api_key)
    user_message = _build_workout_user_message(goal, experience_level, split, equipment)

    logger.info(
        "Streaming AI workout: goal=%s experience=%s split=%s equipment=%s",
        goal, experience_level, split, equipment,
    )

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": WORKOUT_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            stream=True,
            temperature=0.7,
            max_tokens=3000,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield _sse_chunk({"text": delta.content})

    except Exception:
        logger.exception("OpenAI workout streaming failed")
        yield _sse_chunk({"error": "Failed to generate workout plan. Please try again."})

    yield "data: [DONE]\n\n"
