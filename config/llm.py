import time

from openai import OpenAI
from config.settings import settings

client = OpenAI(
    base_url=settings.OPENROUTER_BASE_URL,
    api_key=settings.OPENROUTER_API_KEY,
)


def chat(state, **kwargs):
    """Tüm LLM çağrıları buradan geçer: çağır, ölç, state'e yaz."""
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=settings.MODEL_NAME,
        extra_body={"usage": {"include": True}},
        **kwargs,
    )
    state.llm_seconds += time.perf_counter() - start

    usage = response.usage
    state.llm_calls += 1
    state.prompt_tokens += usage.prompt_tokens
    state.completion_tokens += usage.completion_tokens
    state.cost_usd += getattr(usage, "cost", None) or 0.0  # başka sağlayıcıda alan yoksa 0
    return response
