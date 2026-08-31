# meter.py — token / cost / latency instrumentation. Reusable in any LLM project.
import time

import tiktoken

# Prices drift. Check your provider's pricing page before trusting the dollars.
# USD per 1K tokens.
PRICE_PER_1K = {
    "gpt-5.6-luna": {"input": 0.0002, "output": 0.0012},
}


def count_tokens(text: str, model: str = "gpt-5.6-luna") -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("o200k_base")  # fallback for new models
    return len(enc.encode(text))


def estimate_cost(tin: int, tout: int, model: str = "gpt-5.6-luna") -> float:
    p = PRICE_PER_1K[model]
    return (tin / 1000) * p["input"] + (tout / 1000) * p["output"]


def timed(fn, *args, **kwargs):
    """Run fn, return (result, elapsed_ms)."""
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    return result, (time.perf_counter() - start) * 1000


def report(prompt_text: str, reply: str, ms: float, model: str = "gpt-5.6-luna") -> None:
    tin, tout = count_tokens(prompt_text, model), count_tokens(reply, model)
    if model in PRICE_PER_1K:
        cost = f"cost=${estimate_cost(tin, tout, model):.5f}  "
    else:
        cost = ""  # model not in the price table — report tokens, skip the dollars
    print(f"[meter] in={tin} tok  out={tout} tok  {cost}latency={ms:.0f}ms")
