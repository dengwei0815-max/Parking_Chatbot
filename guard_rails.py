from transformers import pipeline

# Initialize the NER pipeline with a reliable model
ner = pipeline(
    "ner",
    model="dbmdz/bert-large-cased-finetuned-conll03-english"
)

def filter_sensitive(text):
    """
    Detect and filter sensitive information (e.g., person names) from user input.
    Only blocks high-confidence person entities to reduce false positives.
    :param text: User input string
    :return: Warning string if sensitive data detected, else original text
    """
    entities = ner(text)
    for ent in entities:
        label = ent.get('entity', '')
        score = float(ent.get('score', 0))
        word = ent.get('word', '')
        # Only block high-confidence person entities (PER, PERSON)
        if score > 0.95 and any(x in label for x in ['PER', 'PERSON']):
            # Optionally, only block if the word is capitalized (to reduce false positives)
            if word.istitle():
                return "[Sensitive data detected. Please rephrase your request.]"
    return text