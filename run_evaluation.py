"""
Run evaluation against the live RAG chain.

Usage:
    python run_evaluation.py

Requires a running Milvus instance and valid Azure OpenAI credentials in env.
Results are printed to stdout and written to evaluation_report.txt.
"""

from evaluation import evaluate_latency, evaluate_accuracy
from rag import build_rag_chain

QUESTIONS = [
    "What are the parking hours?",
    "What is the daily parking rate?",
    "Can I reserve a parking space in advance?",
    "Where is the parking lot located?",
    "Is there monthly parking available?",
]

EXPECTED_ANSWERS = [
    "The parking lot is open 24 hours a day, 7 days a week.",
    "The daily parking rate is $10 per day.",
    "Yes, you can reserve a parking space in advance through the chatbot.",
    "The parking lot is located at the city center.",
    "Yes, monthly parking passes are available.",
]


if __name__ == "__main__":
    print("Building RAG chain...")
    chain = build_rag_chain()

    print("\n=== Latency Evaluation ===")
    avg_latency = evaluate_latency(chain, QUESTIONS)

    print("\n=== Accuracy Evaluation (Semantic Similarity) ===")
    avg_similarity = evaluate_accuracy(chain, QUESTIONS, EXPECTED_ANSWERS)

    report = (
        f"Evaluation Report\n"
        f"=================\n"
        f"Questions evaluated : {len(QUESTIONS)}\n"
        f"Average latency     : {avg_latency:.2f}s\n"
        f"Average similarity  : {avg_similarity:.3f}\n"
    )
    print("\n" + report)
    with open("evaluation_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    print("Report written to evaluation_report.txt")
