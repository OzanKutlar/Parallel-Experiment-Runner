from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import time
import sys
import threading
import base64
import numpy as np
import socket

# Server settings
host = "0.0.0.0"
port = 3753

class Experimenter:
    def __init__(self):
        self.data_array = []
        self.completed_array = []
        self.givenToPC = []
        self.data_index = []
        self.logs = []
        self.stateLogs = []

    def stateLog(self, newState, index, sentTo="Null"):
        self.stateLogs.append({"state": newState, "index": index, "ID": len(self.stateLogs), "sentTo": sentTo})
    
    def getExperiment(self, ID, computer_name):
        last = self.data_index.pop()
        
        if not self.data_index:
            self.data_index.append(last + 1)
        if(ID != '-1'):
            if(not self.completed_array[int(ID) - 1]):
                self.stateLog("Reset", int(ID))
                print(f"Resetting data {int(ID) + 1} for {computer_name} due to new request.")
                self.log(f"Reset index {int(ID) + 1} by {computer_name}")
                self.data_index.append(int(ID))
                self.givenToPC[int(ID)] = 'Reset'
                self.completed_array[int(ID)] = False
                
        if last < len(self.data_array):
            response_data = self.data_array[last]
            if last == len(self.givenToPC):
                self.givenToPC.append(computer_name)
            else:
                self.givenToPC[last] = computer_name
            if last == len(self.completed_array):
                self.completed_array.append(False)
            else:
                self.completed_array[last] = False
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
        self.stateLog("Finished", int(ID), computer_name)
        print("ID " + ID + " is finished.")
        self.completed_array[int(ID) - 1] = True

    def reset(self, index):
        self.stateLog("Reset", index + 1)
        log(f"Reset index {index + 1} from terminal.")
        self.data_index.append(index)
        self.givenToPC[index] = 'Reset'
        self.completed_array[index] = False


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
    experimenter.logs.append({"Text": text, "ID": len(experimenter.logs), "time": current_time})

    

class HTTPHandler(BaseHTTPRequestHandler):
    global experimenter
    
    def log_message(self, format, *args):
        pass  # This disables the default logging
    
    def do_GET(self):
        global experimenter
        
        if self.path == "/getNum":
            # Send the length of experimenter.data_array as a response
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(str(len(experimenter.data_array)).encode())
            return
        
        if self.path == "/logs":
            last_log = int(self.headers.get('lastLog', len(experimenter.logs) - 6))
            # print(f"Request came for a log with lastlog : {last_log}")
            if(last_log <= len(experimenter.logs) - 6):
                relevant_logs = experimenter.logs[-5:]
            else:
                relevant_logs = experimenter.logs[last_log+1:last_log+5]
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(relevant_logs).encode())
            return
            
        if self.path == "/status":
            last_log = int(self.headers.get('lastLog', len(experimenter.logs) - 6))
            # print(f"Sending state from : {last_log}")
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
            
            experimenter.stateLog("Reset", index+1)
            print(f"Resetting data {index + 1} because of webpage.")
            log(f"Reset index {index + 1} from webpage")
            experimenter.data_index.append(index)
            experimenter.givenToPC[index] = 'Reset'
            experimenter.completed_array[index] = False
            
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
            # Get the content length from headers

            # Read the incoming JSON payload
            post_data = self.rfile.read(content_length).decode('utf-8')

            # Parse JSON data
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

            # Decode the Base64-encoded file content
            try:
                file_content = base64.b64decode(file_content_base64)
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid Base64 content in 'file'")
                return

            # Save the file to disk
            with open("data/" + file_name, 'wb') as f:
                f.write(file_content)

            display_colored_array(experimenter.data_array)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"File uploaded and saved successfully")

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, lastLog, index')
        super().end_headers()

    def do_OPTIONS(self):
        # Handle preflight requests for CORS
        self.send_response(200)
        self.end_headers()


# ChatGPT generated this. When an input object with arrays for parameters is given in,
# It generates all combinations of those parameters as seperate objects.
def generate_combinations(input_obj, id_counter):
    # Get the keys and values from the input object
    keys = list(input_obj.keys())
    values = list(input_obj.values())


    # Recursive function to generate combinations
    def combine(index, current_combination):
        nonlocal id_counter  # To modify the outer variable inside the inner function
        
        # Base case: when the index reaches the end of the keys
        if index == len(keys):
            # Add the current ID to the combination
            current_combination['id'] = id_counter
            result.append(current_combination.copy())
            id_counter += 1  # Increment the ID for the next combination
            return

        # Iterate over all values for the current key
        for value in values[index]:
            current_combination[keys[index]] = value
            combine(index + 1, current_combination)
    
    # List to store all combinations
    result = []

    combine(0, {})
    
    return [result, id_counter]



def display_object_attributes(arr):
    for obj in arr:
        print()
        for attribute, value in obj.items():
            print(f"  {attribute}: {value}")
        print()  # For spacing between objects



