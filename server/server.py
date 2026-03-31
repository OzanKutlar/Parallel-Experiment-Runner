from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
import json
import os
import time
import sys
import threading
import base64
import numpy as np
import socket
import argparse
import glob
from datetime import datetime
from textual.app import App, ComposeResult
from textual.widgets import RichLog, Input, Static
from textual.containers import Horizontal, Vertical

# Server settings
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 3753
STATE_FILE = "experiment_state.json"
class Experimenter:
    def __init__(self):
        self.data_array = []
        self.completed_array = []
        self.givenToPC = []
        self.data_index = []
        self.logs = []
        self.stateLogs = []
        self.lock = threading.Lock() # Thread lock for safety
        self.data_file_name = None

        if not os.path.exists('states'):
            os.makedirs('states')
            
        self.state_file = f"states/state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        self._state_dirty = False
        self._last_save_time = 0
        self.auto_save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)

    def start_auto_save(self):
        self.auto_save_thread.start()

    def _auto_save_loop(self):
        """Runs in the background and saves state every 5 seconds if dirty."""
        while True:
            time.sleep(1)
            if self._state_dirty:
                if time.time() - self._last_save_time >= 5:
                    with self.lock:
                        if len(self.data_array) > 0:
                            self.save_state()
                            self._state_dirty = False
                            self._last_save_time = time.time()

    def save_state(self):
        """Persist current state to disk."""
        try:
            if not self.data_array:
                return
            # Extract timing info from data_array to persist it
            timing_info = {}
            for i, item in enumerate(self.data_array):
                info = {}
                if 'Taken At' in item:
                    info['Taken At'] = item['Taken At']
                if 'Completed At' in item:
                    info['Completed At'] = item['Completed At']
                if info:
                    timing_info[str(i)] = info

            state = {
                "data_file": self.data_file_name,
                "completed_array": self.completed_array,
                "givenToPC": self.givenToPC,
                "data_index": self.data_index,
                "logs": self.logs,
                "stateLogs": self.stateLogs,
                "timing_info": timing_info
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"Error saving state: {e}")

    def load_state(self, file_path):
        """Load state from disk."""
        if not os.path.exists(file_path):
            return False
        
        try:
            with open(file_path, 'r') as f:
                state = json.load(f)
            
            # validation to ensure loaded state matches loaded data size
            if len(self.data_array) > 0:
                # Basic validation
                pass 

            self.completed_array = state.get("completed_array", [])
            self.givenToPC = state.get("givenToPC", [])
            self.data_index = state.get("data_index", [0])
            self.logs = state.get("logs", [])
            self.stateLogs = state.get("stateLogs", [])

            # Restore timing info to data_array
            timing_info = state.get("timing_info", {})
            for idx_str, info in timing_info.items():
                try:
                    idx = int(idx_str)
                    if 0 <= idx < len(self.data_array):
                        self.data_array[idx].update(info)
                except ValueError:
                    pass

            print(f"State loaded from {file_path}")
            return True
        except Exception as e:
            print(f"Error loading state: {e}")
            return False

    def stateLog(self, newState, index, sentTo="Null"):
        self.stateLogs.append({"state": newState, "index": index, "ID": len(self.stateLogs), "sentTo": sentTo})
    
    def getExperiment(self, ID, computer_name):
        with self.lock:
            last = self.data_index.pop()
            
            if not self.data_index:
                self.data_index.append(last + 1)
            
            if(ID != '-1'):
                # Ensure array bounds
                if int(ID) - 1 < len(self.completed_array):
                    if(not self.completed_array[int(ID) - 1]):
                        self.stateLog("Reset", int(ID))
                        print(f"Resetting data {int(ID) + 1} for {computer_name} due to new request.")
                        log(f"Reset index {int(ID) + 1} by {computer_name}")
                        self.data_index.append(int(ID))
                        self.givenToPC[int(ID)] = 'Reset'
                        self.completed_array[int(ID)] = False
                    
            if last < len(self.data_array):
                self.data_array[last]['Taken At'] = time.strftime('%Y-%m-%d %H:%M:%S')
                response_data = self.data_array[last]
                
                # Expand tracking arrays if necessary
                while len(self.givenToPC) <= last:
                    self.givenToPC.append("Null")
                while len(self.completed_array) <= last:
                    self.completed_array.append(False)

                self.givenToPC[last] = computer_name
                self.completed_array[last] = False
                self._state_dirty = True
                
                self.stateLog("Running", last + 1, computer_name)
                display_colored_array(self.data_array)
                log(f"Sent Data on index {last + 1} to {computer_name}")
                print(f"Data {last+1} has been sent to {computer_name}")
            else:
                response_data = {"message": "No more data left."}
                log(f"Shutting down {computer_name}")
                print(f'Data Distribution is finished. Extra connections : ', (last - len(self.data_array)))
            
            return response_data
    
    def complete(self, ID, computer_name):
        with self.lock:
            self.stateLog("Finished", int(ID), computer_name)
            print("ID " + ID + " is finished.")
            
            index = int(ID) - 1
            
            if 0 <= index < len(self.data_array):
                self.data_array[index]['Completed At'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            if index >= len(self.completed_array):
                self.completed_array.extend([False] * (index + 1 - len(self.completed_array)))
            
            self.completed_array[index] = True
            self._state_dirty = True

    def reset(self, index):
        with self.lock:
            self.stateLog("Reset", index + 1)
            log(f"Reset index {index + 1} from terminal.")
            self.data_index.append(index)
            
            # Expand if necessary (though reset usually implies it existed)
            while len(self.givenToPC) <= index:
                self.givenToPC.append("Null")
            while len(self.completed_array) <= index:
                self.completed_array.append(False)

            self.givenToPC[index] = 'Reset'
            self.completed_array[index] = False
            self._state_dirty = True
            
    def calculate_time_stats(self):
        fmt = '%Y-%m-%d %H:%M:%S'
        durations = []
        
        with self.lock:
            # 1. Calculate Active Workers
            active_workers = 0
            for i, pc in enumerate(self.givenToPC):
                if i < len(self.completed_array):
                    is_working = (pc != "Null" and pc != "Reset" and pc != "PRE")
                    is_not_done = not self.completed_array[i]
                    if is_working and is_not_done:
                        active_workers += 1

            # 2. Collect durations from ALL completed tasks
            # We look for tasks that have both a 'Taken At' and 'Completed At' timestamp
            for i, completed in enumerate(self.completed_array):
                if completed:
                    item = self.data_array[i]
                    if 'Taken At' in item and 'Completed At' in item:
                        try:
                            start_time = datetime.strptime(item['Taken At'], fmt)
                            end_time = datetime.strptime(item['Completed At'], fmt)
                            duration = (end_time - start_time).total_seconds()
                            
                            # Sanity check: ensure duration is positive
                            if duration > 0:
                                durations.append(duration)
                        except Exception:
                            continue

            # 3. Calculate Stats
            total_tasks = len(self.data_array)
            finished_tasks = self.completed_array.count(True)
            remaining = total_tasks - finished_tasks
            
            eta_seconds = 0
            
            # We need at least one finished task to calculate average, 
            # and at least one active worker to process the remaining ones.
            if len(durations) > 0 and active_workers > 0:
                # Average wall-clock time it takes for a SINGLE worker to finish ONE task
                avg_duration_per_task = sum(durations) / len(durations)
                
                # System throughput: How many seconds does the SYSTEM take to finish one task?
                # If 1 task takes 100s, but we have 10 workers, the system finishes a task every 10s.
                system_seconds_per_task = avg_duration_per_task / active_workers
                
                eta_seconds = remaining * system_seconds_per_task

            return {
                "eta_seconds": eta_seconds,
                "remaining": remaining,
                "window_tasks": len(durations), # Using this to tell UI we have N samples
                "active_workers": active_workers
            }


experimenter = Experimenter()






RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
Blue = "\033[34m"
Magenta = "\033[35m"
Cyan = "\033[36m"
RESET = "\033[0m"


ROWS_PER_COLUMN = 20  # Number of rows that fit into a single terminal column
COLUMN_DIST = 30

def log(text):
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    # Logs are append-only, thread safe enough for this purpose
    experimenter.logs.append({"Text": text, "ID": len(experimenter.logs), "time": current_time})

    

class HTTPHandler(BaseHTTPRequestHandler):
    global experimenter
    
    def log_message(self, format, *args):
        pass  # This disables the default logging
    
    def do_GET(self):
        global experimenter
        
        if self.path == "/getNum":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(str(len(experimenter.data_array)).encode())
            return
        
        if self.path == "/timeStats":
            stats = experimenter.calculate_time_stats()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode())
            return
        
        
        if self.path == "/logs":
            last_log = int(self.headers.get('lastLog', len(experimenter.logs) - 6))
            if(last_log <= len(experimenter.logs) - 6):
                relevant_logs = experimenter.logs[-30:]
            else:
                relevant_logs = experimenter.logs[last_log+1:last_log+5]
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(relevant_logs).encode())
            return
            
        if self.path == "/status":
            last_log = int(self.headers.get('lastLog', len(experimenter.logs) - 6))
            relevant_logs = experimenter.stateLogs[last_log+1:]
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(relevant_logs).encode())
            return
            
        if self.path == "/info":
            index = int(self.headers.get('index', 0)) - 1
            response = experimenter.data_array[index] if 0 <= index < len(experimenter.data_array) else {"text": "Invalid ID"}
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())
            return

        if self.path == "/batchInfo":
            with experimenter.lock:
                batch = []
                for i, item in enumerate(experimenter.data_array):
                    entry = {"index": i + 1}
                    entry.update(item)
                    batch.append(entry)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(batch).encode())
            return
            
        if self.path == "/reset":
            index = int(self.headers.get('index', 0)) - 1
            response = {"text": "Reset Success"} if 0 <= index < len(experimenter.data_array) else {"text": "Invalid ID"}
            
            # Use the thread-safe reset method instead of direct access
            if 0 <= index < len(experimenter.data_array):
                print(f"Resetting data {index + 1} because of webpage.")
                log(f"Reset index {index + 1} from webpage")
                experimenter.reset(index)
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())
            return

        
        computer_name = self.headers.get('ComputerName', 'Admin')
        ID = self.headers.get('ID', '-1')
        
        response_data = experimenter.getExperiment(ID, computer_name)
        
        response_json = json.dumps(response_data)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(response_json.encode('utf-8'))

    def do_POST(self):
        # try:
            computer_name = self.headers.get('ComputerName', 'Null')
            ID = self.headers.get('ID', '-1')
            if(ID != '-1'):
                experimenter.complete(ID, computer_name)
                
            content_length = int(self.headers['Content-Length'])
            if content_length <= 0:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"No content received.")
                return

            post_data = self.rfile.read(content_length).decode('utf-8')
            json_data = json.loads(post_data)

            file_name = json_data.get('file_name')
            file_content_base64 = json_data.get('file')
            
            if not os.path.exists("data"):
                os.makedirs("data")

            if not file_name or not file_content_base64:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing 'file_name' or 'file' in JSON payload")
                return

            try:
                file_content = base64.b64decode(file_content_base64)
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid Base64 content in 'file'")
                return

            with open("data/" + file_name, 'wb') as f:
                f.write(file_content)

            display_colored_array(experimenter.data_array)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"File uploaded and saved successfully")

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, lastLog, index')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()


