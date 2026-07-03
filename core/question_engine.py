"""
core/question_engine.py — AI-powered question generation for CFA practice.
"""

import json
import re
from typing import List, Dict, Optional

from core.ai_client import call_ai


SYSTEM_PROMPT = """You are a senior CFA exam question writer with 15 years of experience.
You write rigorous, exam-quality multiple-choice questions for the CFA Level I examination.

Rules:
- Each question must have exactly 3 options: A, B, C (CFA format)
- Distractors should target real misconceptions candidates commonly make
- Explanations must be thorough, referencing the relevant concept
- Questions should be realistic and of appropriate complexity
- CRITICAL: Every generated question must be completely original, distinct, and unique from each other and from any reference examples. Do NOT repeat or duplicate any question scenarios or text.
- Output ONLY valid JSON, no extra text
"""


def _parse_questions(raw: str) -> List[Dict]:
    """Extract and parse JSON from AI response."""
    # Try to find JSON array in response
    match = re.search(r"\[[\s\S]*\]", raw)
    if not match:
        # Try single object
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            return [json.loads(match.group())]
        raise ValueError("No JSON found in AI response")
    return json.loads(match.group())


def generate_questions(
    topic: str,
    subtopics: Optional[List[str]] = None,
    difficulty: str = "Medium",
    count: int = 5,
    use_bank_only: bool = False,
) -> List[Dict]:
    """
    Generate CFA practice questions. If use_bank_only=True or the AI call fails,
    falls back to retrieving hand-crafted questions from the local database.
    """
    from database.db import get_bank_questions

    # 1. Handle forced offline / local bank-only mode
    if use_bank_only:
        return _fetch_fallback_questions(topic, subtopics, difficulty, count)

    # 2. Few-shot context generation from bank questions
    few_shot_context = ""
    try:
        # Retrieve up to 2 real questions on this topic from the bank to act as style guides
        bank_qs = get_bank_questions(topic, subtopics, limit=2)
        if bank_qs:
            few_shot_context = "\nUse the following real exam-style questions ONLY as reference examples for question style, length, distractors, and complexity. Do NOT repeat these reference questions. Generate brand-new, distinct questions on the target topic/subtopics:\n\n"
            for idx, bq in enumerate(bank_qs):
                few_shot_context += f"""Example {idx+1}:
- Question: {bq['question_text']}
- Option A: {bq['option_a']}
- Option B: {bq['option_b']}
- Option C: {bq['option_c']}
- Correct Answer: {bq['correct_answer']}
- Explanation: {bq['explanation']}
- Subtopic: {bq['subtopic']}
---
"""
    except Exception:
        # If DB query fails for few-shot, we just proceed without examples
        pass

    subtopic_str = ", ".join(subtopics) if subtopics else "any subtopic"
    prompt = f"""Generate {count} unique, completely distinct CFA Level I multiple-choice questions on the topic:
Topic: {topic}
Subtopics to cover: {subtopic_str}
Difficulty: {difficulty}
{few_shot_context}
Important: Each of the {count} questions must be different from one another. Do not repeat the same question.

Return a JSON array where each item has:
{{
  "question": "...",
  "option_a": "...",
  "option_b": "...",
  "option_c": "...",
  "correct_answer": "A" | "B" | "C",
  "explanation": "...",
  "subtopic": "..."
}}
"""
    try:
        response = call_ai(
            messages=[{"role": "user", "content": prompt}],
            system=SYSTEM_PROMPT,
            max_tokens=4000,
            temperature=0.8,
        )
        questions = _parse_questions(response)

        # Validate, normalize, and deduplicate fields
        cleaned = []
        seen_texts = set()
        for q in questions:
            try:
                q_text = q["question"].strip()
                if q_text.lower() in seen_texts:
                    continue
                seen_texts.add(q_text.lower())
                cleaned.append({
                    "question": q_text,
                    "option_a": q["option_a"],
                    "option_b": q["option_b"],
                    "option_c": q["option_c"],
                    "correct_answer": q["correct_answer"].upper().strip(),
                    "explanation": q["explanation"],
                    "subtopic": q.get("subtopic", ""),
                    "topic": topic,
                    "difficulty": difficulty,
                })
            except KeyError:
                continue  # skip malformed questions
        
        # If AI returned less or empty questions, trigger fallback
        if not cleaned:
            raise ValueError("Empty or malformed JSON returned by AI")
            
        return cleaned

    except Exception as e:
        # Fallback to local question bank on systematic AI failures
        import logging
        logging.warning(f"AI question generation failed: {e}. Falling back to local database question bank.")
        fallback_qs = _fetch_fallback_questions(topic, subtopics, difficulty, count)
        if not fallback_qs:
            # Re-raise original error if we have no fallback questions either
            raise RuntimeError(f"AI generation failed ({e}) and no offline fallback questions are available in the question bank for {topic}.")
        return fallback_qs


def _fetch_fallback_questions(topic: str, subtopics: Optional[List[str]], difficulty: str, count: int) -> List[Dict]:
    """Retrieve fallback questions from local bank and format them like AI-generated dicts."""
    from database.db import get_bank_questions
    
    all_rows = []
    seen_ids = set()

    def add_rows(rows):
        for r in rows:
            if r["id"] not in seen_ids:
                seen_ids.add(r["id"])
                all_rows.append(r)

    # Attempt 1: Specific topic, subtopics, and difficulty
    add_rows(get_bank_questions(topic, subtopics, difficulty, limit=count))
    
    # Attempt 2: If not enough, try without difficulty constraint
    if len(all_rows) < count:
        add_rows(get_bank_questions(topic, subtopics, limit=count))
        
    # Attempt 3: If still not enough, try topic only
    if len(all_rows) < count:
        add_rows(get_bank_questions(topic, limit=count))

    return [
        {
            "question": q["question_text"],
            "option_a": q["option_a"],
            "option_b": q["option_b"],
            "option_c": q["option_c"],
            "correct_answer": q["correct_answer"].upper().strip(),
            "explanation": q["explanation"],
            "subtopic": q["subtopic"] or "",
            "topic": q["topic"],
            "difficulty": q["difficulty"] or difficulty,
        }
        for q in all_rows[:count]
    ]


def generate_mock_exam(
    topic_weights: Dict[str, float],
    total_questions: int = 30,
    difficulty_mix: Dict[str, float] = None,
) -> List[Dict]:
    """
    Generate a mixed mock exam weighted by topic.
    topic_weights: {topic_name: weight_fraction}  (should sum to ~1)
    difficulty_mix: {difficulty: fraction} e.g. {"Easy": 0.2, "Medium": 0.5, "Hard": 0.3}
    """
    if difficulty_mix is None:
        difficulty_mix = {"Easy": 0.2, "Medium": 0.5, "Hard": 0.3}

    all_questions = []
    for topic, weight in topic_weights.items():
        n = max(1, round(total_questions * weight))
        # Mix difficulties
        for diff, dfrac in difficulty_mix.items():
            dcount = max(1, round(n * dfrac))
            try:
                qs = generate_questions(topic=topic, difficulty=diff, count=dcount)
                all_questions.extend(qs)
            except Exception:
                continue
        if len(all_questions) >= total_questions:
            break

    return all_questions[:total_questions]
