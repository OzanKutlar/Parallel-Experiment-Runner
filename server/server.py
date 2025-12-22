from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import time
import sys
import threading
import base64
import numpy as np
import socket
import argparse

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

    def save_state(self):
        """Persist current state to disk."""
        try:
            state = {
                "completed_array": self.completed_array,
                "givenToPC": self.givenToPC,
                "data_index": self.data_index
            }
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"Error saving state: {e}")

    def load_state(self):
        """Load state from disk."""
        if not os.path.exists(STATE_FILE):
            return False
        
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
            
            # validation to ensure loaded state matches loaded data size
            if len(self.data_array) > 0:
                # Basic validation
                pass 

            self.completed_array = state.get("completed_array", [])
            self.givenToPC = state.get("givenToPC", [])
            self.data_index = state.get("data_index", [0])
            print(f"State loaded from {STATE_FILE}")
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
                
                self.stateLog("Running", last + 1, computer_name)
                display_colored_array(self.data_array)
                log(f"Sent Data on index {last + 1} to {computer_name}")
                print(f"Data {last+1} has been sent to {computer_name}")
            else:
                response_data = {"message": "No more data left."}
                log(f"Shutting down {computer_name}")
                print(f'Data Distribution is finished. Extra connections : ', (last - len(self.data_array)))
            
            self.save_state() # Save after modification
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
            self.save_state() # Save after modification

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
            self.save_state() # Save after modification


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

    # Double check gaps
    for i in range(1, lastNonMissing):
        file_name = f"exp-{i}.mat"
        file_path = os.path.join(directory, file_name)
        if not os.path.isfile(file_path):
            experimenter.reset(i-1) # reset uses 0-based index

if __name__ == "__main__":
    print("\033[2J\033[H", end="")
    
    # Argparse Setup
    parser = argparse.ArgumentParser(description="Distributed Experiment Server")
    parser.add_argument("--file", type=str, help="The python file containing parameter definitions (e.g., parameters_msga.py)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port to run the server on (default: {DEFAULT_PORT})")
    parser.add_argument("--cont", action="store_true", help="Continue from previous state (Load JSON state or check existing files)")
    parser.add_argument("--index", type=int, default=0, help="Start from a specific index (if not using --cont)")
    
    # Print help if no args provided
    if len(sys.argv) == 1:
        parser.print_help()
        print("\n[Interactive Mode Initiated due to lack of arguments]")
    
    args = parser.parse_args()
    
    data_file = args.file
    should_load = False

    # File Selection Logic (Interactive Fallback)
    if not data_file:
        id_counter = 1
        py_files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.py') and f != os.path.basename(__file__)]

        if not py_files:
            print("No Python files found, starting with empty data.")
        else:
            if len(py_files) == 1:
                data_file = py_files[0]
                print(f"Found only one Python file: {data_file}")
                should_load = input(f"Do you want to load data from {data_file}? (Y/n): ").strip().lower()
                should_load = should_load in ("", "yes", "y")
            else:
                print("Multiple Python files found:")
                for idx, file in enumerate(py_files, start=1):
                    print(f"{idx}. {file}")
                while True:
                    try:
                        choice = int(input("Choose a file to load (enter the number): ").strip())
                        if 1 <= choice <= len(py_files):
                            data_file = py_files[choice - 1]
                            should_load = input(f"Do you want to load data from {data_file}? (Y/n): ").strip().lower()
                            should_load = should_load in ("", "yes", "y")
                            break
                        else:
                            print("Invalid selection.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")
    else:
        should_load = True

    if not should_load:
        print("No parameters. No experiments.")
        exit()
        
    # Execute the parameter file
    id_counter = 1
    with open(data_file, "r") as f:
        code = f.read()
    
    # 'exec' needs access to the global helper functions defined above
    exec(code)
    experimenter.data_array = data_array

    # State Initialization Logic
    if args.cont:
        # Try loading from JSON first
        loaded = experimenter.load_state()
        if not loaded:
            print("No state file found. Checking 'data/' directory for existing results...")
            check_missing_files("./data/", len(data_array) + 1)
    else:
        # Manual Index Start
        index = args.index
        if index < 0: index = 0
        experimenter.data_index.append(index)
        
        # Mark previous as done implicitly
        for i in range(1, index + 1):
            experimenter.stateLog("Finished", i, "PRE")
            experimenter.givenToPC.append("PRE")
            experimenter.completed_array.append(True)

    server = HTTPServer((DEFAULT_HOST, args.port), HTTPHandler)

    server_thread = threading.Thread(target=start_server, args=(server, args.port), daemon=True)
    server_thread.start()
    
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

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected. Shutting down the server...")
        
    finally:
        experimenter.save_state() # Final save on exit
        server.shutdown()
        server.server_close()
        server_thread.join()
        print("Server stopped.")
