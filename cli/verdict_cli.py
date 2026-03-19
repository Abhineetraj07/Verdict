import asyncio
import json
import sys
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table

from backend.app.engine.orchestrator import run_evaluation
from backend.app.models.schemas import DatasetEntry, EvalSuiteCreate
from backend.app.providers.gemini import GeminiProvider

app = typer.Typer(name="verdict", help="Verdict - Federated Prompt Evaluation Framework")
console = Console()


@app.command()
def run(
    suite: str = typer.Option(..., "--suite", "-s", help="Path to YAML eval suite config"),
    dataset: str = typer.Option(..., "--dataset", "-d", help="Path to JSON dataset file"),
    output: str = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
):
    """Run an evaluation suite on a dataset."""
    suite_path = Path(suite)
    dataset_path = Path(dataset)

    if not suite_path.exists():
        console.print(f"[red]Suite file not found: {suite}[/red]")
        raise typer.Exit(1)
    if not dataset_path.exists():
        console.print(f"[red]Dataset file not found: {dataset}[/red]")
        raise typer.Exit(1)

    with open(suite_path) as f:
        suite_config = yaml.safe_load(f)

    with open(dataset_path) as f:
        dataset_data = json.load(f)

    eval_suite = EvalSuiteCreate(**suite_config)
    entries = [DatasetEntry(**e) for e in dataset_data["entries"]]

    console.print(f"\n[bold]Verdict Evaluation[/bold]")
    console.print(f"Suite: [cyan]{eval_suite.name}[/cyan]")
    console.print(f"Dataset: [cyan]{dataset_data.get('name', dataset)}[/cyan]")
    console.print(f"Entries: [cyan]{len(entries)}[/cyan]")
    console.print(f"Judges: [cyan]{len(eval_suite.judges)}[/cyan]")
    console.print(f"Aggregation: [cyan]{eval_suite.aggregation.method}[/cyan]")
    console.print()

    with console.status("[bold green]Running evaluation..."):
        result = asyncio.run(_run_eval(eval_suite, entries))

    _print_results(result, eval_suite)

    if output:
        output_data = {
            "suite": eval_suite.model_dump(),
            "overall_score": result["overall_score"],
            "stats": result["stats"].model_dump(),
            "dimension_breakdown": [d.model_dump() for d in result["dimension_breakdown"]],
            "entry_results": [r.model_dump() for r in result["entry_results"]],
        }
        with open(output, "w") as f:
            json.dump(output_data, f, indent=2)
        console.print(f"\n[green]Results saved to {output}[/green]")


async def _run_eval(suite: EvalSuiteCreate, entries: list[DatasetEntry]) -> dict:
    provider = GeminiProvider()
    return await run_evaluation(suite, entries, provider)


def _print_results(result: dict, suite: EvalSuiteCreate):
    # Overall score
    console.print(f"[bold green]Overall Score: {result['overall_score']:.2f}[/bold green]\n")

    # Stats
    stats = result["stats"]
    stats_table = Table(title="Run Statistics")
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", justify="right")
    stats_table.add_row("Mean", f"{stats.mean:.2f}")
    stats_table.add_row("Median", f"{stats.median:.2f}")
    stats_table.add_row("Std Dev", f"{stats.std:.2f}")
    stats_table.add_row("Min", f"{stats.min:.2f}")
    stats_table.add_row("Max", f"{stats.max:.2f}")
    console.print(stats_table)
    console.print()

    # Dimension breakdown
    dim_table = Table(title="Dimension Breakdown")
    dim_table.add_column("Dimension", style="cyan")
    dim_table.add_column("Mean", justify="right")
    dim_table.add_column("Min", justify="right")
    dim_table.add_column("Max", justify="right")
    for dim in result["dimension_breakdown"]:
        dim_table.add_row(
            dim.dimension,
            f"{dim.mean_score:.2f}",
            f"{dim.min_score:.2f}",
            f"{dim.max_score:.2f}",
        )
    console.print(dim_table)
    console.print()

    # Per-entry results
    entry_table = Table(title="Entry Results")
    entry_table.add_column("#", style="dim", width=3)
    entry_table.add_column("Input", max_width=40)
    for judge in suite.judges:
        entry_table.add_column(judge.dimension.title(), justify="center")
    entry_table.add_column("Score", justify="right", style="bold")

    for entry_result in result["entry_results"]:
        row = [str(entry_result.entry_index), entry_result.input[:40]]
        for judge in suite.judges:
            judge_score = next(
                (s for s in entry_result.judge_scores if s.dimension == judge.dimension),
                None,
            )
            score_val = f"{judge_score.score:.0f}" if judge_score else "-"
            row.append(score_val)

        score_color = "green" if entry_result.aggregated_score >= 3 else "red"
        row.append(f"[{score_color}]{entry_result.aggregated_score:.2f}[/{score_color}]")
        entry_table.add_row(*row)

    console.print(entry_table)


@app.command()
def init():
    """Create example suite and dataset files in the current directory."""
    examples_dir = Path(__file__).parent.parent / "examples"

    suite_src = examples_dir / "suites" / "customer_support.yaml"
    dataset_src = examples_dir / "datasets" / "customer_support_sample.json"

    if suite_src.exists():
        dest = Path("example_suite.yaml")
        dest.write_text(suite_src.read_text())
        console.print(f"[green]Created {dest}[/green]")

    if dataset_src.exists():
        dest = Path("example_dataset.json")
        dest.write_text(dataset_src.read_text())
        console.print(f"[green]Created {dest}[/green]")

    console.print("\n[bold]Run your first evaluation:[/bold]")
    console.print("  python -m cli.verdict_cli run --suite example_suite.yaml --dataset example_dataset.json")


if __name__ == "__main__":
    app()
