"""Parse and pair retrieval evaluation records from retr_data.txt."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EvaluationRecord:
	"""One original task query paired with its retrieval test query."""

	original_query: str
	retrieval_query: str
	stored_response: str = ""


# Within-batch retrieval row permutations for retr_data.txt.
# Batch 1 reorders retrieval queries; batch 2 swaps the last two retrieval rows.
_BATCH_RETRIEVAL_PERMUTATIONS: dict[int, list[int]] = {
	0: [1, 2, 3, 4, 0, 5, 6],
	1: [0, 1, 2, 4, 3],
}


def _split_batches(section: str) -> list[list[tuple[str, str]]]:
	"""Split a markdown table section into batches separated by blank lines."""
	batches: list[list[tuple[str, str]]] = []
	current: list[tuple[str, str]] = []

	for line in section.splitlines():
		stripped = line.strip()
		if not stripped:
			if current:
				batches.append(current)
				current = []
			continue

		if not stripped.startswith("|"):
			continue
		if "---" in stripped:
			continue
		if stripped.lower().startswith("| query"):
			continue
		if stripped.lower().startswith("| retrieval"):
			continue

		columns = [column.strip() for column in stripped.split("|")[1:-1]]
		if len(columns) < 2 or not columns[0]:
			continue
		current.append((columns[0], columns[1]))

	if current:
		batches.append(current)

	return batches


def _pair_batch(
	original_rows: list[tuple[str, str]],
	retrieval_rows: list[tuple[str, str]],
	batch_index: int,
) -> list[EvaluationRecord]:
	"""Pair original and retrieval rows within a batch using dataset permutations."""
	if len(original_rows) != len(retrieval_rows):
		raise ValueError(
			f"Batch size mismatch: {len(original_rows)} original rows vs "
			f"{len(retrieval_rows)} retrieval rows"
		)

	size = len(original_rows)
	permutation = _BATCH_RETRIEVAL_PERMUTATIONS.get(batch_index, list(range(size)))
	if len(permutation) != size:
		raise ValueError(
			f"Permutation length mismatch for batch {batch_index}: "
			f"expected {size}, got {len(permutation)}"
		)

	return [
		EvaluationRecord(
			original_query=original_rows[original_index][0],
			retrieval_query=retrieval_rows[retrieval_index][0],
			stored_response=retrieval_rows[retrieval_index][1],
		)
		for original_index, retrieval_index in enumerate(permutation)
	]


def load_evaluation_dataset(path: Path | str) -> list[EvaluationRecord]:
	"""Load paired evaluation records from the retrieval test dataset file."""
	dataset_path = Path(path)
	if not dataset_path.exists():
		raise FileNotFoundError(f"Evaluation dataset not found: {dataset_path}")

	content = dataset_path.read_text(encoding="utf-8")
	parts = re.split(r"(?i)\|\s*Retrieval Queries\s*\|", content, maxsplit=1)
	if len(parts) != 2:
		raise ValueError("Dataset must contain a 'Retrieval Queries' section.")

	original_section, retrieval_section = parts
	original_batches = _split_batches(original_section)
	retrieval_batches = _split_batches(retrieval_section)

	if len(original_batches) != len(retrieval_batches):
		raise ValueError(
			f"Batch count mismatch: {len(original_batches)} original batches vs "
			f"{len(retrieval_batches)} retrieval batches"
		)

	records: list[EvaluationRecord] = []
	for batch_index, (original_batch, retrieval_batch) in enumerate(
		zip(original_batches, retrieval_batches, strict=True)
	):
		records.extend(_pair_batch(original_batch, retrieval_batch, batch_index))

	if not records:
		raise ValueError(f"No evaluation records parsed from {dataset_path}")

	return records
