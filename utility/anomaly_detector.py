"""
Anomaly Detector — Textual TUI

Connects to the parallel experiment runner server and analyzes the completion
times of the experiments. It calculates the mean and standard deviation of
the durations and highlights statistical outliers (too fast or too slow).
It also groups the anomalies by their most common data parameters.

Usage:
    python anomaly_detector.py [--host 127.0.0.1] [--port 3753]
"""

import argparse
import json
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
)


class CheckingScreen(Screen):
    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
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
                yield Static("Click an anomaly in the tree to see its parameters.", id="data-panel")
        with Vertical(id="bottom"):
            yield ProgressBar(id="pbar", total=100, show_eta=True)
            yield Static("Checking server connection...", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.anomalies_list = []
        self.durations = []
        self.mean = 0
        self.stdev = 0
        self.run_check()

    @on(Tree.NodeSelected)
    def on_node_selected(self, event: Tree.NodeSelected) -> None:
        data_panel = self.query_one("#data-panel", Static)
        node_data = event.node.data
        if node_data:
            # It's an anomaly leaf node
            d = node_data.get("data", {})
            duration = node_data.get("duration", 0)
            idx = node_data.get("index", "?")
            
            lines = [f"[b]Experiment {idx}[/] - Duration: [yellow]{duration:.2f}s[/]\n"]
            for k, v in d.items():
                if k not in ("id", "Taken At", "Completed At"):
                    lines.append(f"[cyan]{k}[/]: {v}")
                    
            lines.append("\n[dim]Timestamps:[/]")
            if "Taken At" in d:
                lines.append(f" Taken At: {d['Taken At']}")
            if "Completed At" in d:
                lines.append(f" Completed At: {d['Completed At']}")
                
            data_panel.update("\n".join(lines))
        else:
            # Root or group node
            data_panel.update("Select a specific experiment below a group to view its data.")

    def group_anomalies(self, anomalies):
        freq = {}
        for a in anomalies:
            data = a["data"]
            for k, v in data.items():
                if k in ("id", "Taken At", "Completed At"):
                    continue
                pair = (k, str(v))
                freq[pair] = freq.get(pair, 0) + 1
                
        groups = {}
        for a in anomalies:
            data = a["data"]
            best_pair = None
            best_count = 1
            
            for k, v in data.items():
                if k in ("id", "Taken At", "Completed At"):
                    continue
                pair = (k, str(v))
                if freq[pair] > best_count:
                    best_count = freq[pair]
                    best_pair = pair
                    
            if best_pair:
                group_name = f"{best_pair[0]} = {best_pair[1]}"
            else:
                group_name = "Unique / Uncategorized"
                
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(a)
            
        # Sort groups by size (descending)
        return dict(sorted(groups.items(), key=lambda item: len(item[1]), reverse=True))

    def update_tree(self, anomalies):
        tree = self.query_one("#anomaly-tree", Tree)
        tree.clear()
        
        groups = self.group_anomalies(anomalies)
        
        for group_name, group_items in groups.items():
            group_node = tree.root.add(f"[b]{group_name}[/] ({len(group_items)})", expand=True)
            for item in group_items:
                idx = item["index"]
                d = item["duration"]
                
                status = "[red]Too Long[/red]" if d > self.mean else "[blue]Too Short[/blue]"
                label = f"Exp {idx}: {d:.1f}s {status}"
                group_node.add_leaf(label, data=item)


    @work(exclusive=True, thread=True)
    def run_check(self) -> None:
        status_w = self.query_one("#status", Static)
        stats_panel = self.query_one("#stats-panel", Static)
        pbar = self.query_one("#pbar", ProgressBar)

        base_url = f"http://{self.app.host}:{self.app.port}"

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

        self.app.call_from_thread(setattr, pbar, "total", total_experiments)
        self.app.call_from_thread(
            status_w.update,
            f"  [green]✓ Connected[/]  •  [bold]{total_experiments:,}[/] experiments to check.",
        )

        fmt = "%Y-%m-%d %H:%M:%S"

        for i in range(1, total_experiments + 1):
            try:
                req = urllib.request.Request(f"{base_url}/info")
                req.add_header("index", str(i))
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())

                if "Taken At" in data and "Completed At" in data:
                    start_time = datetime.strptime(data["Taken At"], fmt)
                    end_time = datetime.strptime(data["Completed At"], fmt)
                    duration = (end_time - start_time).total_seconds()

                    if duration > 0:
                        self.durations.append(
                            {"index": i, "duration": duration, "data": data}
                        )

                self.app.call_from_thread(pbar.advance, 1)

                if i % 10 == 0 or i == total_experiments:
                    if len(self.durations) > 1:
                        dur_vals = [d["duration"] for d in self.durations]
                        self.mean = statistics.mean(dur_vals)
                        self.stdev = statistics.stdev(dur_vals)

                        threshold = 2 * self.stdev
                        lower_bound = max(0, self.mean - threshold)
                        upper_bound = self.mean + threshold

                        new_anomalies = False
                        for item in self.durations:
                            d = item["duration"]
                            idx = item["index"]
                            if d < lower_bound or d > upper_bound:
                                if idx not in [a["index"] for a in self.anomalies_list]:
                                    self.anomalies_list.append(item)
                                    new_anomalies = True

                        if new_anomalies:
                            self.app.call_from_thread(self.update_tree, self.anomalies_list.copy())

                        stats_txt = (
                            f"[b]Sample Size:[/] {len(self.durations)}\n"
                            f"[b]Mean Duration:[/] {self.mean:.2f}s\n"
                            f"[b]Std Dev (σ):[/] {self.stdev:.2f}s\n"
                            f"[b]Bounds:[/] {lower_bound:.2f}s - {upper_bound:.2f}s\n\n"
                            f"[b]Anomalies:[/] {len(self.anomalies_list)}"
                        )
                        self.app.call_from_thread(stats_panel.update, stats_txt)

                pct = i / total_experiments * 100
                self.app.call_from_thread(
                    status_w.update,
                    f"  [bold]{i:,}[/] / [bold]{total_experiments:,}[/] fetched  │  [cyan]{pct:.1f}%[/]",
                )

                _time.sleep(0.005)

            except Exception as e:
                # Silently skip on error to allow the loop to continue
                pass

        self.app.call_from_thread(
            status_w.update,
            f"  [bold green]✓ Done![/]  │  [bold]{total_experiments:,}[/] total  │  "
            f"[yellow]{len(self.durations)}[/] valid times  │  [red]{len(self.anomalies_list)}[/] anomalies found",
        )


class AnomalyDetectorApp(App):
    TITLE = "Anomaly Detector"
    CSS = """
    Screen {
        background: $surface;
    }

    #main {
        height: 1fr;
    }
    #left {
        width: 1fr;
        min-width: 30;
    }
    #left-hdr, #right-hdr, #details-hdr {
        height: 1;
        padding: 0 1;
        background: $accent 15%;
        text-style: bold;
    }
    #anomaly-tree {
        height: 1fr;
        border-right: thick $accent 30%;
        padding: 0 1;
        scrollbar-size: 1 1;
    }
    #right {
        width: 45;
    }
    #stats-panel {
        height: auto;
        min-height: 8;
        padding: 1 2;
    }
    #data-panel {
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

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port

    def on_mount(self) -> None:
        self.push_screen(CheckingScreen())


def main():
    parser = argparse.ArgumentParser(description="Anomaly Detector TUI")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=3753, help="Server port")
    args = parser.parse_args()

    app = AnomalyDetectorApp(args.host, args.port)
    app.run()


if __name__ == "__main__":
    main()
