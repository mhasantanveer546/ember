"""
Ember Search Engine — Precision / Recall Benchmark (Phase 1.9)

Precision and recall need ground truth: a human judgment of which
documents are actually relevant to a query. Real corpora don't come with
that for free, so this uses a small, deliberately hand-labeled corpus
where "relevant" is unambiguous by construction — good for catching
regressions in ranking/retrieval logic, not a claim about real-world
search quality (that needs real usage data, per Phase 1.9's spirit of
measuring rather than assuming).

Definitions:
    precision@k = (relevant documents in top k) / k
    recall      = (relevant documents retrieved) / (total relevant documents)
"""

from search_engine.inverted_index import InvertedIndex
from search_engine.tokenizer import tokenize
from search_engine.top_k import top_k_search

# (document_id, text) pairs. Deliberately includes near-miss documents
# (same vocabulary, different topic) to make precision meaningful.
_CORPUS = [
    ("doc1", "Congestion control in TCP prevents network collapse under heavy load."),
    ("doc2", "TCP slow start and congestion avoidance are core congestion control mechanisms."),
    ("doc3", "Database normalization reduces redundancy in relational schema design."),
    ("doc4", "Normal forms in database normalization include 1NF, 2NF, and 3NF."),
    ("doc5", "Traffic congestion in major cities is a growing urban planning problem."),
    ("doc6", "This recipe uses garlic, onions, and fresh basil for the sauce base."),
    ("doc7", "Sorting algorithms like quicksort and mergesort have O(n log n) complexity."),
    ("doc8", "Hash maps provide average O(1) lookup, insertion, and deletion."),
]

# query -> set of document IDs judged relevant, decided by hand when the
# corpus above was written (this IS the ground truth, not derived from
# the search engine itself).
_QUERIES_WITH_GROUND_TRUTH = {
    "congestion control": {"doc1", "doc2"},  # doc5 is urban traffic, NOT network congestion
    "database normalization": {"doc3", "doc4"},
    "sorting algorithms": {"doc7"},
}


def _build_benchmark_index() -> InvertedIndex:
    idx = InvertedIndex()
    for document_id, text in _CORPUS:
        idx.add_document(document_id, tokenize(text))
    return idx


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """precision@k = (relevant docs in top k) / k"""
    if k == 0:
        return 0.0
    top_k_retrieved = retrieved[:k]
    hits = sum(1 for doc_id in top_k_retrieved if doc_id in relevant)
    return hits / k


def recall(retrieved: list[str], relevant: set[str]) -> float:
    """recall = (relevant docs retrieved, at any rank) / (total relevant docs)"""
    if not relevant:
        return 0.0
    hits = sum(1 for doc_id in retrieved if doc_id in relevant)
    return hits / len(relevant)


def run_benchmark() -> dict[str, dict[str, float]]:
    """
    Run every query in _QUERIES_WITH_GROUND_TRUTH against the benchmark
    corpus, returning precision@k (k = number of relevant docs for that
    query) and recall for each.
    """
    idx = _build_benchmark_index()
    all_doc_ids = [doc_id for doc_id, _ in _CORPUS]
    results = {}

    for query_text, relevant_doc_ids in _QUERIES_WITH_GROUND_TRUTH.items():
        query_terms = tokenize(query_text)
        top_results = top_k_search(idx, query_terms, all_doc_ids, k=len(all_doc_ids))
        retrieved_ids = [doc_id for doc_id, score in top_results if score > 0]

        k = len(relevant_doc_ids)
        results[query_text] = {
            "precision_at_k": precision_at_k(retrieved_ids, relevant_doc_ids, k),
            "recall": recall(retrieved_ids, relevant_doc_ids),
        }

    return results


if __name__ == "__main__":
    for query, metrics in run_benchmark().items():
        print(f"{query!r}: precision@k={metrics['precision_at_k']:.2f}  recall={metrics['recall']:.2f}")