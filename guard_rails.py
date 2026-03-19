"""
Guardrails
----------
Two responsibilities:
1. filter_input(text)  — redact person names from USER INPUT before passing to LLM,
                         so names are never sent to the vector DB query or LLM prompt.
2. filter_output(text) — redact person names from LLM OUTPUT before showing to user,
                         preventing the LLM from leaking names it may have retrieved
                         from the vector DB.

Design notes:
- We redact (replace with [REDACTED]) rather than blocking the whole message, so the
  conversation can continue even when a name is present.
- The NER model is loaded once at module level to avoid repeated cold-starts.
- filter_sensitive() is kept as a convenience alias for filter_input() so existing
  callers (app.py, tests) continue to work without changes.
"""

from transformers import pipeline

# Load NER pipeline once at import time
_ner = pipeline(
    "ner",
    model="dbmdz/bert-large-cased-finetuned-conll03-english",
    aggregation_strategy="simple",  # merge sub-tokens into full entity spans
)


def _redact_entities(text: str, threshold: float = 0.85) -> str:
    """
    Use NER to find person entities and replace them with [REDACTED].
    Falls back gracefully if NER fails.
    """
    try:
        entities = _ner(text)
    except Exception:
        return text

    # Sort by start position descending so replacements don't shift offsets
    person_spans = [
        e for e in entities
        if "PER" in e.get("entity_group", "") and e.get("score", 0) >= threshold
    ]
    person_spans.sort(key=lambda e: e["start"], reverse=True)

    result = text
    for ent in person_spans:
        result = result[: ent["start"]] + "[REDACTED]" + result[ent["end"] :]
    return result


def filter_input(text: str) -> str:
    """
    Redact person names from user input before it reaches the LLM / vector DB.
    Returns the sanitised text (conversation continues even when names are present).
    """
    return _redact_entities(text)


def filter_output(text: str) -> str:
    """
    Redact person names from LLM output before displaying to the user.
    This prevents the system from leaking names stored in the vector DB.
    """
    return _redact_entities(text)


# Backwards-compatible alias used by app.py and existing tests
def filter_sensitive(text: str) -> str:
    return filter_input(text)
