# app/llm.py
from groq import Groq
from .config import GROQ_API_KEY, GROQ_MODEL

_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def _build_messages(messages: list[dict]) -> list[dict]:
    return [{"role": m["role"], "content": m["content"]} for m in messages]


def chat(messages: list[dict]) -> tuple[str, dict]:
    """
    Send a chat completion request to Groq.
    messages: List of {"role": "system"|"user"|"assistant", "content": "..."}
    Returns: (response_text, usage_dict)
    """
    if _client is None:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    response = _client.chat.completions.create(
        model=GROQ_MODEL,
        messages=_build_messages(messages),
    )

    choice = response.choices[0]
    text = choice.message.content

    usage_info = getattr(response, "usage", None)
    usage = {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}
    if usage_info is not None:
        usage.update(
            prompt_tokens=getattr(usage_info, "prompt_tokens", None),
            completion_tokens=getattr(usage_info, "completion_tokens", None),
            total_tokens=getattr(usage_info, "total_tokens", None),
        )

    return text, usage
