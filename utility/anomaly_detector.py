"""
Anomaly Detector — Textual TUI

Connects to the parallel experiment runner server and analyzes the completion
times of the experiments. It calculates the mean and standard deviation of
the durations and highlights statistical outliers (too fast or too slow).

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

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Footer,
    Header,
    ProgressBar,
    RichLog,
    Static,
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
                yield RichLog(
                    id="anomaly-log",
                    highlight=True,
                    markup=True,
                    wrap=False,
                    auto_scroll=True,
                )
            with Vertical(id="right"):
                yield Static("[b]📊 Statistics[/b]", id="right-hdr")
                yield Static("Initializing...", id="stats-panel")
        with Vertical(id="bottom"):
            yield ProgressBar(id="pbar", total=100, show_eta=True)
            yield Static("Checking server connection...", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.run_check()

    @work(exclusive=True, thread=True)
    def run_check(self) -> None:
        status_w = self.query_one("#status", Static)
        stats_panel = self.query_one("#stats-panel", Static)
        pbar = self.query_one("#pbar", ProgressBar)
        alog = self.query_one("#anomaly-log", RichLog)

        base_url = f"http://{self.app.host}:{self.app.port}"

        # 1. Check Connection
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

        durations = []
        fmt = "%Y-%m-%d %H:%M:%S"
        anomalies = []

        # 2. Fetch Data & Calculate Stats Continuously
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
                        durations.append(
                            {"index": i, "duration": duration, "data": data}
                        )

                # Progress updates
                self.app.call_from_thread(pbar.advance, 1)

                # Update stats panel every 10 items or at the end to save UI redraws
                if i % 10 == 0 or i == total_experiments:
                    if len(durations) > 1:
                        dur_vals = [d["duration"] for d in durations]
                        mean = statistics.mean(dur_vals)
                        stdev = statistics.stdev(dur_vals)

                        # Find new anomalies
                        threshold = 2 * stdev
                        lower_bound = max(0, mean - threshold)
                        upper_bound = mean + threshold

                        current_anomalies_count = 0
                        for item in durations:
                            d = item["duration"]
                            idx = item["index"]
                            if d < lower_bound or d > upper_bound:
                                current_anomalies_count += 1
                                # Log it if not logged before
                                if idx not in [a["index"] for a in anomalies]:
                                    anomalies.append(item)
                                    status_type = (
                                        "[red]Too Long[/red]"
                                        if d > upper_bound
                                        else "[blue]Too Short[/blue]"
                                    )
                                    msg = (
                                        f"[bold]Exp {idx}[/]: {d:.1f}s {status_type} "
                                        f"(Avg: {mean:.1f}s, σ: {stdev:.1f})"
                                    )
                                    self.app.call_from_thread(alog.write, msg)

                        stats_txt = (
                            f"[b]Sample Size:[/] {len(durations)}\n"
                            f"[b]Mean Duration:[/] {mean:.2f}s\n"
                            f"[b]Std Dev (σ):[/] {stdev:.2f}s\n"
                            f"[b]Bounds:[/] {lower_bound:.2f}s - {upper_bound:.2f}s\n\n"
                            f"[b]Anomalies:[/] {current_anomalies_count}"
                        )
                        self.app.call_from_thread(stats_panel.update, stats_txt)

                pct = i / total_experiments * 100
                self.app.call_from_thread(
                    status_w.update,
                    f"  [bold]{i:,}[/] / [bold]{total_experiments:,}[/] fetched  │  [cyan]{pct:.1f}%[/]",
                )

                # Throttle slightly to keep UI responsive
                _time.sleep(0.005)

            except Exception as e:
                self.app.call_from_thread(
                    alog.write, f"[red]Error fetching Exp {i}: {e}[/]"
                )

        # 3. Final summary
        self.app.call_from_thread(
            status_w.update,
            f"  [bold green]✓ Done![/]  │  [bold]{total_experiments:,}[/] total  │  "
            f"[yellow]{len(durations)}[/] valid times  │  [red]{len(anomalies)}[/] anomalies found",
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
    #left-hdr, #right-hdr {
        height: 1;
        padding: 0 1;
        background: $accent 15%;
        text-style: bold;
    }
    #anomaly-log {
        height: 1fr;
        border-right: thick $accent 30%;
        padding: 0 1;
        scrollbar-size: 1 1;
    }
    #right {
        width: 40;
    }
    #stats-panel {
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
