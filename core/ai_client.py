"""
core/ai_client.py — Unified wrapper for Claude, OpenAI GPT-4o, Gemini, Groq, and Hugging Face.
Set AI_PROVIDER in .env to switch providers.
"""

import os
from typing import List, Dict, Optional

# Read provider dynamically to support env changes on the fly
def get_provider() -> str:
    return os.getenv("AI_PROVIDER", "claude").lower()


def _call_claude(messages: List[Dict], system: str, max_tokens: int = 4096, temperature: float = 0.7) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest")
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=messages,
    )
    return response.content[0].text


def _call_openai(messages: List[Dict], system: str, max_tokens: int = 4096, temperature: float = 0.7) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    full_messages = [{"role": "system", "content": system}] + messages
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    response = client.chat.completions.create(
        model=model,
        messages=full_messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content


def _call_gemini(messages: List[Dict], system: str, max_tokens: int = 4096, temperature: float = 0.7) -> str:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model_name = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        ),
    )
    # Convert to Gemini format
    history = []
    for m in messages[:-1]:
        role = "model" if m["role"] == "assistant" else "user"
        history.append({"role": role, "parts": [m["content"]]})
    chat = model.start_chat(history=history)
    response = chat.send_message(messages[-1]["content"])
    return response.text


def _call_groq(messages: List[Dict], system: str, max_tokens: int = 4096, temperature: float = 0.7) -> str:
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    full_messages = [{"role": "system", "content": system}] + messages
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    response = client.chat.completions.create(
        model=model,
        messages=full_messages,
        max_tokens=max_tokens if max_tokens <= 8192 else 8192,
        temperature=temperature,
    )
    return response.choices[0].message.content


def _call_huggingface(messages: List[Dict], system: str, max_tokens: int = 4096, temperature: float = 0.7) -> str:
    from openai import OpenAI
    client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=os.getenv("HF_TOKEN"),
    )
    full_messages = [{"role": "system", "content": system}] + messages
    model = os.getenv("HF_MODEL", "meta-llama/Llama-3.3-70B-Instruct")
    response = client.chat.completions.create(
        model=model,
        messages=full_messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content


def call_ai(
    messages: List[Dict[str, str]],
    system: str,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    provider: Optional[str] = None,
) -> str:
    """
    Unified AI call. 
    messages: list of {"role": "user"|"assistant", "content": str}
    system:   system prompt string
    provider: override env setting with 'claude'|'openai'|'gemini'|'groq'|'huggingface'
    """
    p = (provider or get_provider()).lower()
    if p == "claude":
        return _call_claude(messages, system, max_tokens, temperature)
    elif p in ("openai", "gpt"):
        return _call_openai(messages, system, max_tokens, temperature)
    elif p == "gemini":
        return _call_gemini(messages, system, max_tokens, temperature)
    elif p == "groq":
        return _call_groq(messages, system, max_tokens, temperature)
    elif p in ("huggingface", "hf"):
        return _call_huggingface(messages, system, max_tokens, temperature)
    else:
        raise ValueError(
            f"Unknown AI provider: {p}. Set AI_PROVIDER to 'claude', 'openai', 'gemini', 'groq', or 'huggingface'."
        )

