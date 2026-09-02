"""AI-powered meal plan generation service.

Streams meal plan suggestions from OpenAI's GPT-4o-mini via Server-Sent Events (SSE).
Falls back to realistic mock responses when credits are exhausted or the API is
unreachable, so the frontend streaming UX still works in sandbox / staging.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator

from openai import (
    APIConnectionError,
    APIStatusError,
    AsyncOpenAI,
    AuthenticationError,
    RateLimitError,
)

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.nutrition import MealPlanRequest

logger = get_logger(__name__)

# ── OpenAI exception types we treat as "transient / quota" ───────────
_OPENAI_ERRORS = (
    RateLimitError,
    APIConnectionError,
    AuthenticationError,
    APIStatusError,
)

# Delay (seconds) between SSE chunk yields during mock streaming so the
# frontend cursor animation still runs smoothly.
_MOCK_CHUNK_DELAY = 0.02

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


async def _stream_sandbox_chunks(
    text: str,
    sandbox_label: str = "sandbox",
) -> AsyncGenerator[str, None]:
    """Yield *text* in small SSE chunks so the frontend cursor still animates.

    The first chunk contains a ``"sandbox": true`` flag so the UI can show
    an informational banner (e.g. "Using offline AI model — Sandbox mode").
    """
    # Send the sandbox flag in the very first chunk.
    yield _sse_chunk({"sandbox": True, "text": ""})

    chunk_size = 8  # characters per chunk
    for i in range(0, len(text), chunk_size):
        yield _sse_chunk({"text": text[i : i + chunk_size]})
        await asyncio.sleep(_MOCK_CHUNK_DELAY)


async def generate_meal_plan_stream(
    payload: MealPlanRequest,
) -> AsyncGenerator[str, None]:
    """Generate a meal plan using OpenAI GPT-4o-mini with streaming.

    Yields SSE-formatted chunks:
        data: {"text": "<chunk>"}\n\n

    Ends with:
        data: [DONE]\n\n

    If the OpenAI call fails (quota exhausted, rate-limited, network error, etc.)
    a realistic fallback plan is streamed instead so the frontend UX is never
    broken.
    """
    api_key = settings.openai_api_key
    model = settings.openai_model

    if not api_key:
        logger.warning("OPENAI_API_KEY is not configured — falling back to sandbox")
        async for chunk in _stream_sandbox_chunks(_MOCK_MEAL_PLAN, "meal-plan"):
            yield chunk
        yield "data: [DONE]\n\n"
        return

    client = _build_openai_client(api_key)
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

    except _OPENAI_ERRORS as exc:
        logger.warning(
            "OpenAI API unavailable (%s: %s) — streaming sandbox fallback",
            type(exc).__name__,
            exc,
        )
        async for chunk in _stream_sandbox_chunks(_MOCK_MEAL_PLAN, "meal-plan"):
            yield chunk

    except Exception:
        logger.exception("Unexpected error during OpenAI meal plan streaming")
        async for chunk in _stream_sandbox_chunks(_MOCK_MEAL_PLAN, "meal-plan"):
            yield chunk

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

    Falls back to a realistic mock workout when the OpenAI API is unavailable.
    """
    api_key = settings.openai_api_key
    model = settings.openai_model

    if not api_key:
        logger.warning("OPENAI_API_KEY is not configured — falling back to sandbox")
        async for chunk in _stream_sandbox_chunks(_MOCK_WORKOUT, "workout"):
            yield chunk
        yield "data: [DONE]\n\n"
        return

    client = _build_openai_client(api_key)
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

    except _OPENAI_ERRORS as exc:
        logger.warning(
            "OpenAI API unavailable (%s: %s) — streaming sandbox workout fallback",
            type(exc).__name__,
            exc,
        )
        async for chunk in _stream_sandbox_chunks(_MOCK_WORKOUT, "workout"):
            yield chunk

    except Exception:
        logger.exception("Unexpected error during OpenAI workout streaming")
        async for chunk in _stream_sandbox_chunks(_MOCK_WORKOUT, "workout"):
            yield chunk

    yield "data: [DONE]\n\n"


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════


def _build_openai_client(api_key: str) -> AsyncOpenAI:
    """Create an AsyncOpenAI client — separated for easy mocking in tests."""
    return AsyncOpenAI(api_key=api_key)


# ═══════════════════════════════════════════════════════════════════════
# Sandbox Fallback Content
# ═══════════════════════════════════════════════════════════════════════

