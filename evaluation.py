import time
from sklearn.metrics import precision_score, recall_score

def evaluate_latency(chain, questions):
    latencies = []
    for q in questions:
        start = time.time()
        chain.run(q)
        latencies.append(time.time() - start)
    avg_latency = sum(latencies) / len(latencies)
    print(f"Average Latency: {avg_latency:.2f}s")

def evaluate_accuracy(chain, questions, expected_answers):
    predictions = [chain.run(q) for q in questions]
    # For demo, treat exact match as correct
    precision = precision_score(expected_answers, predictions, average='micro')
    recall = recall_score(expected_answers, predictions, average='micro')
    print(f"Precision: {precision:.2f}, Recall: {recall:.2f}")