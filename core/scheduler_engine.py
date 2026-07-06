"""
core/scheduler_engine.py — AI-powered learning schedule generator using spaced repetition.
"""

import json
import re
from datetime import date, timedelta
from typing import List, Dict, Optional

from core.ai_client import call_ai

SYSTEM_PROMPT = """You are an expert learning coach specializing in CFA exam preparation.
You use evidence-based study techniques including:
- Spaced Repetition (Ebbinghaus forgetting curve)
- Active Recall
- Interleaved practice
- Spaced testing effect

You analyze a candidate's performance data and create personalized, realistic study schedules
that maximize retention and exam readiness.

Output ONLY valid JSON, no extra text.
"""


def _parse_schedule(raw: str) -> List[Dict]:
    """Extract JSON array from AI response with robust sanitization.
    Handles truncated responses (free-tier token limits) by recovering
    complete JSON objects individually.
    """
    cleaned = raw.strip()

    # Strip markdown code fences if present
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    # 1. Try to parse the entire string as-is
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for val in data.values():
                if isinstance(val, list):
                    return val
    except Exception:
        pass

    # 2. Try regex to find the first complete [ ... ] array
    array_match = re.search(r"\[[\s\S]*\]", cleaned)
    if array_match:
        try:
            data = json.loads(array_match.group())
            if isinstance(data, list):
                return data
        except Exception:
            pass

    # 3. Partial recovery: extract individual complete { ... } objects
    #    This handles cases where the LLM response was truncated mid-array.
    objects = []
    for m in re.finditer(r"\{[^{}]*\}", cleaned, re.DOTALL):
        try:
            obj = json.loads(m.group())
            if isinstance(obj, dict) and "date" in obj and "topic" in obj:
                objects.append(obj)
        except Exception:
            continue
    if objects:
        return objects

    # 4. Try dict wrapper
    dict_match = re.search(r"\{[\s\S]*\}", cleaned)
    if dict_match:
        try:
            data = json.loads(dict_match.group())
            if isinstance(data, dict):
                for val in data.values():
                    if isinstance(val, list):
                        return val
        except Exception:
            pass

    snippet = cleaned[:300] + "..." if len(cleaned) > 300 else cleaned
    raise ValueError(
        f"Could not parse scheduler response as JSON.\n"
        f"Raw snippet: {repr(snippet)}"
    )


def generate_schedule(
    topic_performance: List[Dict],
    completed_sessions: List[Dict],
    free_slots: Optional[List[str]] = None,
    days_ahead: int = 14,
    exam_date: Optional[str] = None,
) -> List[Dict]:
    """
    Generate a 2-week personalized study schedule.
    
    topic_performance: [{topic, avg_score, sessions_done, last_studied}]
    completed_sessions: recent session history
    free_slots: e.g. ["Monday evenings", "Saturday mornings"]
    """
    today = date.today().isoformat()

    # Prepare performance summary
    perf_summary = []
    for p in topic_performance:
        last = p.get("last_studied") or "never"
        avg_score = p.get("avg_score")
        avg_score_val = avg_score if avg_score is not None else 0.0
        perf_summary.append(
            f"- {p['topic']}: avg score {avg_score_val:.0f}%, "
            f"{p['sessions_done']} sessions, last studied: {last}"
        )

    recent_sessions = []
    for s in completed_sessions[:10]:
        score_val = s.get("score")
        score_num = score_val if score_val is not None else 0.0
        _raw_dt = s.get('started_at', '?')
        _dt_str = _raw_dt.isoformat()[:10] if hasattr(_raw_dt, 'isoformat') else str(_raw_dt)[:10]
        recent_sessions.append(
            f"- {_dt_str}: {s['topic']} {s['session_type']} → {score_num:.0f}%"
        )

    slots_str = ", ".join(free_slots) if free_slots else "flexible (no specific constraints)"
    exam_str = f"Exam date: {exam_date}" if exam_date else "Exam date: not specified"

    prompt = f"""Create a {days_ahead}-day personalized CFA Level I study schedule starting from {today}.

CANDIDATE PERFORMANCE DATA:
{chr(10).join(perf_summary) if perf_summary else 'No data yet — beginner.'}

RECENT STUDY HISTORY:
{chr(10).join(recent_sessions) if recent_sessions else 'No recent sessions.'}

AVAILABILITY: {slots_str}
{exam_str}

INSTRUCTIONS:
1. Prioritize topics with low scores or not studied recently
2. Apply spaced repetition — schedule reviews ~10 days after last low-score session
3. Mix session types: Practice, Mock Exam, Review
4. Include a reason for each scheduled session
5. Don't over-schedule — max 1-2 sessions per day
6. Assign priority: 'high' for weak topics, 'medium' for maintenance, 'low' for review

Return ONLY a compact JSON array of at most 10 items (no extra text, no markdown):
[{{"date":"YYYY-MM-DD","topic":"...","session_type":"Practice|Mock Exam|Review","priority":"high|medium|low","reason":"short reason"}}, ...]
"""

    response = call_ai(
        messages=[{"role": "user", "content": prompt}],
        system=SYSTEM_PROMPT,
        max_tokens=1500,
        temperature=0.4,
    )
    return _parse_schedule(response)


