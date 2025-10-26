import json
import sys
import os
import requests
from typing import List, Dict, Any

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def load_eval_set(filepath: str = "eval/qa_eval_set.json") -> List[Dict[str, Any]]:
    with open(filepath, 'r') as f:
        return json.load(f)


def calculate_f1(expected: str, actual: str) -> float:
    expected_tokens = set(expected.lower().split())
    actual_tokens = set(actual.lower().split())

    if not expected_tokens or not actual_tokens:
        return 0.0

    true_positives = len(expected_tokens & actual_tokens)
    false_positives = len(actual_tokens - expected_tokens)
    false_negatives = len(expected_tokens - actual_tokens)

    if true_positives == 0:
        return 0.0

    precision = true_positives / (true_positives + false_positives)
    recall = true_positives / (true_positives + false_negatives)

    f1 = 2 * (precision * recall) / (precision + recall)
    return f1


def exact_match(expected: str, actual: str) -> bool:
    return expected.lower().strip() == actual.lower().strip()


def run_evaluation(document_ids: List[str] = None) -> Dict[str, Any]:
    eval_set = load_eval_set()

    total_questions = len(eval_set)
    exact_matches = 0
    f1_scores = []
    has_sources = 0

    print(f"Running evaluation on {total_questions} questions...")
    print(f"API Base URL: {API_BASE_URL}")
    print("-" * 80)

    for item in eval_set:
        question_id = item["id"]
        question = item["question"]
        expected = item["expected_answer"]

        try:
            response = requests.post(
                f"{API_BASE_URL}/ask",
                json={"question": question, "document_ids": document_ids},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                actual_answer = data.get("answer", "")
                sources = data.get("sources", [])

                is_exact = exact_match(expected, actual_answer)
                f1 = calculate_f1(expected, actual_answer)

                if is_exact:
                    exact_matches += 1

                if sources:
                    has_sources += 1

                f1_scores.append(f1)

                print(f"[{question_id}] F1: {f1:.2f} | Exact: {is_exact} | Sources: {len(sources)}")
                print(f"  Q: {question}")
                print(f"  Expected: {expected}")
                print(f"  Actual: {actual_answer[:100]}...")
                print()

            else:
                print(f"[{question_id}] ERROR: Status {response.status_code}")
                f1_scores.append(0.0)

        except Exception as e:
            print(f"[{question_id}] ERROR: {str(e)}")
            f1_scores.append(0.0)

    avg_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0
    exact_match_rate = exact_matches / total_questions
    citation_rate = has_sources / total_questions

    results = {
        "total_questions": total_questions,
        "exact_matches": exact_matches,
        "exact_match_rate": exact_match_rate,
        "average_f1": avg_f1,
        "citation_rate": citation_rate
    }

    print("-" * 80)
    print("EVALUATION RESULTS")
    print("-" * 80)
    print(f"Total Questions: {total_questions}")
    print(f"Exact Matches: {exact_matches} ({exact_match_rate:.1%})")
    print(f"Average F1 Score: {avg_f1:.3f}")
    print(f"Questions with Citations: {has_sources} ({citation_rate:.1%})")
    print("-" * 80)

    return results


def save_score(results: Dict[str, Any], filepath: str = "eval/score.txt"):
    score = results["average_f1"] * 100

    with open(filepath, 'w') as f:
        f.write(f"Score: {score:.1f}/100\n\n")
        f.write(f"Evaluation Summary:\n")
        f.write(f"- Exact Match Rate: {results['exact_match_rate']:.1%}\n")
        f.write(f"- Average F1: {results['average_f1']:.3f}\n")
        f.write(f"- Citation Rate: {results['citation_rate']:.1%}\n\n")

        if score < 50:
            f.write("Note: Low score may indicate missing test data or API configuration issues.\n")
        elif score < 70:
            f.write("Note: Moderate performance. Consider improving extraction accuracy and RAG quality.\n")
        else:
            f.write("Note: Good performance on evaluation set.\n")

    print(f"\nScore saved to {filepath}")


if __name__ == "__main__":
    doc_ids = sys.argv[1:] if len(sys.argv) > 1 else None

    results = run_evaluation(document_ids=doc_ids)
    save_score(results)

    print(f"\nFinal Score: {results['average_f1'] * 100:.1f}/100")
