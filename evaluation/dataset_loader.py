"""Dataset loader for specialized agent evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class EvaluationTask:
    """A single evaluation task for agent comparison."""

    task_id: str
    query: str


class DatasetLoader:
    """Load evaluation tasks from CSV file."""

    def __init__(self, dataset_path: str | Path) -> None:
        self.dataset_path = Path(dataset_path)

    def load_tasks(self) -> list[EvaluationTask]:
        """Load tasks from CSV file."""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")

        df = pd.read_csv(self.dataset_path)
        tasks = [
            EvaluationTask(task_id=row["task_id"], query=row["query"])
            for _, row in df.iterrows()
        ]
        return tasks
