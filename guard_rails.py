from transformers import pipeline

# Use a pre-trained NER model to detect sensitive info
ner = pipeline("ner", grouped_entities=True)

def filter_sensitive(text):
    entities = ner(text)
    for ent in entities:
        if ent['entity_group'] in ['PERSON', 'ORG', 'LOC']:
            return "[Sensitive data detected. Please rephrase your request.]"
    return text