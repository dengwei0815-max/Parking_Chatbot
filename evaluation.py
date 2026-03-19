"""
Evaluation module
-----------------
Provides two evaluation functions for the RAG chatbot:

evaluate_latency  — measures average response time per query
evaluate_accuracy — measures semantic similarity between predicted and expected
                    answers using sentence-transformers cosine similarity.
                    (Exact-string matching would never work for LLM outputs.)
"""

import time
from sentence_transformers import SentenceTransformer, util

_embed_model = None


def _get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed_model


def evaluate_latency(chain, questions: list) -> float:
    """
    Measure average response latency of the RAG chain.

    Args:
        chain: A RAG chain with an .invoke({"query": ...}) interface.
        questions: List of question strings.

    Returns:
        Average latency in seconds.
    """
    latencies = []
    for q in questions:
        start = time.time()
        chain.invoke({"query": q})
        latencies.append(time.time() - start)
    avg = sum(latencies) / len(latencies) if latencies else 0.0
    print(f"Average Latency: {avg:.2f}s  (over {len(questions)} questions)")
    return avg


def evaluate_accuracy(chain, questions: list, expected_answers: list) -> float:
    """
    Evaluate semantic similarity between chain responses and expected answers.

    Uses cosine similarity of sentence embeddings; scores range 0-1.
    A score ≥ 0.7 is generally considered a good match.

    Args:
        chain: A RAG chain with an .invoke({"query": ...}) interface.
        questions: List of question strings.
        expected_answers: List of reference answer strings (same length).

    Returns:
        Average cosine similarity score.
    """
    model = _get_embed_model()
    predictions = [chain.invoke({"query": q})["result"] for q in questions]
    scores = []
    for pred, gt in zip(predictions, expected_answers):
        sim = util.pytorch_cos_sim(
            model.encode(pred, convert_to_tensor=True),
            model.encode(gt,   convert_to_tensor=True),
        ).item()
        scores.append(sim)
        print(f"  Q: {gt!r:.60s}  sim={sim:.3f}")
    avg = sum(scores) / len(scores) if scores else 0.0
    print(f"Average Semantic Similarity: {avg:.3f}")
    return avg
