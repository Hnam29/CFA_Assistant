"""
core/chatbot_engine.py — CFA AI Tutor chatbot with structured system prompt.
"""

from typing import List, Dict
from core.ai_client import call_ai

SYSTEM_PROMPT = """You are an expert CFA (Chartered Financial Analyst) Level I tutor and coach.
You have deep expertise in all 10 CFA Level I topic areas:
- Ethics & Professional Standards
- Quantitative Methods
- Economics
- Financial Statement Analysis
- Corporate Issuers
- Equity Investments
- Fixed Income
- Derivatives
- Alternative Investments
- Portfolio Management

Your role is to:
1. Explain CFA concepts clearly, with appropriate depth for Level I candidates
2. Provide worked examples when helpful (use realistic numbers)
3. Highlight common misconceptions and exam traps
4. Explain why certain answers are correct/incorrect on practice questions
5. Relate concepts to real-world applications where appropriate

Guidelines:
- Use markdown formatting (bold, bullet points, tables) to structure responses
- For mathematical concepts, show step-by-step calculations
- Reference specific LOS (Learning Outcome Statements) when relevant
- Keep explanations concise but complete
- If a question is outside CFA scope, politely redirect to CFA-relevant content
- Never make up facts or invent CFA standards — be accurate
"""


def chat_with_tutor(
    messages: List[Dict[str, str]],
    user_message: str,
    context: str = "",
    user_context: str = "",
) -> str:
    """
    Send a user message to the AI tutor and get a response.

    messages: prior conversation history [{"role": ..., "content": ...}]
    user_message: the new user query
    context: optional context (e.g., question they just answered) to inject
    user_context: personalisation data (profile, scores) to make the AI aware of the student
    """
    system = SYSTEM_PROMPT
    if user_context:
        system += f"\n\n## Student Profile\n{user_context}"
    if context:
        system += f"\n\n## Current Context\n{context}"

    # Build messages list
    history = list(messages)
    history.append({"role": "user", "content": user_message})

    response = call_ai(
        messages=history,
        system=system,
        max_tokens=2048,
        temperature=0.65,
    )
    return response


def get_quick_explanation(topic: str, concept: str) -> str:
    """Get a brief explanation of a specific concept."""
    prompt = f"""Briefly explain '{concept}' in the context of {topic} for CFA Level I.
Cover: definition, key formula (if applicable), and one exam-relevant note.
Keep it under 200 words."""

    return call_ai(
        messages=[{"role": "user", "content": prompt}],
        system=SYSTEM_PROMPT,
        max_tokens=512,
        temperature=0.5,
    )
