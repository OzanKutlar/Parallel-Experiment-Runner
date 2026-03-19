"""
Experiment Completion Checker — Rich TUI
Replaces the old check.sh bash script with a Python TUI.

Scans a data directory for missing exp-N.mat files based on
the total experiment count derived from a selected parameter file.

Usage:
    python check.py [--data-dir PATH]
    Default --data-dir is ../server/data
"""

import argparse
import os
import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt
from rich.progress import Progress, BarColumn, TextColumn, MofNCompleteColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text
from rich import box

# ---------------------------------------------------------------------------
# Helper functions (mirrored from server.py so parameter files can exec)
# ---------------------------------------------------------------------------

def merge_objects(dict1, dict2):
    merged = dict1.copy()
    merged.update(dict2)
    return merged


def generate_combinations(input_obj, id_counter):
    keys = list(input_obj.keys())
    values = list(input_obj.values())

    def combine(index, current_combination):
        nonlocal id_counter
        if index == len(keys):
            current_combination["id"] = id_counter
            result.append(current_combination.copy())
            id_counter += 1
            return
        for value in values[index]:
            current_combination[keys[index]] = value
            combine(index + 1, current_combination)

    result = []
    combine(0, {})
    return [result, id_counter]


def generate_combined_data(shared_params, id_counter, *param_sets):
    combined_data_array = []
    for params in param_sets:
        temp_data_array, id_counter = generate_combinations(
            merge_objects(shared_params, params), id_counter
        )
        combined_data_array += temp_data_array
    return combined_data_array, id_counter


def print_list_as_json(lst):
    pass  # stub — not needed for checking


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Experiment Completion Checker")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "..", "server", "data"),
        help="Path to the data directory (default: ../server/data)",
    )
    args = parser.parse_args()
    data_dir = os.path.abspath(args.data_dir)

    # --- Locate parameter files ---
    server_dir = os.path.join(os.path.dirname(__file__), "..", "server")
    server_dir = os.path.abspath(server_dir)
    param_files = sorted(
        f
        for f in os.listdir(server_dir)
        if f.startswith("parameters_") and f.endswith(".py")
    )

    if not param_files:
        console.print("[bold red]No parameter files found in server/[/]")
        sys.exit(1)

    # --- File selection ---
    console.print()
    console.print(
        Panel(
            "[bold cyan]Experiment Completion Checker[/bold cyan]",
            subtitle="Select a parameter file",
            box=box.DOUBLE_EDGE,
        )
    )

    table = Table(
        show_header=True,
        header_style="bold magenta",
        box=box.SIMPLE_HEAVY,
        pad_edge=False,
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Parameter File", style="cyan")

    for idx, fname in enumerate(param_files, start=1):
        table.add_row(str(idx), fname)

    console.print(table)

    choice = IntPrompt.ask(
        "\n[bold yellow]Select file[/bold yellow]",
        choices=[str(i) for i in range(1, len(param_files) + 1)],
    )
    selected_file = param_files[choice - 1]
    selected_path = os.path.join(server_dir, selected_file)

    console.print(
        f"\n  [dim]Selected:[/dim] [bold green]{selected_file}[/bold green]\n"
    )

    # --- Execute parameter file to get data_array ---
    try:
        import numpy as np  # noqa: F401 — some param files use numpy
    except ImportError:
        np = None

    id_counter = 1
    local_ns = {
        "id_counter": id_counter,
        "generate_combinations": generate_combinations,
        "generate_combined_data": generate_combined_data,
        "merge_objects": merge_objects,
        "print_list_as_json": print_list_as_json,
    }
    if np is not None:
        local_ns["np"] = np

    with open(selected_path, "r") as f:
        code = f.read()

    exec(code, local_ns)

    data_array = local_ns.get("data_array", [])
    total = len(data_array)

    if total == 0:
        console.print("[bold red]data_array is empty — nothing to check.[/]")
        sys.exit(1)

    console.print(
        Panel(
            f"[bold white]Total experiments:[/bold white]  [bold cyan]{total:,}[/bold cyan]\n"
            f"[bold white]Data directory:[/bold white]     [dim]{data_dir}[/dim]",
            title="[bold]Summary[/bold]",
            box=box.ROUNDED,
        )
    )

    # --- Scan for missing files ---
    missing = []
    found = 0

    with Progress(
        TextColumn("[bold blue]Checking"),
        BarColumn(bar_width=40),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("scan", total=total)

        for i in range(1, total + 1):
            file_name = f"exp-{i}.mat"
            file_path = os.path.join(data_dir, file_name)
            if os.path.isfile(file_path):
                found += 1
            else:
                missing.append(file_name)
            progress.advance(task)

    # --- Results ---
    pct = (found / total) * 100 if total else 0
    pct_style = "bold green" if pct == 100 else ("bold yellow" if pct >= 50 else "bold red")

    result_table = Table(
        title="[bold]Results[/bold]",
        box=box.ROUNDED,
        show_header=False,
        padding=(0, 2),
    )
    result_table.add_column("Metric", style="bold white")
    result_table.add_column("Value", justify="right")

    result_table.add_row("Total experiments", f"[cyan]{total:,}[/cyan]")
    result_table.add_row("Found", f"[green]{found:,}[/green]")
    result_table.add_row("Missing", f"[red]{len(missing):,}[/red]")
    result_table.add_row("Completion", f"[{pct_style}]{pct:.1f}%[/{pct_style}]")

    console.print()
    console.print(result_table)

    if missing:
        console.print()
        miss_table = Table(
            title=f"[bold red]Missing Files ({len(missing):,})[/bold red]",
            box=box.SIMPLE,
            show_header=False,
            pad_edge=False,
        )
        miss_table.add_column("#", style="dim", width=8, justify="right")
        miss_table.add_column("File", style="red")

        # Show up to 50 inline, then summarise
        show_limit = 50
        for idx, name in enumerate(missing[:show_limit], start=1):
            miss_table.add_row(str(idx), name)

        if len(missing) > show_limit:
            miss_table.add_row("…", f"and {len(missing) - show_limit:,} more")

        console.print(miss_table)
    else:
        console.print("\n[bold green]✓ All experiment files are present![/bold green]\n")


if __name__ == "__main__":
    main()
