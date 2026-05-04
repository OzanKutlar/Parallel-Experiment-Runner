"""
Anomaly Detector — Textual TUI

Connects to the parallel experiment runner server and analyzes the completion
times of the experiments. It calculates the mean and standard deviation of
the durations and highlights statistical outliers (too fast or too slow).
It also groups the anomalies by their most common data parameters.

Now includes a Historical States tab to merge missing timestamps from
previous server sessions.

Usage:
    python anomaly_detector.py [--host 127.0.0.1] [--port 3753] [--states-dir ../server/states]
"""

import argparse
import glob
import json
import os
import statistics
import time as _time
import urllib.error
import urllib.request
from datetime import datetime

from textual import work, on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Footer,
    Header,
    ProgressBar,
    Static,
    Tree,
    TabbedContent,
    TabPane,
    OptionList,
    Button
)
from textual.widgets.option_list import Option


def format_duration(seconds: float) -> str:
    """Convert seconds to a human-readable Xh Xm Xs string."""
    if seconds < 0:
        return "N/A"
    total = int(round(seconds))
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    parts = []
    if h > 0:
        parts.append(f"{h}h")
    if m > 0:
        parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts) if parts else "0s"


class CheckingScreen(Screen):
    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial="tab-anomalies"):
            with TabPane("🔍 Anomaly Analysis", id="tab-anomalies"):
                with Horizontal(id="main"):
                    with Vertical(id="left"):
                        yield Static("[b]⚠️ Anomalies Found[/b]", id="left-hdr")
                        tree = Tree("Anomalies", id="anomaly-tree")
                        tree.root.expand()
                        yield tree
                    with Vertical(id="right"):
                        yield Static("[b]📊 Statistics[/b]", id="right-hdr")
                        yield Static("Initializing...", id="stats-panel")
                        yield Static("[b]🔍 Data Details[/b]", id="details-hdr")
                        yield Static("Click or use arrows to select an anomaly.", id="data-panel")
            
            with TabPane("💾 Historical States", id="tab-states"):
                with Horizontal(id="state-main"):
                    with Vertical(id="state-left"):
                        yield Static("[b]State Files[/b]", id="state-left-hdr")
                        yield OptionList(id="state-list")
                    with Vertical(id="state-right"):
                        yield Static("[b]State Details[/b]", id="state-right-hdr")
                        yield Static("Scanning for historical state files...", id="state-details")
                        yield Button("Merge This State", id="btn-merge", variant="success")

        with Vertical(id="bottom"):
            yield ProgressBar(id="pbar", total=100, show_eta=True)
            yield Static("Checking server connection...", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.all_data = []
        self.anomalies_list = []
        self.durations = []
        self.states_data = []
        self.mean = 0
        self.median = 0
        self.stdev = 0
        self.shortest = 0
        self.longest = 0
        self.run_check()

    @on(Tree.NodeSelected)
    @on(Tree.NodeHighlighted)
    def on_node_interaction(self, event) -> None:
        data_panel = self.query_one("#data-panel", Static)
        node_data = getattr(event.node, "data", None)
        if node_data:
            d = node_data.get("data", {})
            duration = node_data.get("duration", 0)
            idx = node_data.get("index", "?")

            lines = [f"[b]Experiment {idx}[/] - Duration: [yellow]{format_duration(duration)}[/]\n"]
            for k, v in d.items():
                if k not in ("id", "Taken At", "Completed At", "index"):
                    lines.append(f"[cyan]{k}[/]: {v}")

            lines.append("\n[dim]Timestamps:[/]")
            if "Taken At" in d:
                lines.append(f" Taken At: {d['Taken At']}")
            if "Completed At" in d:
                lines.append(f" Completed At: {d['Completed At']}")
            if node_data.get("historical_merge"):
                lines.append(" [green](Sourced from historical state file)[/]")

            data_panel.update("\n".join(lines))
        else:
            data_panel.update("Select a specific experiment below a group to view its data.")

    @on(OptionList.OptionSelected)
    @on(OptionList.OptionHighlighted)
    def on_state_interaction(self, event) -> None:
        details_panel = self.query_one("#state-details", Static)
        idx = event.option_index
        if 0 <= idx < len(self.states_data):
            state = self.states_data[idx]
            
            slot_txt = "[green]Yes[/green]" if state['slots_in'] else "[red]No[/red]"
            match_txt = "[green]Yes[/green]" if state['matches_total'] else "[red]No[/red]"
            
            lines = [
                f"[b]File:[/] {state['filename']}",
                f"[b]Path:[/] [dim]{state['path']}[/]\n",
                f"[b]Parameter File:[/] [cyan]{state['param_file']}[/]",
                f"[b]Total Items:[/] {state['total_items']}",
                f"[b]Completed Items:[/] {state['completed_count']}",
                f"[b]Stopped at ID:[/] {state['max_completed_index'] + 1} (0-indexed: {state['max_completed_index']})",
                f"[b]Timing Entries Available:[/] {state['timing_entries']}\n",
                f"[b]Slots In (Matches Live PRE count)?[/] {slot_txt}",
                f"[b]Matches Total Live Experiments?[/] {match_txt}"
            ]
            
            if state.get('is_merged'):
                lines.append(f"\n[b]Timings Merged into Live Analysis:[/] [bold yellow]{state['merged_count']}[/]")
            
            if state['slots_in']:
                lines.append("\n[dim]💡 This state perfectly aligns with where the live server resumed processing.[/]")
            elif state['matches_total']:
                lines.append("\n[dim]💡 This state matches the parameter space size of the live server.[/]")
                
            details_panel.update("\n".join(lines))
            
            btn = self.query_one("#btn-merge", Button)
            btn.display = True
            btn.disabled = state.get('is_merged', False) or state['timing_entries'] == 0

    @on(Button.Pressed, "#btn-merge")
    def on_merge_pressed(self, event: Button.Pressed) -> None:
        state_list = self.query_one("#state-list", OptionList)
        idx = state_list.highlighted
        if idx is None or idx < 0 or idx >= len(self.states_data):
            return
            
        state = self.states_data[idx]
        if state.get("is_merged") or state["timing_entries"] == 0:
            return
            
        merged_count = 0
        for idx_str, t_info in state["raw_timing"].items():
            try:
                i = int(idx_str)
                if 0 <= i < len(self.all_data):
                    if "Completed At" not in self.all_data[i] and "Completed At" in t_info:
                        self.all_data[i]["Taken At"] = t_info.get("Taken At")
                        self.all_data[i]["Completed At"] = t_info.get("Completed At")
                        self.all_data[i]["historical_merge"] = True
                        merged_count += 1
            except ValueError:
                continue
                
        state["merged_count"] = merged_count
        state["is_merged"] = True
        
        # Update Option List visual by rebuilding it
        options = []
        for i, s in enumerate(self.states_data):
            if s.get("is_merged"):
                marker = "[green]★[/]"
                label = f"{marker} {s['filename']} ({s['merged_count']} merged)"
            else:
                marker = "[dim]○[/]"
                label = f"{marker} {s['filename']}"
            options.append(Option(label, id=f"state-{i}"))
            
        state_list.clear_options()
        state_list.add_options(options)
        state_list.highlighted = idx
        
        # Re-trigger interaction to update details & disable button
        self.on_state_interaction(OptionList.OptionHighlighted(state_list, idx))
        
        # Re-process
        self.process_data()

    def group_anomalies(self, anomalies, normal_runs):
        anom_freq = {}
        norm_freq = {}
        
        for a in anomalies:
            for k, v in a["data"].items():
                if k in ("id", "Taken At", "Completed At", "index"):
                    continue
                pair = (k, str(v))
                anom_freq[pair] = anom_freq.get(pair, 0) + 1
                
        for n in normal_runs:
            for k, v in n["data"].items():
                if k in ("id", "Taken At", "Completed At", "index"):
                    continue
                pair = (k, str(v))
                norm_freq[pair] = norm_freq.get(pair, 0) + 1

        groups = {}
        for a in anomalies:
            best_pair = None
            best_score = -1

            for k, v in a["data"].items():
                if k in ("id", "Taken At", "Completed At", "index"):
                    continue
                pair = (k, str(v))
                a_count = anom_freq[pair]
                n_count = norm_freq.get(pair, 0)
                
                # Exclusivity ratio: 1.0 means it ONLY happens in anomalies
                ratio = a_count / (a_count + n_count) if (a_count + n_count) > 0 else 0
                
                # Heavily weight high exclusivity, break ties with higher occurrence count
                score = (ratio * 10000) + a_count

                if score > best_score:
                    best_score = score
                    best_pair = pair

            if best_pair:
                group_name = f"{best_pair[0]} = {best_pair[1]} (Anomalous: {anom_freq[best_pair]}, Normal: {norm_freq.get(best_pair, 0)})"
            else:
                group_name = "Unique / Uncategorized"

            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(a)

        return dict(sorted(groups.items(), key=lambda item: len(item[1]), reverse=True))

    def update_tree(self, anomalies, normal_runs):
        tree = self.query_one("#anomaly-tree", Tree)
        tree.clear()

        groups = self.group_anomalies(anomalies, normal_runs)

        for group_name, group_items in groups.items():
            group_node = tree.root.add(f"[b]{group_name}[/]", expand=True)
            for item in group_items:
                idx = item["index"]
                d = item["duration"]

                status = "[red]Too Long[/red]" if d > self.mean else "[blue]Too Short[/blue]"
                label = f"Exp {idx}: {format_duration(d)} {status}"
                group_node.add_leaf(label, data=item)

    @work(exclusive=True, thread=True)
    def run_check(self) -> None:
        status_w = self.query_one("#status", Static)
        stats_panel = self.query_one("#stats-panel", Static)
        pbar = self.query_one("#pbar", ProgressBar)

        base_url = f"http://{self.app.host}:{self.app.port}"

        # 1. Check connection & get total
        try:
            req = urllib.request.Request(f"{base_url}/getNum")
            with urllib.request.urlopen(req, timeout=5) as response:
                total_experiments = int(response.read().decode())
        except Exception as e:
            self.app.call_from_thread(
                status_w.update,
                f"[bold red]✗ Could not connect to server at {base_url}[/]",
            )
            self.app.call_from_thread(
                stats_panel.update,
                f"[red]Error: {str(e)}[/]\nAre you sure the server is running?",
            )
            return

        if total_experiments == 0:
            self.app.call_from_thread(
                status_w.update, "[bold yellow]! Connected, but 0 experiments found.[/]"
            )
            return
            
        # 2. Get Live PRE count by querying /status history
        live_pre_count = 0
        try:
            req = urllib.request.Request(f"{base_url}/status", headers={"lastLog": "-1"})
            with urllib.request.urlopen(req, timeout=10) as response:
                logs = json.loads(response.read().decode())
                # Count how many logs were sent to PRE (indicating they were loaded from disk on startup)
                live_pre_count = sum(1 for log in logs if log.get("sentTo") == "PRE")
        except Exception:
            pass

        self.app.call_from_thread(
            status_w.update,
            f"  [green]✓ Connected[/]  •  [bold]{total_experiments:,}[/] experiments  •  Fetching batch data…",
        )

        # 3. Fetch all data in one batch request
        try:
            req = urllib.request.Request(f"{base_url}/batchInfo")
            with urllib.request.urlopen(req, timeout=30) as response:
                all_data = json.loads(response.read().decode())
        except Exception as e:
            self.app.call_from_thread(
                status_w.update,
                f"[bold red]✗ Failed to fetch batch data: {e}[/]",
            )
            return
            
        # 4. Load and process historical states to merge missing timestamps
        self.app.call_from_thread(status_w.update, "  Parsing Historical States...")
        states_dir = self.app.states_dir
        state_files = sorted(glob.glob(os.path.join(states_dir, "state_*.json")), reverse=True)
        
        state_options = []
        
        for fpath in state_files:
            try:
                with open(fpath, 'r') as f:
                    s_data = json.load(f)
                
                comp_arr = s_data.get("completed_array", [])
                total_items = len(comp_arr)
                completed_count = sum(1 for c in comp_arr if c)
                
                max_completed = -1
                for i in range(len(comp_arr)-1, -1, -1):
                    if comp_arr[i]:
                        max_completed = i
                        break
                        
                timing_info = s_data.get("timing_info", {})
                
                state_dict = {
                    "path": fpath,
                    "filename": os.path.basename(fpath),
                    "param_file": s_data.get("data_file", "Unknown"),
                    "total_items": total_items,
                    "completed_count": completed_count,
                    "max_completed_index": max_completed,
                    "timing_entries": len(timing_info),
                    "raw_timing": timing_info
                }
                
                # Evaluate match / slot in
                slots_in = (max_completed == live_pre_count - 1 and live_pre_count > 0)
                matches_total = (total_items == total_experiments)
                
                state_dict["slots_in"] = slots_in
                state_dict["matches_total"] = matches_total
                
                # Merge logic (Manual, default 0)
                state_dict["merged_count"] = 0
                state_dict["is_merged"] = False
                self.states_data.append(state_dict)
                
                marker = "[dim]○[/]"
                state_options.append(Option(f"{marker} {state_dict['filename']}", id=f"state-{len(self.states_data)-1}"))
                
            except Exception:
                continue
                
        if state_options:
            state_list = self.query_one("#state-list", OptionList)
            self.app.call_from_thread(state_list.add_options, state_options)

        self.all_data = all_data
        self.process_data()

    @work(exclusive=True, thread=True)
    def process_data(self) -> None:
        status_w = self.query_one("#status", Static)
        stats_panel = self.query_one("#stats-panel", Static)
        pbar = self.query_one("#pbar", ProgressBar)
        
        self.durations.clear()
        self.anomalies_list.clear()

        # 5. Parse durations
        self.app.call_from_thread(setattr, pbar, "progress", 0)
        self.app.call_from_thread(setattr, pbar, "total", len(self.all_data))
        self.app.call_from_thread(
            status_w.update,
            f"  [green]✓ Data Ready[/]  •  [bold]{len(self.all_data):,}[/] experiments  •  Analyzing durations…",
        )

        fmt = "%Y-%m-%d %H:%M:%S"
        batch_size = max(500, len(self.all_data) // 50)
        advanced = 0
        
        for i, data in enumerate(self.all_data):
            idx = data.get("index", i + 1)
            
            if idx >= getattr(self.app, 'start_index', 0):
                if "Taken At" in data and "Completed At" in data:
                    try:
                        start_time = datetime.strptime(data["Taken At"], fmt)
                        end_time = datetime.strptime(data["Completed At"], fmt)
                        duration = (end_time - start_time).total_seconds()
                        if duration > 0:
                            self.durations.append(
                                {
                                    "index": idx,
                                    "duration": duration,
                                    "data": data,
                                    "historical_merge": data.get("historical_merge", False)
                                }
                            )
                    except Exception:
                        pass

            advanced += 1
            if advanced >= batch_size or i == len(self.all_data) - 1:
                self.app.call_from_thread(pbar.advance, advanced)
                pct = (i + 1) / len(self.all_data) * 100
                self.app.call_from_thread(
                    status_w.update,
                    f"  Parsing [bold]{i + 1:,}[/] / [bold]{len(self.all_data):,}[/]  │  [cyan]{pct:.1f}%[/]",
                )
                advanced = 0

        # 6. Compute statistics & find anomalies
        if len(self.durations) < 2:
            self.app.call_from_thread(
                status_w.update,
                f"[bold yellow]! Only {len(self.durations)} valid timing(s) found — not enough to detect anomalies.[/]",
            )
            return

        dur_vals = [d["duration"] for d in self.durations]
        self.mean = statistics.mean(dur_vals)
        self.median = statistics.median(dur_vals)
        self.stdev = statistics.stdev(dur_vals)
        self.shortest = min(dur_vals)
        self.longest = max(dur_vals)

        threshold = 2 * self.stdev
        lower_bound = max(0, self.mean - threshold)
        upper_bound = self.mean + threshold

        normal_runs = []
        for item in self.durations:
            d = item["duration"]
            if d < lower_bound or d > upper_bound:
                self.anomalies_list.append(item)
            else:
                normal_runs.append(item)

        # 7. Update UI with final results
        stats_txt = (
            f"[b]Sample Size:[/] {len(self.durations)}\n"
            f"[b]Shortest Run:[/] {format_duration(self.shortest)}\n"
            f"[b]Longest Run:[/] {format_duration(self.longest)}\n"
            f"[b]Mean Duration:[/] {format_duration(self.mean)}\n"
            f"[b]Median Duration:[/] {format_duration(self.median)}\n"
            f"[b]Std Dev (σ):[/] {format_duration(self.stdev)}\n"
            f"[b]Bounds:[/] {format_duration(lower_bound)} - {format_duration(upper_bound)}\n\n"
            f"[b]Anomalies:[/] {len(self.anomalies_list)}"
        )
        self.app.call_from_thread(stats_panel.update, stats_txt)
        self.app.call_from_thread(self.update_tree, self.anomalies_list.copy(), normal_runs)

        self.app.call_from_thread(
            status_w.update,
            f"  [bold green]✓ Done![/]  │  [bold]{len(self.all_data):,}[/] total  │  "
            f"[yellow]{len(self.durations)}[/] valid times  │  [red]{len(self.anomalies_list)}[/] anomalies found"
        )


class AnomalyDetectorApp(App):
    TITLE = "Anomaly Detector"
    CSS = """
    Screen {
        background: $surface;
    }

    #main, #state-main {
        height: 1fr;
    }
    #left, #state-left {
        width: 1fr;
        min-width: 30;
        border-right: thick $accent 30%;
    }
    #left-hdr, #right-hdr, #details-hdr, #state-left-hdr, #state-right-hdr {
        height: 1;
        padding: 0 1;
        background: $accent 15%;
        text-style: bold;
    }
    #anomaly-tree {
        height: 1fr;
        padding: 0 1;
        scrollbar-size: 1 1;
    }
    #state-list {
        height: 1fr;
        padding: 0 1;
    }
    #right, #state-right {
        width: 2fr;
    }
    #stats-panel {
        height: auto;
        min-height: 8;
        padding: 1 2;
    }
    #data-panel, #state-details {
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
    #btn-merge {
        margin: 1 2;
        display: none;
    }
    """

    def __init__(self, host, port, start_index, states_dir):
        super().__init__()
        self.host = host
        self.port = port
        self.start_index = start_index
        self.states_dir = states_dir

    def on_mount(self) -> None:
        self.push_screen(CheckingScreen())


def main():
    parser = argparse.ArgumentParser(description="Anomaly Detector TUI")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=3753, help="Server port")
    parser.add_argument("--start-index", type=int, default=0, help="Minimum index to consider for anomalies")
    
    # Default to ../server/states relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_states = os.path.normpath(os.path.join(script_dir, "..", "server", "states"))
    parser.add_argument("--states-dir", type=str, default=default_states, help="Path to the historical states directory")
    
    args = parser.parse_args()

    app = AnomalyDetectorApp(args.host, args.port, args.start_index, args.states_dir)
    app.run()


if __name__ == "__main__":
    main()