def merge_objects(dict1, dict2): 
    merged = dict1.copy() 
    merged.update(dict2) 
    return merged
    

def generate_combined_data(shared_params, id_counter, *param_sets):
    combined_data_array = []

    for params in param_sets:
        # Merge shared_params with the current params and generate combinations
        temp_data_array, id_counter = generate_combinations(merge_objects(shared_params, params), id_counter)
        # Append the resulting data array to the combined array
        combined_data_array += temp_data_array

    return combined_data_array, id_counter


def print_list_as_json(lst):
    json_str = json.dumps(lst, indent=4)
    with open("listJson.json", "w") as file:
        file.write(json_str)
   
def display_colored_array(data_array):
    return
    print("\033[2J\033[H", end="")  # Clear the screen

    # Determine number of columns needed
    total_rows = len(experimenter.data_array)
    num_columns = (total_rows + ROWS_PER_COLUMN - 1) // ROWS_PER_COLUMN

    # Prepare table data
    columns = [[] for _ in range(num_columns)]
    for index, value in enumerate(experimenter.data_array):
        column_index = index // ROWS_PER_COLUMN
        row_index = index % ROWS_PER_COLUMN

        # Determine status color and format value
        status_color = (GREEN if (experimenter.completed_array[index] == True) else (RED if experimenter.givenToPC[index] == 'Reset' else Magenta)) if index < len(experimenter.givenToPC) else RED
        status = f"{status_color}{index + 1}{RESET}"
        pc_value = f"{YELLOW}({experimenter.givenToPC[index]}){RESET}" if index < len(experimenter.givenToPC) else f"{YELLOW}(N/A){RESET}"

        # Append row to the appropriate column
        columns[column_index].append(f"{status} {pc_value}")

    # Print the data in columns
    for row in range(ROWS_PER_COLUMN):
        for col in range(num_columns):
            if row < len(columns[col]):  # Check if this row exists in the column
                print(f"{columns[col][row]:<{COLUMN_DIST}}", end="")  # Adjust padding for alignment
        print()  # Newline for the next row
        
    print("Enter command (type 'quit' to stop): ")
   
def start_server(server):
    log("Server Started")
    print(f"Server running on {server.server_address[0]}:{server.server_address[1]}")
    server.serve_forever()


if __name__ == "__main__":
    print("\033[2J\033[H", end="")
    if len(sys.argv) > 1:
        experimenter.data_index.append(int(sys.argv[1]) - 1)
        if(experimenter.data_index[-1] < 0):
            experimenter.data_index[-1] = 0
        for i in range(1,experimenter.data_index[-1] + 1):
            experimenter.stateLog("Finished", i, "PRE")
            experimenter.givenToPC.append("PRE")
            experimenter.completed_array.append(True)
    else:
        experimenter.data_index.append(0)
    # print(experimenter.data_index[-1])
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
    
    if not should_load:
        print("No parameters. No experiments.");
        exit()
    with open(data_file, "r") as f:
        code = f.read()  # Read the script content

    exec(code)  # Execute the script dynamically
    experimenter.data_array = data_array

    
    server = HTTPServer((host, port), HTTPHandler)

    server_thread = threading.Thread(target=start_server, args=(server,), daemon=True)
    server_thread.start()
    

    try:
        while True:
            user_input = input()
            if user_input.lower() == 'quit':
                print("Shutting down the server...")
                break
            if user_input.lower() == "start":
                socket_server.sendCommand("start")
            elif user_input.startswith('print '):
                try:
                    index = int(user_input.split()[1]) - 1
                    if 0 <= index < len(experimenter.data_array):
                        print(json.dumps(experimenter.data_array[index], indent=2))
                        input()
                    else:
                        print(f"Index {index+1} is out of bounds. Array length is 1-{len(experimenter.data_array)}.")
                except (IndexError, ValueError):
                    print("Invalid command format. Use 'print x', where x is a valid index.")
            elif user_input.startswith('reset '):
                try:
                    indices = user_input.split()[1]
                    
                    print("Resetting indices : " + user_input.split()[1])
                    
                    if ':' in indices:
                        start, end = map(int, indices.split(':'))
                        start, end = start - 1, end - 1
                        
                        if 0 <= start < len(experimenter.givenToPC) and 0 <= end < len(experimenter.givenToPC) and start <= end:
                            for index in range(start, end + 1):
                                experimenter.reset(index)
                        else:
                            print(f"Invalid range. Ensure both indices are within 1-{len(experimenter.givenToPC)} and start ≤ end.")
                    
                    else:
                        index = int(indices) - 1
                        if 0 <= index < len(experimenter.givenToPC):
                            experimenter.reset(index)
                        else:
                            print(f"Index {index + 1} is out of bounds. Array length is 1-{len(experimenter.givenToPC)}.")
                except (IndexError, ValueError):
                    print("Invalid command format. Use 'reset x' or 'reset x:y', where x and y are valid indices.")

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected. Shutting down the server...")
        
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join()
        # socket_server.stop()
        print("Server stopped.")



