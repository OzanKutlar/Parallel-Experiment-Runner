"""
Experiment Integrity Checker — Textual TUI

Scans a data directory for exp-N.mat files based on the total experiment count 
derived from a selected parameter file. It deeply inspects each .mat file for:
1. Missing files
2. Corrupted files (unparseable by scipy)
3. Structural integrity (missing required objects)
4. Data integrity (NaNs, empty fields inside structs)

Usage:
    python integrity_check.py [--data-dir PATH]
    Default --data-dir is ../server/data
"""

import argparse
import os
import sys
import time as _time
import numpy as np
import scipy.io

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
from textual.widgets.option_list import Option
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

def compress_missing_ranges(nums):
    """Compress [1, 3, 4, 5] into range strings."""
    if not nums:
        return []
    nums = sorted(nums)
    ranges = []
    start = end = nums[0]
    for n in nums[1:]:
        if n == end + 1:
            end = n
        else:
            ranges.append(f"{start}" if start == end else f"{start}‥{end}")
            start = end = n
    ranges.append(f"{start}" if start == end else f"{start}‥{end}")
    return ranges

def check_file(fpath):
    if not os.path.isfile(fpath):
        return "missing", "File not found"
    
    if os.path.getsize(fpath) == 0:
        return "corrupted", "File is 0 bytes"
        
    try:
        mat_data = scipy.io.loadmat(fpath, squeeze_me=True, struct_as_record=False)
    except Exception as e:
        return "corrupted", f"Failed to load: {str(e)}"
        
    # Check structure
    required_keys = ['best', 'error', 'runtime', 'convergence_array', 'op', 'algo']
    missing_keys = [k for k in required_keys if k not in mat_data]
    if missing_keys:
        return "bad_struct", f"Missing variables: {', '.join(missing_keys)}"
        
    # Check data integrity
    try:
        best = mat_data['best']
        error = mat_data['error']
        runtime = mat_data['runtime']
        conv_array = mat_data['convergence_array']
        
        # 1. best.fit
        fit = getattr(best, 'fit', None)
        if fit is None or (isinstance(fit, float) and np.isnan(fit)):
            return "bad_data", "best.fit is missing or NaN"
            
        # 2. best.point
        point = getattr(best, 'point', None)
        if point is None or (isinstance(point, np.ndarray) and np.isnan(point).any()):
            return "bad_data", "best.point is missing or contains NaN"
            
        # 3. error.obj_space
        obj_err = getattr(error, 'obj_space', None)
        if obj_err is None or (isinstance(obj_err, float) and np.isnan(obj_err)):
            return "bad_data", "error.obj_space is missing or NaN"
            
        # 4. runtime
        if isinstance(runtime, float) and np.isnan(runtime):
            return "bad_data", "runtime is NaN"
            
        # 5. convergence_array
        if not isinstance(conv_array, np.ndarray):
            return "bad_data", "convergence_array is not an array"
        if np.isnan(conv_array).any():
            return "bad_data", "convergence_array contains NaN"
            
    except Exception as e:
        return "bad_data", f"Data extraction error: {str(e)}"
        
    return "healthy", "OK"


# ── Selection Screen ───────────────────────────────────────────────

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
                    "🔍 [bold cyan]Experiment Deep Integrity Checker[/]",
                    id="sel-title",
                )
                yield Static(
                    "[dim]Select a parameter file to determine expected target count[/]", id="sel-sub"
                )
                yield OptionList(
                    *[Option(f, id=f) for f in self.param_files],
                    id="file-list",
                )
        yield Footer()

    @on(OptionList.OptionSelected)
    def on_selected(self, event: OptionList.OptionSelected) -> None:
        self.app.selected_param = event.option.id
        self.app.push_screen(CheckingScreen())


# ── Checking Screen ───────────────────────────────────────────────

