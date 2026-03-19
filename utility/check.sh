"""
Experiment Completion Checker — Textual TUI

Scans a data directory for missing exp-N.mat files based on
the total experiment count derived from a selected parameter file.

Usage:
    python check.py [--data-dir PATH]
    Default --data-dir is ../server/data
"""

import argparse
import os
import sys
import time as _time

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Center
from textual.widgets import (
    Header,
    Footer,
    Static,
    ProgressBar,
    OptionList,
    RichLog,
)
from textual.screen import Screen
from textual import work, on
from textual.binding import Binding


# ── Helper functions (mirrored from server.py) ─────────────────────────


def merge_objects(dict1, dict2):
    merged = dict1.copy()
    merged.update(dict2)
    return merged


def generate_combinations(input_obj, id_counter):
    keys = list(input_obj.keys())
    values = list(input_obj.values())
    result = []

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

    combine(0, {})
    return [result, id_counter]


def generate_combined_data(shared_params, id_counter, *param_sets):
    combined = []
    for params in param_sets:
        arr, id_counter = generate_combinations(
            merge_objects(shared_params, params), id_counter
        )
        combined += arr
    return combined, id_counter


def print_list_as_json(lst):
    pass  # stub


# ── Utilities ──────────────────────────────────────────────────────────


def compress_missing_ranges(filenames):
    """Compress ['exp-1.mat', 'exp-3.mat', …] into range strings."""
    if not filenames:
        return []
    nums = sorted(int(f.split("-")[1].split(".")[0]) for f in filenames)
    ranges = []
    start = end = nums[0]
    for n in nums[1:]:
        if n == end + 1:
            end = n
        else:
            ranges.append(f"exp-{start}" if start == end else f"exp-{start}‥exp-{end}")
            start = end = n
    ranges.append(f"exp-{start}" if start == end else f"exp-{start}‥exp-{end}")
    return ranges


# ── Selection Screen ───────────────────────────────────────────────────


class SelectionScreen(Screen):
    BINDINGS = [Binding("q", "quit", "Quit")]

    def __init__(self, param_files):
        super().__init__()
        self.param_files = param_files

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Center():
            with Vertical(id="sel-box"):
                yield Static(
                    "🔬 [bold cyan]Experiment Completion Checker[/]",
                    id="sel-title",
                )
                yield Static(
                    "[dim]Select a parameter file to begin[/]", id="sel-sub"
                )
                yield OptionList(*self.param_files, id="file-list")
        yield Footer()

    @on(OptionList.OptionSelected)
    def on_selected(self, event: OptionList.OptionSelected) -> None:
        self.app.selected_param = self.param_files[event.option_index]
        self.app.push_screen(CheckingScreen())


# ── Checking Screen ────────────────────────────────────────────────────


