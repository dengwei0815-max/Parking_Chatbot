import guard_rails
from guard_rails import filter_sensitive, filter_input, filter_output


def _mock_ner_with_name(name, start, end):
    """Return a mock NER function that detects a single PER entity."""
    def _ner(text):
        if name in text:
            return [{"entity_group": "PER", "score": 0.99, "word": name,
                     "start": start, "end": end}]
        return []
    return _ner


def test_sensitive_detection_redacts(monkeypatch):
    """filter_sensitive should redact detected names, not block the whole message."""
    monkeypatch.setattr(guard_rails, "_ner", _mock_ner_with_name("John", 11, 15))
    text = "My name is John Doe"
    filtered = filter_sensitive(text)
    assert "John" not in filtered
    assert "[REDACTED]" in filtered


def test_non_sensitive_passes_through(monkeypatch):
    """Text with no person names should be returned unchanged."""
    monkeypatch.setattr(guard_rails, "_ner", lambda text: [])
    text = "What are the working hours?"
    assert filter_sensitive(text) == text


def test_filter_output_redacts_llm_response(monkeypatch):
    """filter_output should redact names from LLM-generated responses."""
    monkeypatch.setattr(guard_rails, "_ner", _mock_ner_with_name("Alice", 27, 32))
    text = "The reservation was made by Alice last Tuesday."
    result = filter_output(text)
    assert "Alice" not in result
    assert "[REDACTED]" in result


def test_filter_input_alias(monkeypatch):
    """filter_input and filter_sensitive should behave identically."""
    monkeypatch.setattr(guard_rails, "_ner", _mock_ner_with_name("Bob", 0, 3))
    text = "Bob wants a parking space."
    assert filter_input(text) == filter_sensitive(text)