class CheckingScreen(Screen):
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "app.pop_screen", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main"):
            with Vertical(id="left"):
                yield Static("[b]⚠️ Integrity Issues Log[/b]", id="left-hdr")
                yield RichLog(
                    id="file-log",
                    highlight=True,
                    markup=True,
                    wrap=False,
                    max_lines=3000,
                    auto_scroll=True,
                )
            with Vertical(id="right"):
                yield Static("[b]📊 Live Summary[/b]", id="right-hdr")
                yield Static("Loading parameter file…", id="params")
        with Vertical(id="bottom"):
            yield ProgressBar(id="pbar", total=100, show_eta=True)
            yield Static("Preparing…", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.run_check()

    @work(exclusive=True, thread=True)
    def run_check(self) -> None:
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
            "np": np
        }

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
            f"[bold]{total:,}[/] expected experiments  •  "
            f"Scanning [dim]{data_dir}[/]",
        )
        _time.sleep(0.4)

        missing = []
        corrupted = []
        bad_struct = []
        bad_data = []
        healthy = 0

        update_every = max(1, total // 400)
        advanced = 0
        batch_logs = []

        def update_summary_ui():
            lines = [
                "[bold]━━━ Integrity Report ━━━[/]\n",
                f"  [bold]Parameter file:[/]  [cyan]{param_file}[/]",
                f"  [bold]Data directory:[/]  [dim]{data_dir}[/]\n",
                f"  [bold]Total Expected:[/]  [white]{total:,}[/]\n",
                f"  [bold green]Healthy:[/]         {healthy:,}",
                f"  [bold yellow]Missing:[/]         {len(missing):,}",
                f"  [bold red]Corrupted (I/O):[/] {len(corrupted):,}",
                f"  [bold magenta]Bad Struct:[/]      {len(bad_struct):,}",
                f"  [bold orange1]Invalid Data:[/]    {len(bad_data):,}",
            ]
            self.app.call_from_thread(params_w.update, "\n".join(lines))

        for i in range(total):
            exp_id = i + 1
            fname = f"exp-{exp_id}.mat"
            fpath = os.path.join(data_dir, fname)

            status, msg = check_file(fpath)

            if status == "healthy":
                healthy += 1
            else:
                if status == "missing":
                    missing.append(exp_id)
                    batch_logs.append(f"[yellow]Missing:[/] {fname}")
                elif status == "corrupted":
                    corrupted.append((exp_id, msg))
                    batch_logs.append(f"[red]Corrupted:[/] {fname} - {msg}")
                elif status == "bad_struct":
                    bad_struct.append((exp_id, msg))
                    batch_logs.append(f"[magenta]Bad Struct:[/] {fname} - {msg}")
                elif status == "bad_data":
                    bad_data.append((exp_id, msg))
                    batch_logs.append(f"[orange1]Invalid Data:[/] {fname} - {msg}")

            should_update = ((i + 1) % update_every == 0) or (i == total - 1)
            if should_update:
                if batch_logs:
                    self.app.call_from_thread(flog.write, "\n".join(batch_logs))
                    batch_logs = []

                update_summary_ui()

                # Progress bar
                step = (i + 1) - advanced
                advanced = i + 1
                self.app.call_from_thread(pbar.advance, step)

                # Status bar
                pct = (i + 1) / total * 100
                self.app.call_from_thread(
                    status_w.update,
                    f"  [bold]{i+1:,}[/] / [bold]{total:,}[/]  │  "
                    f"[green]Healthy: {healthy:,}[/]  [red]Errors: {(len(missing)+len(corrupted)+len(bad_struct)+len(bad_data)):,}[/]  │  "
                    f"[cyan]{pct:.1f}%[/]",
                )

        # ── Final summary ────────────────────────────────────────
        update_summary_ui()
        if missing:
            ranges = compress_missing_ranges(missing)
            shown = ", ".join(ranges[:15])
            if len(ranges) > 15:
                shown += f" … +{len(ranges) - 15} more"
            self.app.call_from_thread(flog.write, f"\n[bold yellow]Missing ranges:[/] {shown}")
        
        if healthy == total:
            self.app.call_from_thread(flog.write, "\n[bold green]100% PERFECT INTEGRITY. All expected data is fully intact and readable.[/]")
            
        self.app.call_from_thread(
            status_w.update,
            f"  [bold green]✓ Scan Complete![/]  │  "
            f"[bold]{total:,}[/] checked  │  "
            f"[green]Healthy: {healthy:,}[/]",
        )


# ── App ────────────────────────────────────────────────────────────────

class IntegrityCheckerApp(App):
    TITLE = "Integrity Deep Checker"
    CSS = """
    Screen {
        background: $surface;
    }

    /* ── Selection ── */
    #sel-box {
        width: 64;
        height: auto;
        min-height: 10;
        max-height: 80vh;
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
        min-height: 3;
        max-height: 20;
        overflow-y: auto;
    }

    /* ── Checking ── */
    #main {
        height: 1fr;
    }
    #left {
        width: 2fr;
        min-width: 40;
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
        width: 1fr;
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
        description="Deep Integrity MAT Checker TUI"
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

    app = IntegrityCheckerApp(server_dir, data_dir, param_files)
    app.run()


if __name__ == "__main__":
    main()