_MOCK_MEAL_PLAN = """# High-Protein South Asian Meal Plan

> 🧪 **Sandbox Mode** — This plan was generated by the local fallback model. For AI-personalised plans, add a valid OpenAI API key.

## 📋 Daily Summary

| Nutrient | Target | Planned |
|----------|--------|---------|
| Calories | 2,200 kcal | 2,185 kcal |
| Protein | 120 g | 124 g |
| Carbs | 250 g | 242 g |
| Fat | 65 g | 68 g |

---

## 🌅 Breakfast — Desi Protein Oats (540 kcal)

| Food | Portion | Cal | Protein | Carbs | Fat |
|------|---------|-----|---------|-------|-----|
| Steel-cut oats | 1 cup (80 g) | 300 | 10 g | 54 g | 5 g |
| Milk (whole) | 1 cup (240 ml) | 150 | 8 g | 12 g | 8 g |
| Whey protein | 1 scoop (30 g) | 120 | 24 g | 3 g | 1.5 g |
| Banana | 1 medium | 105 | 1.3 g | 27 g | 0.4 g |
| Almonds | 6 pieces (10 g) | 58 | 2.1 g | 2.1 g | 5 g |

**Meal Total:** 540 kcal · 24 g protein · 52 g carbs · 12 g fat

---

## ☀️ Lunch — Chicken Tikka Brown Rice Bowl (680 kcal)

| Food | Portion | Cal | Protein | Carbs | Fat |
|------|---------|-----|---------|-------|-----|
| Chicken tikka (grilled) | 200 g | 330 | 46 g | 2 g | 14 g |
| Brown rice (cooked) | 1.5 cups (285 g) | 345 | 7.5 g | 72 g | 2.8 g |
| Raita (yogurt + cucumber) | ½ cup | 60 | 3 g | 5 g | 2.5 g |
| Mixed salad (kachumber) | 1 bowl | 40 | 1.5 g | 8 g | 0.2 g |

**Meal Total:** 680 kcal · 48 g protein · 87 g carbs · 20 g fat

---

## 🌆 Snack — Paneer Tikka Bites (310 kcal)

| Food | Portion | Cal | Protein | Carbs | Fat |
|------|---------|-----|---------|-------|-----|
| Paneer (grilled) | 100 g | 265 | 18 g | 3 g | 20 g |
| Green chutney | 2 tbsp | 15 | 0.5 g | 2 g | 0.5 g |
| Cucumber slices | 1 cup | 16 | 0.7 g | 3.5 g | 0.1 g |
| Green tea | 1 cup | 2 | 0 g | 0 g | 0 g |

**Meal Total:** 310 kcal · 19 g protein · 9 g carbs · 21 g fat

---

## 🌙 Dinner — Lentil Curry with Chapati (655 kcal)

| Food | Portion | Cal | Protein | Carbs | Fat |
|------|---------|-----|---------|-------|-----|
| Masoor dal (red lentil curry) | 1.5 cups | 290 | 18 g | 42 g | 4 g |
| Whole wheat chapati | 2 medium | 200 | 6 g | 36 g | 3.5 g |
| Palak paneer | 1 cup | 180 | 12 g | 8 g | 11 g |
| Steamed rice (basmati) | ½ cup (100 g) | 130 | 2.7 g | 28 g | 0.3 g |

**Meal Total:** 655 kcal · 33 g protein · 90 g carbs · 19 g fat

---

## 💡 Tips

1. **Hydration** — Aim for 3–4 litres of water daily; add lemon slices for flavour
2. **Meal Prep** — Batch-cook chicken tikka and brown rice on Sunday for the week
3. **Protein Timing** — Consume whey within 30 minutes post-workout for optimal recovery
4. **Fibre** — The brown rice and lentils provide ~18 g of dietary fibre (60% daily target)
"""