# ChatGPT generated this. When an input object with arrays for parameters is given in,
# It generates all combinations of those parameters as seperate objects.
def generate_combinations(input_obj, id_counter):
    keys = list(input_obj.keys())
    values = list(input_obj.values())

    def combine(index, current_combination):
        nonlocal id_counter
        
        if index == len(keys):
            current_combination['id'] = id_counter
            result.append(current_combination.copy())
            id_counter += 1
            return

        for value in values[index]:
            current_combination[keys[index]] = value
            combine(index + 1, current_combination)
    
    result = []
    combine(0, {})
    return [result, id_counter]



def display_object_attributes(arr):
    for obj in arr:
        print()
        for attribute, value in obj.items():
            print(f"  {attribute}: {value}")
        print()



def merge_objects(dict1, dict2): 
    merged = dict1.copy() 
    merged.update(dict2) 
    return merged
    

def generate_combined_data(shared_params, id_counter, *param_sets):
    combined_data_array = []

    for params in param_sets:
        temp_data_array, id_counter = generate_combinations(merge_objects(shared_params, params), id_counter)
        combined_data_array += temp_data_array

    return combined_data_array, id_counter


def print_list_as_json(lst):
    json_str = json.dumps(lst, indent=4)
    with open("listJson.json", "w") as file:
        file.write(json_str)
   
