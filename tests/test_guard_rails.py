from guard_rails import filter_sensitive

def test_sensitive_detection():
    text = "My name is John Doe"
    filtered = filter_sensitive(text)
    assert filtered.startswith("[Sensitive")

def test_non_sensitive():
    text = "What are the working hours?"
    filtered = filter_sensitive(text)
    assert filtered == text