_MOCK_WORKOUT = """# Push / Pull / Legs — Hypertrophy Program

> 🧪 **Sandbox Mode** — This program was generated by the local fallback model. For AI-personalised routines, add a valid OpenAI API key.

## Overview

- **Split:** Push / Pull / Legs (6-day rotation)
- **Frequency:** 5–6 days/week
- **Focus:** Muscle Hypertrophy
- **Duration:** 4-week mesocycle
- **Progressive Overload:** +2.5 kg compound / +1–2 reps accessory each week

---

## Day 1 — Push (Chest, Shoulders, Triceps)

### Warm-up
- 5 min incline treadmill walk
- Band pull-aparts: 2 × 15
- Dumbbell lateral raises: 2 × 12 (light)

### Working Sets

| Exercise | Sets × Reps | Rest | Notes |
|----------|-------------|------|-------|
| Barbell Bench Press | 4 × 8–10 | 2 min | Controlled eccentric 3 sec |
| Incline Dumbbell Press | 3 × 10–12 | 90 sec | Full ROM, squeeze at top |
| Cable Flyes (low-to-high) | 3 × 12–15 | 60 sec | Slow negative |
| Overhead Press (barbell) | 4 × 8–10 | 2 min | No leg drive |
| Lateral Raises | 3 × 15–20 | 45 sec | Slight lean forward |
| Tricep Pushdowns | 3 × 12–15 | 60 sec | Rope attachment |
| Overhead Tricep Extension | 3 × 10–12 | 60 sec | Dumbbell, full stretch |

### Cool-down
- Chest doorway stretch: 2 × 30 sec each side
- Tricep overhead stretch: 2 × 30 sec
- Foam roll upper back: 2 min

---

## Day 2 — Pull (Back, Biceps, Rear Delts)

### Warm-up
- 5 min rowing machine (easy pace)
- Cat-cow stretches: 2 × 10
- Band face pulls: 2 × 15

### Working Sets

| Exercise | Sets × Reps | Rest | Notes |
|----------|-------------|------|-------|
| Deadlift (conventional) | 4 × 6–8 | 2.5 min | Belt up at 80%+ |
| Weighted Pull-ups | 4 × 8–10 | 2 min | Add weight when > 10 reps |
| Barbell Bent-Over Row | 3 × 8–10 | 90 sec | Overhand grip |
| Seated Cable Row | 3 × 12–15 | 60 sec | Squeeze scapulae |
| Face Pulls | 3 × 15–20 | 45 sec | External rotation at top |
| Barbell Curl | 3 × 10–12 | 60 sec | No swinging |
| Hammer Curl | 3 × 12 | 45 sec | Alternating arms |

### Cool-down
- Lat stretch (hanging from bar): 2 × 30 sec
- Bicep wall stretch: 2 × 20 sec each arm
- Foam roll lats: 2 min

---

## Day 3 — Legs (Quads, Hamstrings, Glutes, Calves)

### Warm-up
- 5 min bike (moderate)
- Bodyweight squats: 2 × 15
- Leg swings: 2 × 10 each direction

### Working Sets

| Exercise | Sets × Reps | Rest | Notes |
|----------|-------------|------|-------|
| Barbell Back Squat | 4 × 8–10 | 2.5 min | Below parallel |
| Romanian Deadlift | 4 × 10–12 | 2 min | Hamstring stretch at bottom |
| Bulgarian Split Squat | 3 × 10–12/leg | 90 sec | Hold dumbbells |
| Leg Press | 3 × 12–15 | 90 sec | Feet high and wide for glutes |
| Leg Curl (lying) | 3 × 12–15 | 60 sec | Slow eccentric |
| Standing Calf Raise | 4 × 15–20 | 45 sec | Full stretch at bottom |
| Seated Calf Raise | 3 × 15–20 | 45 sec | Pause at top |

### Cool-down
- Quad stretch: 2 × 30 sec each
- Hamstring door stretch: 2 × 30 sec each
- Pigeon pose: 2 × 30 sec each side
- Foam roll quads/hamstrings: 3 min

---

## 📈 Weekly Progression Notes

- **Week 1 (Introduction):** Use RPE 7–8 weights. Focus on form and mind-muscle connection. Record baseline numbers.
- **Week 2 (Volume Increase):** Add 1 extra set to compound lifts OR add 2 reps to each working set. Maintain same weight.
- **Week 3 (Intensity Increase):** Increase weight by 2.5 kg on compounds (squat, bench, deadlift, OHP) and 1–2.5 kg on accessories. Keep reps the same.
- **Week 4 (Deload):** Reduce weight to 60% of week 3. Reduce volume by ~40%. Focus on recovery and mobility. Prepare for next mesocycle.

---

## 🥗 Nutrition Reminder

- **Protein:** Aim for 1.6–2.2 g per kg of body weight daily
- **Hydration:** 3+ litres of water per day
- **Sleep:** 7–9 hours for optimal recovery
"""