def display_colored_array(data_array):
    return
    # Visualization logic omitted for brevity as per original file
   
def start_server(server, port):
    log("Server Started")
    print(f"Server running on {server.server_address[0]}:{port}")
    server.serve_forever()

def check_missing_files(directory, max_number):
    missing_count = 0
    lastNonMissing = -1
    for i in range(1, max_number + 1):
        file_name = f"exp-{i}.mat"
        file_path = os.path.join(directory, file_name)
        if not os.path.isfile(file_path):
            missing_count += 1
        else:
            lastNonMissing = i
       
    print(f"Last Index found on disk: {lastNonMissing}")
    
    experimenter.data_index.append(lastNonMissing)
    if(experimenter.data_index[-1] < 0):
        experimenter.data_index[-1] = 0
    
    # Mark everything up to last found file as complete
    # Using direct access here for bulk initialization before server start
    while len(experimenter.completed_array) < experimenter.data_index[-1]:
        experimenter.completed_array.append(True)
        experimenter.givenToPC.append("PRE")
        
    for i in range(0, experimenter.data_index[-1]):
        experimenter.completed_array[i] = True
        experimenter.givenToPC[i] = "PRE"
        experimenter.stateLog("Finished", i + 1, "PRE")

    # Double check gaps
    for i in range(1, lastNonMissing):
        file_name = f"exp-{i}.mat"
        file_path = os.path.join(directory, file_name)
        if not os.path.isfile(file_path):
            experimenter.reset(i-1) # reset uses 0-based index