class CheckingScreen(Screen):
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "app.pop_screen", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main"):
            with Vertical(id="left"):
                yield Static("[b]📂 Experiment Files[/b]", id="left-hdr")
                yield RichLog(
                    id="file-log",
                    highlight=True,
                    markup=True,
                    wrap=False,
                    max_lines=2000,
                    auto_scroll=True,
                )
            with Vertical(id="right"):
                yield Static("[b]⚙  Parameters[/b]", id="right-hdr")
                yield Static("Loading parameter file…", id="params")
        with Vertical(id="bottom"):
            yield ProgressBar(id="pbar", total=100, show_eta=True)
            yield Static("Preparing…", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.run_check()

    @work(exclusive=True, thread=True)
    def run_check(self) -> None:
        try:
            import numpy as np
        except ImportError:
            np = None

        param_file = self.app.selected_param
        server_dir = self.app.server_dir
        data_dir = self.app.data_dir

        # Execute the parameter file
        ns = {
            "id_counter": 1,
            "generate_combinations": generate_combinations,
            "generate_combined_data": generate_combined_data,
            "merge_objects": merge_objects,
            "print_list_as_json": print_list_as_json,
        }
        if np is not None:
            ns["np"] = np

        path = os.path.join(server_dir, param_file)
        with open(path) as fh:
            exec(fh.read(), ns)

        data_array = ns.get("data_array", [])
        total = len(data_array)

        status_w = self.query_one("#status", Static)

        if total == 0:
            self.app.call_from_thread(
                status_w.update,
                "[bold red]data_array is empty — nothing to check.[/]",
            )
            return

        pbar = self.query_one("#pbar", ProgressBar)
        flog = self.query_one("#file-log", RichLog)
        params_w = self.query_one("#params", Static)

        self.app.call_from_thread(setattr, pbar, "total", total)
        self.app.call_from_thread(
            status_w.update,
            f"  Loaded [bold cyan]{param_file}[/]  •  "
            f"[bold]{total:,}[/] experiments  •  "
            f"Scanning [dim]{data_dir}[/]",
        )
        _time.sleep(0.4)

        missing = []
        found = 0
        update_every = max(1, total // 800)
        batch_lines = []
        advanced = 0

        for i in range(total):
            exp_id = i + 1
            fname = f"exp-{exp_id}.mat"
            fpath = os.path.join(data_dir, fname)

            exists = os.path.isfile(fpath)
            if exists:
                found += 1
                batch_lines.append(f"[green]  ✓  {fname}[/]")
            else:
                missing.append(fname)
                batch_lines.append(f"[bold red]  ✗  {fname}[/]")

            should_update = ((i + 1) % update_every == 0) or (i == total - 1)
            if not should_update:
                continue

            # Flush batch to file log
            self.app.call_from_thread(flog.write, "\n".join(batch_lines))
            batch_lines = []

            # Show current experiment params
            exp = data_array[i]
            ptxt = "\n".join(
                f"  [cyan]{k}[/]: [white]{v}[/]"
                for k, v in exp.items()
                if k != "id"
            )
            self.app.call_from_thread(
                params_w.update,
                f"[bold yellow]▶ {fname}[/]\n"
                f"[dim]Experiment {exp_id:,} of {total:,}[/]\n\n{ptxt}",
            )

            # Progress bar
            step = (i + 1) - advanced
            advanced = i + 1
            self.app.call_from_thread(pbar.advance, step)

            # Status bar
            pct = (i + 1) / total * 100
            self.app.call_from_thread(
                status_w.update,
                f"  [bold]{i+1:,}[/] / [bold]{total:,}[/]  │  "
                f"[green]✓ {found:,}[/]  [red]✗ {len(missing):,}[/]  │  "
                f"[cyan]{pct:.1f}%[/]",
            )

            # Throttle for visual effect
            if total < 200:
                _time.sleep(0.03)
            elif total < 2000:
                _time.sleep(0.01)
            else:
                _time.sleep(0.002)

        # ── Final summary ────────────────────────────────────────
        pct = found / total * 100 if total else 0
        pct_c = "green" if pct == 100 else ("yellow" if pct >= 50 else "red")

        bar_w = 30
        filled = int(bar_w * pct / 100)
        bar = f"[green]{'█' * filled}[/][dim]{'░' * (bar_w - filled)}[/]"

        lines = [
            "[bold]━━━ Completion Report ━━━[/]\n",
            f"  [bold]Parameter file:[/]  [cyan]{param_file}[/]",
            f"  [bold]Data directory:[/]  [dim]{data_dir}[/]",
            f"  [bold]Total:[/]           [white]{total:,}[/]",
            f"  [bold]Found:[/]           [green]{found:,}[/]",
            f"  [bold]Missing:[/]         [red]{len(missing):,}[/]",
            f"  [bold]Completion:[/]      {bar}  [{pct_c}]{pct:.1f}%[/]",
        ]

        if missing:
            ranges = compress_missing_ranges(missing)
            shown = ", ".join(ranges[:20])
            if len(ranges) > 20:
                shown += f" … +{len(ranges) - 20} more"
            lines.append(f"\n  [bold red]Missing ranges:[/]\n  [red]{shown}[/]")
        else:
            lines.append(f"\n  [bold green]✓ All experiment files present![/]")

        self.app.call_from_thread(params_w.update, "\n".join(lines))
        self.app.call_from_thread(
            status_w.update,
            f"  [bold green]✓ Done![/]  │  "
            f"[bold]{total:,}[/] checked  │  "
            f"[green]✓ {found:,}[/]  [red]✗ {len(missing):,}[/]  │  "
            f"[{pct_c}]{pct:.1f}%[/]",
        )


# ── App ────────────────────────────────────────────────────────────────


class CheckerApp(App):
    TITLE = "Experiment Checker"
    CSS = """
    Screen {
        background: $surface;
    }

    /* ── Selection ── */
    #sel-box {
        width: 64;
        height: auto;
        max-height: 80%;
        padding: 2 4;
        border: tall $accent;
        background: $panel;
    }
    #sel-title {
        text-align: center;
        padding: 1 0;
    }
    #sel-sub {
        text-align: center;
        margin-bottom: 1;
    }
    #file-list {
        height: auto;
        max-height: 20;
    }

    /* ── Checking ── */
    #main {
        height: 1fr;
    }
    #left {
        width: 1fr;
        min-width: 30;
    }
    #left-hdr, #right-hdr {
        height: 1;
        padding: 0 1;
        background: $accent 15%;
        text-style: bold;
    }
    #file-log {
        height: 1fr;
        border-right: thick $accent 30%;
        padding: 0 1;
        scrollbar-size: 1 1;
    }
    #right {
        width: 50;
    }
    #params {
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
    }
    #bottom {
        height: auto;
        dock: bottom;
        background: $panel;
        padding: 0 1;
    }
    ProgressBar {
        padding: 0 1;
    }
    #status {
        text-align: center;
        height: 1;
        padding: 0 1;
    }
    """

    def __init__(self, server_dir, data_dir, param_files):
        super().__init__()
        self.server_dir = server_dir
        self.data_dir = data_dir
        self.param_files = param_files
        self.selected_param = None

    def on_mount(self) -> None:
        self.push_screen(SelectionScreen(self.param_files))


# ── Entry point ────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Experiment Completion Checker TUI"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Path to the data directory (default: ../server/data)",
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_dir = os.path.normpath(os.path.join(script_dir, "..", "server"))
    data_dir = args.data_dir or os.path.join(server_dir, "data")
    data_dir = os.path.abspath(data_dir)

    param_files = sorted(
        f
        for f in os.listdir(server_dir)
        if f.startswith("parameters_") and f.endswith(".py")
    )

    if not param_files:
        print("No parameter files (parameters_*.py) found in server/")
        sys.exit(1)

    app = CheckerApp(server_dir, data_dir, param_files)
    app.run()


if __name__ == "__main__":
    main()
