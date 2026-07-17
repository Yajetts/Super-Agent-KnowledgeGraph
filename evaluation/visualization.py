"""Publication-quality charts for SuperAgent evaluation."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as patches


def load_metrics_from_report(report_path: Path) -> dict[str, dict[str, float]]:
    """Load metrics from the evaluation report."""
    metrics = {"baseline": {}, "superagent": {}}
    
    with open(report_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    current_section = None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if "Baseline Results" in line:
            current_section = "baseline"
        elif "SuperAgent Results" in line:
            current_section = "superagent"
        elif "Task Success Rate (TSR)" in line:
            # Value is on the next line
            value_line = lines[i + 1].strip()
            value = float(value_line.replace("%", ""))
            metrics[current_section]["tsr"] = value
        elif "Expected Agent Coverage (EAC)" in line:
            # Value is on the next line
            value_line = lines[i + 1].strip()
            value = float(value_line.replace("%", ""))
            metrics[current_section]["asa"] = value
        elif "Specialized Agent Utilization Rate (SAUR)" in line:
            # Value is on the next line
            value_line = lines[i + 1].strip()
            value = float(value_line.replace("%", ""))
            metrics[current_section]["saur"] = value
        elif "Average Execution Time (AET)" in line:
            # Value is on the next line
            value_line = lines[i + 1].strip()
            value = float(value_line.split()[0])
            metrics[current_section]["aet"] = value
        
        i += 1
    
    return metrics


def generate_task_success_rate_chart(metrics: dict[str, dict[str, float]], output_dir: Path) -> None:
    """Generate Task Success Rate comparison chart."""
    fig, ax = plt.subplots(figsize=(6, 4))
    
    systems = ["Baseline", "SuperAgent"]
    values = [metrics["baseline"]["tsr"], metrics["superagent"]["tsr"]]
    
    bars = ax.bar(systems, values, color=["#3498db", "#2ecc71"], width=0.6)
    ax.set_ylabel("Task Success Rate (%)", fontsize=11)
    ax.set_title("Task Success Rate Comparison", fontsize=12, fontweight="bold")
    ax.set_ylim(0, 110)
    ax.set_xlabel("System Configuration", fontsize=11)
    
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{height:.2f}%",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    
    ax.tick_params(axis="both", labelsize=10)
    plt.tight_layout()
    
    plt.savefig(output_dir / "task_success_rate.png", dpi=300, facecolor="white")
    plt.savefig(output_dir / "task_success_rate.pdf", facecolor="white")
    plt.close()
    
    print("Generated: task_success_rate.png and task_success_rate.pdf")


def generate_agent_selection_accuracy_chart(metrics: dict[str, dict[str, float]], output_dir: Path) -> None:
    """Generate Agent Selection Accuracy comparison chart."""
    fig, ax = plt.subplots(figsize=(6, 4))
    
    systems = ["Baseline", "SuperAgent"]
    values = [metrics["baseline"]["asa"], metrics["superagent"]["asa"]]
    
    bars = ax.bar(systems, values, color=["#3498db", "#2ecc71"], width=0.6)
    ax.set_ylabel("Agent Selection Accuracy (%)", fontsize=11)
    ax.set_title("Agent Selection Accuracy Comparison", fontsize=12, fontweight="bold")
    ax.set_ylim(0, 110)
    ax.set_xlabel("System Configuration", fontsize=11)
    
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{height:.2f}%",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    
    ax.tick_params(axis="both", labelsize=10)
    plt.tight_layout()
    
    plt.savefig(output_dir / "agent_selection_accuracy.png", dpi=300, facecolor="white")
    plt.savefig(output_dir / "agent_selection_accuracy.pdf", facecolor="white")
    plt.close()
    
    print("Generated: agent_selection_accuracy.png and agent_selection_accuracy.pdf")


def generate_saur_chart(metrics: dict[str, dict[str, float]], output_dir: Path) -> None:
    """Generate Specialized Agent Utilization Rate comparison chart."""
    fig, ax = plt.subplots(figsize=(6, 4))
    
    systems = ["Baseline", "SuperAgent"]
    values = [metrics["baseline"]["saur"], metrics["superagent"]["saur"]]
    
    bars = ax.bar(systems, values, color=["#3498db", "#2ecc71"], width=0.6)
    ax.set_ylabel("Specialized Agent Utilization Rate (%)", fontsize=11)
    ax.set_title("Specialized Agent Utilization Rate Comparison", fontsize=12, fontweight="bold")
    ax.set_ylim(0, 110)
    ax.set_xlabel("System Configuration", fontsize=11)
    
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{height:.2f}%",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    
    ax.tick_params(axis="both", labelsize=10)
    plt.tight_layout()
    
    plt.savefig(output_dir / "specialized_agent_utilization.png", dpi=300, facecolor="white")
    plt.savefig(output_dir / "specialized_agent_utilization.pdf", facecolor="white")
    plt.close()
    
    print("Generated: specialized_agent_utilization.png and specialized_agent_utilization.pdf")


def generate_execution_time_chart(metrics: dict[str, dict[str, float]], output_dir: Path) -> None:
    """Generate Execution Time comparison chart."""
    fig, ax = plt.subplots(figsize=(6, 4))
    
    systems = ["Baseline", "SuperAgent"]
    values = [metrics["baseline"]["aet"], metrics["superagent"]["aet"]]
    
    bars = ax.bar(systems, values, color=["#3498db", "#2ecc71"], width=0.6)
    ax.set_ylabel("Execution Time (s)", fontsize=11)
    ax.set_title("Average Execution Time Comparison", fontsize=12, fontweight="bold")
    ax.set_xlabel("System Configuration", fontsize=11)
    
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{height:.2f}s",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    
    ax.tick_params(axis="both", labelsize=10)
    plt.tight_layout()
    
    plt.savefig(output_dir / "execution_time.png", dpi=300, facecolor="white")
    plt.savefig(output_dir / "execution_time.pdf", facecolor="white")
    plt.close()
    
    print("Generated: execution_time.png and execution_time.pdf")


def generate_superagent_charts() -> None:
    """Generate all publication-quality charts for SuperAgent evaluation."""
    # Setup paths
    results_dir = Path("evaluation/results")
    charts_dir = Path("evaluation/charts_superagent")
    charts_dir.mkdir(parents=True, exist_ok=True)
    
    # Load metrics from report
    report_path = Path("docs/superagent_report_v2.md")
    metrics = load_metrics_from_report(report_path)
    
    print("Generating publication-quality charts...")
    print(f"Output directory: {charts_dir}")
    print()
    
    # Generate all charts
    generate_task_success_rate_chart(metrics, charts_dir)
    generate_agent_selection_accuracy_chart(metrics, charts_dir)
    generate_saur_chart(metrics, charts_dir)
    generate_execution_time_chart(metrics, charts_dir)
    
    print()
    print("All charts generated successfully!")


def load_kg_metrics() -> dict[str, float]:
    """Load Knowledge Graph evaluation metrics from report."""
    base_dir = Path(__file__).parent.parent
    report_path = base_dir / "docs" / "kg_report.md"
    
    metrics = {}
    
    with open(report_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        if "**Knowledge Density**" in line:
            # Value is on the same line after the colon
            value = float(line.split(":")[-1].strip())
            metrics["knowledge_density"] = value
        elif "**Average Relevant Knowledge Reuse Rate**" in line:
            # Value is on the same line after the colon
            value = float(line.split(":")[-1].strip())
            metrics["relevant_knowledge_reuse_rate"] = value
        elif "**Knowledge Organization Score**" in line:
            # Value is on the same line after the colon
            value = float(line.split(":")[-1].strip())
            metrics["knowledge_organization_score"] = value
        elif "**Average Context Retrieval Latency**" in line:
            # Value is on the same line after the colon (e.g., "0.0305 seconds")
            value_str = line.split(":")[-1].strip().split()[0]
            value = float(value_str)
            metrics["retrieval_latency"] = value
    
    return metrics


def generate_kg_dashboard() -> None:
    """Generate publication-quality Knowledge Graph performance dashboard."""
    # Load metrics
    metrics = load_kg_metrics()
    
    # Extract values
    kd = metrics["knowledge_density"]
    rkrr = metrics["relevant_knowledge_reuse_rate"]
    kos = metrics["knowledge_organization_score"]
    latency_ms = metrics["retrieval_latency"] * 1000  # Convert to ms
    
    # Setup figure
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    fig.patch.set_facecolor('white')
    
    # Card configurations
    cards = [
        {
            "ax": axes[0, 0],
            "title": "Knowledge Density",
            "value": f"{kd:.3f}",
            "subtitle": "Average relationships per node",
            "normalized": kd / 3.0,  # Max expected value of 3.0
            "color": "#3498db"
        },
        {
            "ax": axes[0, 1],
            "title": "Relevant Knowledge Reuse Rate",
            "value": f"{rkrr * 100:.2f}%",
            "subtitle": "Relevant historical knowledge retrieved",
            "normalized": rkrr,  # Already 0-1
            "color": "#2ecc71"
        },
        {
            "ax": axes[1, 0],
            "title": "Knowledge Organization Score",
            "value": f"{kos * 100:.0f}%",
            "subtitle": "Structural completeness of graph",
            "normalized": kos,  # Already 0-1
            "color": "#9b59b6"
        },
        {
            "ax": axes[1, 1],
            "title": "Retrieval Latency",
            "value": f"{latency_ms:.1f} ms",
            "subtitle": "Average retrieval time",
            "normalized": 1 - (latency_ms / 100.0),  # Invert: lower is better
            "color": "#e74c3c"
        }
    ]
    
    # Draw each card
    for card in cards:
        ax = card["ax"]
        
        # Remove axes
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Add border
        rect = patches.Rectangle((0, 0), 1, 1, linewidth=1, edgecolor='#e0e0e0', facecolor='none')
        ax.add_patch(rect)
        
        # Title
        ax.text(0.5, 0.85, card["title"], ha='center', va='top', fontsize=12, fontweight='bold')
        
        # Value
        ax.text(0.5, 0.55, card["value"], ha='center', va='center', fontsize=24, fontweight='bold')
        
        # Progress bar background
        bar_x = 0.15
        bar_y = 0.25
        bar_width = 0.7
        bar_height = 0.08
        ax.add_patch(patches.Rectangle((bar_x, bar_y), bar_width, bar_height, 
                                       linewidth=0, facecolor='#e0e0e0'))
        
        # Progress bar fill
        fill_width = bar_width * card["normalized"]
        ax.add_patch(patches.Rectangle((bar_x, bar_y), fill_width, bar_height, 
                                       linewidth=0, facecolor=card["color"]))
        
        # Subtitle
        ax.text(0.5, 0.12, card["subtitle"], ha='center', va='top', fontsize=9, color='#666666')
    
    plt.tight_layout()
    
    # Save outputs
    base_dir = Path(__file__).parent
    charts_dir = base_dir / "results" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    
    png_path = charts_dir / "knowledge_graph_dashboard.png"
    pdf_path = charts_dir / "knowledge_graph_dashboard.pdf"
    
    plt.savefig(png_path, dpi=300, facecolor='white')
    plt.savefig(pdf_path, facecolor='white')
    plt.close()
    
    print(f"Generated: {png_path}")
    print(f"Generated: {pdf_path}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "kg":
        generate_kg_dashboard()
    else:
        generate_superagent_charts()