class ServerApp(App):
    CSS = """
    #left-pane {
        width: 65%;
        height: 100%;
        border-right: solid green;
    }
    #right-pane {
        width: 35%;
        height: 100%;
    }
    #log-view {
        height: 1fr;
    }
    #command-input {
        dock: bottom;
        border: solid cyan;
    }
    #params-view {
        height: 1fr;
        padding: 1;
    }
    """
    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="left-pane"):
                yield RichLog(id="log-view", markup=True)
                yield Input(placeholder="Enter command (print <idx>, reset <idx>, complete <idx>, quit)...", id="command-input")
            with Vertical(id="right-pane"):
                yield Static("Waiting for data...", id="params-view")

    def on_mount(self) -> None:
        self.log_view = self.query_one("#log-view", RichLog)
        self.params_view = self.query_one("#params-view", Static)
        self.last_log_id = 0
        self.update_timer = self.set_interval(0.5, self.update_dashboard)
        self.log_view.write("[bold green]Server GUI Started[/bold green]")

    def update_dashboard(self):
        while self.last_log_id < len(experimenter.logs):
            log_item = experimenter.logs[self.last_log_id]
            self.log_view.write(f"[{log_item['time']}] {log_item['Text']}")
            self.last_log_id += 1
            
        with experimenter.lock:
            if len(experimenter.data_index) > 0:
                next_idx = experimenter.data_index[-1]
                if 0 <= next_idx < len(experimenter.data_array):
                    next_param = experimenter.data_array[next_idx]
                    formatted = json.dumps(next_param, indent=2)
                    self.params_view.update(f"[bold cyan]Next Experiment [{next_idx+1}]:[/bold cyan]\n\n{formatted}")
                else:
                    self.params_view.update("[bold yellow]All experiments distributed![/bold yellow]")
            else:
                self.params_view.update("No active index.")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value
        self.query_one(Input).value = ""
        user_input = cmd.strip()
        
        if user_input.lower() == 'quit':
            self.exit()
        elif user_input.startswith('print '):
            self.log_view.write(f"> {user_input}")
            try:
                index = int(user_input.split()[1]) - 1
                if 0 <= index < len(experimenter.data_array):
                    self.log_view.write(json.dumps(experimenter.data_array[index], indent=2))
                else:
                    self.log_view.write(f"Index {index+1} is out of bounds.")
            except Exception:
                self.log_view.write("Invalid command.")
        elif user_input.startswith('reset '):
            self.log_view.write(f"> {user_input}")
            try:
                indices = user_input.split()[1]
                if ':' in indices:
                    start, end = map(int, indices.split(':'))
                    start, end = start - 1, end - 1
                    for index in range(start, end + 1):
                        experimenter.reset(index)
                else:
                    experimenter.reset(int(indices) - 1)
            except Exception:
                self.log_view.write("Invalid command.")
        elif user_input.startswith('complete '):
            self.log_view.write(f"> {user_input}")
            try:
                indices_str = user_input.split()[1]
                if ':' in indices_str:
                    start_str, end_str = indices_str.split(':')
                    for i_1_based in range(int(start_str), int(end_str) + 1):
                        experimenter.complete(str(i_1_based), "Terminal")
                else:
                    experimenter.complete(indices_str, "Terminal")
            except Exception:
                self.log_view.write("Invalid command.")
        elif user_input.startswith('help'):
            self.log_view.write(f"> {user_input}")
            self.log_view.write("Available commands:")
            self.log_view.write("  print <idx>   - Print the parameters of the specified index")
            self.log_view.write("  reset <idx>   - Reset the state of the specified index")
            self.log_view.write("  complete <idx>- Mark the specified index as complete")
            self.log_view.write("  quit          - Shut down the server")
            self.log_view.write("  help          - Show this help message")
        else:
            self.log_view.write(f"Unknown command: {user_input}")

