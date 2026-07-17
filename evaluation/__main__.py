"""CLI entrypoint for retrieval evaluation."""

from __future__ import annotations

import argparse
from pathlib import Path

from loguru import logger

from config.logging_config import setup_logging
from evaluation.backends.graph_only import GraphOnlyBackend
from evaluation.backends.graphrag import GraphRAGBackend
from evaluation.compare import compare_backends
from evaluation.evaluator import EvaluatorConfig, RetrievalEvaluator


def _project_root() -> Path:
	return Path(__file__).resolve().parents[1]


def _build_parser() -> argparse.ArgumentParser:
	root = _project_root()
	parser = argparse.ArgumentParser(description="SuperAgent KG retrieval evaluation")
	subparsers = parser.add_subparsers(dest="command", required=True)

	run_parser = subparsers.add_parser("run", help="Run evaluation for one backend")
	run_parser.add_argument(
		"--backend",
		default="graph_only",
		choices=["graph_only", "graphrag"],
		help="Retrieval backend to evaluate",
	)
	run_parser.add_argument(
		"--dataset",
		type=Path,
		default=root / "docs" / "retr_data.txt",
		help="Path to the retrieval test dataset",
	)
	run_parser.add_argument(
		"--results-dir",
		type=Path,
		default=root / "evaluation" / "results",
		help="Directory for machine-readable backend result files",
	)
	run_parser.add_argument(
		"--report",
		type=Path,
		default=root / "docs" / "eval_baseline.md",
		help="Path for the markdown baseline report",
	)
	run_parser.add_argument(
		"--threshold",
		type=float,
		default=0.75,
		help="Semantic similarity threshold for relevance",
	)
	run_parser.add_argument(
		"--local-embeddings",
		action="store_true",
		help="Force local TF-IDF embeddings instead of OpenAI",
	)

	compare_parser = subparsers.add_parser("compare", help="Compare backend result files")
	compare_parser.add_argument(
		"result_files",
		nargs="+",
		type=Path,
		help="JSON result files to compare (e.g. graph_only.json graphrag.json)",
	)
	compare_parser.add_argument(
		"--output",
		type=Path,
		default=root / "docs" / "eval_comparison.md",
		help="Path for the comparison markdown report",
	)

	return parser


def main() -> None:
	setup_logging()
	parser = _build_parser()
	args = parser.parse_args()

	if args.command == "run":
		config = EvaluatorConfig(
			dataset_path=args.dataset,
			results_dir=args.results_dir,
			markdown_report_path=args.report,
			relevance_threshold=args.threshold,
			prefer_openai_embeddings=not args.local_embeddings,
		)

		if args.backend == "graph_only":
			evaluator = RetrievalEvaluator(backend=GraphOnlyBackend(), config=config)
		elif args.backend == "graphrag":
			evaluator = RetrievalEvaluator(backend=GraphRAGBackend(), config=config)
		else:
			raise SystemExit(f"Unsupported backend: {args.backend}")

		evaluator.run()
		return

	if args.command == "compare":
		compare_backends(args.result_files, args.output)
		return

	raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
	main()