def generate_rule_based_schedule(
    topic_performance: List[Dict],
    completed_sessions: List[Dict],
    days_ahead: int = 14,
    exam_date: Optional[str] = None,
    subject_filter: Optional[str] = None,
    free_slots: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Generate a study schedule using a rule-based spaced repetition algorithm.
    """
    from utils.cfa_topics import TOPIC_NAMES
    from database.db import get_curriculum_weights
    from datetime import datetime

    db_weights = get_curriculum_weights()
    today = date.today()
    
    # 1. Setup performance map and last studied date map
    perf_map = {}
    last_studied_map = {}
    
    for p in topic_performance:
        topic = p["topic"]
        perf_map[topic] = p["avg_score"]
        if p.get("last_studied"):
            try:
                # SQLite timestamp can be "YYYY-MM-DD HH:MM:SS" or "YYYY-MM-DD"
                dt_str = p["last_studied"][:10]
                last_studied_map[topic] = datetime.strptime(dt_str, "%Y-%m-%d").date()
            except Exception:
                pass

    # Also extract last studied from recent completed sessions for extra accuracy
    for s in completed_sessions:
        topic = s["topic"]
        if s.get("started_at") and topic not in last_studied_map:
            try:
                _raw = s["started_at"]
                dt_str = _raw.isoformat()[:10] if hasattr(_raw, "isoformat") else str(_raw)[:10]
                last_studied_map[topic] = datetime.strptime(dt_str, "%Y-%m-%d").date()
            except Exception:
                pass

    # 2. Determine study phase (days to exam)
    study_phase = "core"
    if exam_date:
        try:
            ex_date = datetime.strptime(exam_date, "%Y-%m-%d").date()
            days_to_exam = (ex_date - today).days
            if days_to_exam < 15:
                study_phase = "mock"
            elif days_to_exam <= 45:
                study_phase = "interleaved"
        except Exception:
            pass

    # Define deterministic session type cycles
    cycles = {
        "core": ["Practice", "Practice", "Review", "Practice", "Review"],
        "interleaved": ["Practice", "Review", "Practice", "Review", "Mock Exam"],
        "mock": ["Mock Exam", "Review", "Practice", "Review", "Practice"]
    }
    type_cycle = cycles[study_phase]
    session_count = 0

    scheduled_sessions = []

    # Choose topics to schedule
    target_topics = [subject_filter] if subject_filter and subject_filter in TOPIC_NAMES else TOPIC_NAMES

    # Loop through each day
    for day_idx in range(1, days_ahead + 1):
        target_day = today + timedelta(days=day_idx)
        weekday_name = target_day.strftime("%A") # Monday, Tuesday, etc.
        
        # Check availability if free_slots is provided
        if free_slots:
            is_weekend = weekday_name in ["Saturday", "Sunday"]
            available = False
            
            # Map weekday / weekend to free slots
            if not is_weekend:
                if any(slot in free_slots for slot in ["Weekday mornings", "Weekday lunch", "Weekday evenings"]):
                    available = True
            else:
                if "Weekends" in free_slots:
                    available = True
                elif weekday_name == "Saturday" and any(slot in free_slots for slot in ["Saturday mornings", "Saturday afternoons"]):
                    available = True
                elif weekday_name == "Sunday" and any(slot in free_slots for slot in ["Sunday mornings", "Sunday afternoons"]):
                    available = True
            
            if not available:
                continue

        # Calculate priority scores for target topics on this day
        scores = {}
        for topic in target_topics:
            weight = db_weights.get(topic, 10)
            score_val = perf_map.get(topic)
            last_date = last_studied_map.get(topic)
            
            # Performance factor
            if score_val is None:
                perf_factor = 2.0  # Never studied = high priority
            elif score_val < 60:
                perf_factor = 2.0
            elif score_val < 75:
                perf_factor = 1.0
            else:
                perf_factor = 0.5
                
            # Recency factor
            if last_date is None:
                recency_factor = 3.0
            else:
                days_since = (target_day - last_date).days
                if days_since < 3:
                    recency_factor = 0.2  # Avoid scheduling the same topic back-to-back
                elif days_since <= 7:
                    recency_factor = 1.0
                else:
                    recency_factor = 1.5 + (days_since - 7) * 0.1
            
            scores[topic] = weight * perf_factor * recency_factor

        if not scores:
            continue
            
        # Select the topic with the highest score
        chosen_topic = max(scores, key=scores.get)
        
        # Determine session type
        sess_type = type_cycle[session_count % len(type_cycle)]
        session_count += 1
        
        # Override Mock Exam if score is too low (< 50%) or never studied
        topic_score = perf_map.get(chosen_topic)
        if sess_type == "Mock Exam" and (topic_score is None or topic_score < 50):
            sess_type = "Practice"

        # Determine priority
        if topic_score is None:
            priority = "high"
        elif topic_score < 60:
            priority = "high"
        elif topic_score < 75:
            priority = "medium"
        else:
            priority = "low"

        # Construct reasoning
        weight = db_weights.get(chosen_topic, 10)
        last_date = last_studied_map.get(chosen_topic)
        
        if topic_score is None:
            reason = f"Introductory {sess_type.lower()} session. Topic curriculum weight: {weight}%."
        elif topic_score < 60:
            reason = f"Priority topic (avg score: {topic_score:.0f}%). Intensive practice to boost performance."
        elif last_date and (target_day - last_date).days > 7:
            days_since = (target_day - last_date).days
            reason = f"Spaced repetition recall session. Last studied {days_since} days ago."
        else:
            reason = f"Routine maintenance of key topic (avg score: {topic_score:.0f}%)."

        scheduled_sessions.append({
            "date": target_day.isoformat(),
            "topic": chosen_topic,
            "session_type": sess_type,
            "priority": priority,
            "reason": reason
        })
        
        # Update last studied map so spaced repetition registers it
        last_studied_map[chosen_topic] = target_day

    return scheduled_sessions


def get_study_insights(topic_performance: List[Dict], sessions: List[Dict]) -> str:
    """
    Ask AI to provide qualitative insights about the learner's progress and behavior.
    Returns a markdown-formatted insight string.
    """
    if not topic_performance and not sessions:
        return "Complete your first practice session to get personalized insights!"

    perf_str = json.dumps(topic_performance, indent=2, default=str)
    sessions_str = json.dumps(sessions[:15], indent=2, default=str)

    prompt = f"""Based on this CFA candidate's learning data, provide 3-5 concise, actionable insights.

Performance data:
{perf_str}

Recent sessions:
{sessions_str}

Format your response as markdown bullet points. Be specific, encouraging, and practical.
Focus on: what's going well, what needs attention, and one key study tip.
"""
    return call_ai(
        messages=[{"role": "user", "content": prompt}],
        system=SYSTEM_PROMPT,
        max_tokens=600,
        temperature=0.6,
    )