from textual.widgets import OptionList, Header, Footer, ProgressBar, Button
from textual.widgets.option_list import Option
from textual.widgets import Label

from textual.screen import Screen

class FileSelectionScreen(Screen):
    BINDINGS = [("escape", "quit", "Quit")]

    def __init__(self, py_files):
        super().__init__()
        self.py_files = py_files

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="container"):
            with Vertical(id="dialog"):
                yield Label("[bold cyan]Select a Parameter File to Load[/bold cyan]", classes="center-text")
                yield OptionList(*[Option(f) for f in self.py_files], id="file-list")
        yield Footer()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.app.selected_file = self.py_files[event.option_index]
        self.app.push_screen(ConfirmParamScreen(self.app.selected_file))

    def action_quit(self):
        self.app.exit(None)

class ConfirmParamScreen(Screen):
    def __init__(self, data_file):
        super().__init__()
        self.data_file = data_file
    
    BINDINGS = [("y", "answer_yes", "Yes"), ("n", "answer_no", "No"), ("escape", "answer_no", "Cancel")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="container"):
            with Vertical(id="dialog"):
                yield Label(f"[bold cyan]Confirm Parameter Selection[/bold cyan]\n", classes="center-text")
                yield Label(f"Do you want to load data from [bold green]{self.data_file}[/bold green]?", classes="center-text")
                with Horizontal(id="buttons"):
                    yield Button("Yes (Y)", variant="success", id="yes")
                    yield Button("No (N)", variant="error", id="no")
        yield Footer()

    def action_answer_yes(self):
        self.app.should_load_params = True
        self.check_state()

    def action_answer_no(self):
        self.app.exit((None, None, False))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            self.action_answer_yes()
        else:
            self.action_answer_no()

    def check_state(self):
        pattern = os.path.join("states", "*.json")
        files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        found_state = None
        for f_name in files:
            try:
                with open(f_name, 'r') as f:
                    state = json.load(f)
                if state.get("data_file") == self.data_file:
                    found_state = f_name
                    self.app.state_data = state
                    break
            except Exception:
                continue
        
        if found_state:
            self.app.push_screen(StatePromptScreen(self.data_file, found_state, self.app.state_data))
        else:
            self.app.exit((self.data_file, None, True))

