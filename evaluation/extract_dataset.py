"""Extract evaluation dataset from retr_data.txt and save as JSON."""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.dataset import load_evaluation_dataset


def main() -> None:
    """Extract and save evaluation dataset as JSON."""
    project_root = Path(__file__).resolve().parents[1]
    dataset_path = project_root / "docs" / "retr_data.txt"
    output_path = project_root / "evaluation" / "test_queries.json"

    # Load dataset using existing parser
    records = load_evaluation_dataset(dataset_path)

    # Convert to serializable format
    dataset = [
        {
            "original_query": record.original_query,
            "retrieval_query": record.retrieval_query,
            "stored_response": record.stored_response,
        }
        for record in records
    ]

    # Save as JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(dataset)} evaluation records to {output_path}")


if __name__ == "__main__":
    main()