class StatePromptScreen(Screen):
    def __init__(self, data_file, f_name, state_data):
        super().__init__()
        self.data_file = data_file
        self.f_name = f_name
        self.state_data = state_data
    
    BINDINGS = [("y", "answer_yes", "Yes"), ("n", "answer_no", "No"), ("escape", "answer_no", "Cancel")]

    def compose(self) -> ComposeResult:
        comp_arr = self.state_data.get("completed_array", [])
        self.comp = sum(1 for c in comp_arr if c)
        self.total = len(comp_arr)

        yield Header(show_clock=True)
        with Vertical(id="container"):
            with Vertical(id="dialog"):
                yield Label("[bold cyan]Found Previous State[/bold cyan]", classes="info-label")
                yield Label(f"File: [bold green]{self.f_name}[/bold green]")
                yield Label(f"Param File: [bold green]{self.data_file}[/bold green]\n")
                
                yield Label("Progress:", classes="center-text")
                yield ProgressBar(total=self.total, show_eta=False, id="progress")
                yield Label(f"{self.comp} / {self.total} Complete\n", classes="right-text")
                
                try:
                    with open(self.data_file, "r") as f:
                        code = f.read()
                    local_vars = {}
                    exec(code, globals(), local_vars)
                    data_array = local_vars.get("data_array", [])
                    
                    if self.state_data.get("data_index") and len(self.state_data["data_index"]) > 0:
                        last_idx = self.state_data["data_index"][-1]
                        if 0 <= last_idx < len(data_array):
                            last_param = data_array[last_idx]
                            yield Label("[bold]Last parameter sent:[/bold]")
                            yield Label(f"{json.dumps(last_param, indent=2)}\n")
                except Exception:
                    pass
                    
                yield Label("Do you want to load this state?", classes="center-text")
                with Horizontal(id="buttons"):
                    yield Button("Yes, load it (Y)", variant="success", id="yes")
                    yield Button("No, skip (N)", variant="error", id="no")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(ProgressBar).advance(self.comp)

    def action_answer_yes(self):
        self.app.exit((self.data_file, self.f_name, True))

    def action_answer_no(self):
        self.app.exit((self.data_file, None, True))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            self.action_answer_yes()
        else:
            self.action_answer_no()

class SetupWizardApp(App):
    CSS = """
    #dialog {
        padding: 2 4;
        border: solid green;
        background: $surface;
        width: auto;
        height: auto;
    }
    #container {
        align: center middle;
    }
    #buttons {
        margin-top: 2;
        layout: horizontal;
        align: center middle;
        height: auto;
    }
    Button {
        margin: 0 2;
    }
    .info-label {
        margin-bottom: 1;
        content-align: center middle;
        width: 100%;
    }
    .center-text {
        content-align: center middle;
        width: 100%;
    }
    .right-text {
        content-align: right middle;
        width: 100%;
    }
    OptionList {
        border: solid green;
    }
    """

    def __init__(self, py_files=None, start_file=None):
        super().__init__()
        self.py_files = py_files
        self.selected_file = start_file
        self.state_data = None
        self.should_load_params = False

    def on_mount(self):
        if self.selected_file:
            pattern = os.path.join("states", "*.json")
            files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
            found_state = None
            for f_name in files:
                try:
                    with open(f_name, 'r') as f:
                        state = json.load(f)
                    if state.get("data_file") == self.selected_file:
                        found_state = f_name
                        self.state_data = state
                        break
                except Exception:
                    continue
            
            if found_state:
                self.push_screen(StatePromptScreen(self.selected_file, found_state, self.state_data))
            else:
                self.exit((self.selected_file, None, True))
        else:
            self.push_screen(FileSelectionScreen(self.py_files))

if __name__ == "__main__":
    print("\033[2J\033[H", end="")
    
    # Argparse Setup
    parser = argparse.ArgumentParser(description="Distributed Experiment Server")
    parser.add_argument("--file", type=str, help="The python file containing parameter definitions (e.g., parameters_msga.py)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port to run the server on (default: {DEFAULT_PORT})")
    parser.add_argument("--gui", action="store_true", help="Launch the Textual TUI")
    parser.add_argument("--index", type=int, default=0, help="Start from a specific index (if not loading state)")
    
    # Print help if no args provided
    if len(sys.argv) == 1:
        parser.print_help()
        print("\n[Interactive Mode Initiated due to lack of arguments]")
    
    args = parser.parse_args()
    
    data_file = args.file
    should_load = False

    # File Selection Logic
    loaded = False
    if not data_file:
        id_counter = 1
        py_files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.py') and f != os.path.basename(__file__)]

        if not py_files:
            print("No Python files found, starting with empty data.")
        else:
            if len(py_files) == 1:
                data_file = py_files[0]
                print(f"Found only one Python file: {data_file}")
                app = SetupWizardApp(start_file=data_file)
                result = app.run()
            else:
                app = SetupWizardApp(py_files=py_files)
                result = app.run()

            if not result:
                print("No file selected. Exiting.")
                exit()
            
            data_file, state_file, should_load = result

            if not should_load:
                print("No parameters. No experiments.")
                exit()
            if state_file:
                loaded = True
    else:
        app = SetupWizardApp(start_file=data_file)
        result = app.run()
        if not result:
            print("Setup cancelled. Exiting.")
            exit()
        data_file, state_file, should_load = result
        
        if not should_load:
            print("No parameters. No experiments.")
            exit()
        if state_file:
            loaded = True

    # Execute the parameter file
    id_counter = 1
    with open(data_file, "r") as f:
        code = f.read()
    
    # 'exec' needs access to the global helper functions defined above
    exec(code)
    experimenter.data_array = data_array
    experimenter.data_file_name = data_file
    
    if loaded:
        experimenter.load_state(state_file)
    else:
        print("Checking 'data/' directory for existing results...")
        check_missing_files("./data/", len(data_array) + 1)
        
        index = args.index
        if index < 0: index = 0
        if len(experimenter.data_index) == 0:
            experimenter.data_index.append(index)
        elif experimenter.data_index[-1] < index:
            experimenter.data_index[-1] = index
        
        # Mark previous as done implicitly
        for i in range(1, experimenter.data_index[-1] + 1):
            experimenter.stateLog("Finished", i, "PRE")
            if len(experimenter.givenToPC) <= i - 1:
                experimenter.givenToPC.append("PRE")
            else:
                experimenter.givenToPC[i - 1] = "PRE"
                
            if len(experimenter.completed_array) <= i - 1:
                experimenter.completed_array.append(True)
            else:
                experimenter.completed_array[i - 1] = True

    experimenter.start_auto_save()

    server = ThreadingHTTPServer((DEFAULT_HOST, args.port), HTTPHandler)

    server_thread = threading.Thread(target=start_server, args=(server, args.port), daemon=True)
    server_thread.start()
    
    if args.gui:
        app = ServerApp()
        app.run()
        experimenter.save_state()
        server.shutdown()
        server.server_close()
        server_thread.join()
        print("Server stopped.")
    else:
        try:
            while True:
                user_input = input()
                if user_input.lower() == 'quit':
                    print("Shutting down the server...")
                    break
                elif user_input.startswith('print '):
                    try:
                        index = int(user_input.split()[1]) - 1
                        if 0 <= index < len(experimenter.data_array):
                            print(json.dumps(experimenter.data_array[index], indent=2))
                        else:
                            print(f"Index {index+1} is out of bounds.")
                    except Exception:
                        print("Invalid command.")
                elif user_input.startswith('reset '):
                    try:
                        indices = user_input.split()[1]
                        if ':' in indices:
                            start, end = map(int, indices.split(':'))
                            start, end = start - 1, end - 1
                            for index in range(start, end + 1):
                                experimenter.reset(index)
                        else:
                            experimenter.reset(int(indices) - 1)
                    except Exception:
                        print("Invalid command.")
                elif user_input.startswith('complete '):
                    try:
                        indices_str = user_input.split()[1]
                        if ':' in indices_str:
                            start_str, end_str = indices_str.split(':')
                            for i_1_based in range(int(start_str), int(end_str) + 1):
                                experimenter.complete(str(i_1_based), "Terminal")
                        else:
                            experimenter.complete(indices_str, "Terminal")
                    except Exception:
                        print("Invalid command.")
                elif user_input.startswith('help'):
                    print("Available commands:")
                    print("  print <idx>   - Print the parameters of the specified index")
                    print("  reset <idx>   - Reset the state of the specified index")
                    print("  complete <idx>- Mark the specified index as complete")
                    print("  quit          - Shut down the server")
                    print("  help          - Show this help message")

        except KeyboardInterrupt:
            print("\nKeyboardInterrupt detected. Shutting down the server...")
            
        finally:
            experimenter.save_state() # Final save on exit
            server.shutdown()
            server.server_close()
            server_thread.join()
            print("Server stopped.")
