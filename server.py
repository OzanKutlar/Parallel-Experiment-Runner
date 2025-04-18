from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import time
import sys
import threading
import base64
import numpy as np

# Server settings
host = "0.0.0.0"
port = 3753


data_array = []
completed_array = []
givenToPC = []

data_index = []

logs = []
stateLogs = []

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
    logs.append({"Text": text, "ID": len(logs), "time": current_time})

    
def stateLog(newState, index, sentTo="Null"):
    stateLogs.append({"state": newState, "index": index, "ID": len(stateLogs), "sentTo": sentTo})

class MyRequestHandler(BaseHTTPRequestHandler):
    global data_index
    
    def log_message(self, format, *args):
        pass
    
    def do_GET(self):
        global data_index
        
        if self.path == "/getNum":
            # Send the length of data_array as a response
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(str(len(data_array)).encode())
            return
        
        if self.path == "/logs":
            last_log = int(self.headers.get('lastLog', len(logs) - 6))
            # print(f"Request came for a log with lastlog : {last_log}")
            if(last_log <= len(logs) - 6):
                relevant_logs = logs[-5:]
            else:
                relevant_logs = logs[last_log+1:last_log+5]
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(relevant_logs).encode())
            return
            
        if self.path == "/status":
            last_log = int(self.headers.get('lastLog', len(logs) - 6))
            # print(f"Sending state from : {last_log}")
            relevant_logs = stateLogs[last_log+1:]
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(relevant_logs).encode())
            return
            
        if self.path == "/info":
            index = int(self.headers.get('index', 0)) - 1

            response = data_array[index] if 0 <= index < len(data_array) else {"text": "Invalid ID"}

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())
            return
            
        if self.path == "/reset":
            index = int(self.headers.get('index', 0)) - 1

            response = {"text": "Reset Success"} if 0 <= index < len(data_array) else {"text": "Invalid ID"}
            
            stateLog("Reset", index+1)
            print(f"Resetting data {index + 1} because of webpage.")
            log(f"Reset index {index + 1} from webpage")
            data_index.append(index)
            givenToPC[index] = 'Reset'
            completed_array[index] = False
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())
            return

        
        computer_name = self.headers.get('ComputerName', 'Admin')
        
        ID = self.headers.get('ID', '-1')
        
        last = data_index.pop()
        
        if not data_index:
            data_index.append(last + 1)
        if(ID != '-1'):
            if(not completed_array[int(ID) - 1]):
                stateLog("Reset", int(ID))
                print(f"Resetting data {int(ID) + 1} for {computer_name} due to new request.")
                log(f"Reset index {int(ID) + 1} by {computer_name}")
                data_index.append(int(ID))
                givenToPC[int(ID)] = 'Reset'
                completed_array[int(ID)] = False
                
        if last < len(data_array):
            response_data = data_array[last]
            if last == len(givenToPC):
                givenToPC.append(computer_name)
            else:
                givenToPC[last] = computer_name
            if last == len(completed_array):
                completed_array.append(False)
            else:
                completed_array[last] = False
            stateLog("Running", last + 1, computer_name)
            display_colored_array(data_array)
            log(f"Sent Data on index {last + 1} to {computer_name}")
            print(f"Data {last+1} has been sent to {computer_name}")
        else:
            response_data = {"message": "No more data left."}
            log(f"Shutting down {computer_name}")
            print(f'Data Distribution is finished. Extra connections : ', (last - len(data_array)))
        
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
                log(f"Recieved Data : {ID}")
                stateLog("Finished", int(ID), computer_name)
                print("ID " + ID + " is finished.")
                completed_array[int(ID) - 1] = True
                
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

            display_colored_array(data_array)
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
    print(json_str)
   
def display_colored_array(data_array):
    print("\033[2J\033[H", end="")  # Clear the screen

    # Determine number of columns needed
    total_rows = len(data_array)
    num_columns = (total_rows + ROWS_PER_COLUMN - 1) // ROWS_PER_COLUMN

    # Prepare table data
    columns = [[] for _ in range(num_columns)]
    for index, value in enumerate(data_array):
        column_index = index // ROWS_PER_COLUMN
        row_index = index % ROWS_PER_COLUMN

        # Determine status color and format value
        status_color = (GREEN if (completed_array[index] == True) else (RED if givenToPC[index] == 'Reset' else Magenta)) if index < len(givenToPC) else RED
        status = f"{status_color}{index + 1}{RESET}"
        pc_value = f"{YELLOW}({givenToPC[index]}){RESET}" if index < len(givenToPC) else f"{YELLOW}(N/A){RESET}"

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
    print("\033[2J\033[H", end="")  # Clear the screen
    if len(sys.argv) > 1:
        data_index.append(int(sys.argv[1]) - 1)
        if(data_index[-1] < 0):
            data_index[-1] = 0
        for i in range(1,data_index[-1] + 1):
            stateLog("Finished", i, "PRE")
            givenToPC.append("PRE")
            completed_array.append(True)
    else:
        data_index.append(0)
    # print(data_index[-1])
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

    
    server = HTTPServer((host, port), MyRequestHandler)

    server_thread = threading.Thread(target=start_server, args=(server,), daemon=True)
    server_thread.start()

    try:
        while True:
            display_colored_array(data_array)
            user_input = input()
            if user_input.lower() == 'quit':
                print("Shutting down the server...")
                server.shutdown()
                server.server_close()
                server_thread.join()
                print("Server stopped.")
                break
            elif user_input.startswith('print '):
                try:
                    index = int(user_input.split()[1]) - 1
                    if 0 <= index < len(data_array):
                        print(json.dumps(data_array[index], indent=2))
                        input()
                    else:
                        print(f"Index {index+1} is out of bounds. Array length is 1-{len(data_array)}.")
                except (IndexError, ValueError):
                    print("Invalid command format. Use 'print x', where x is a valid index.")
            elif user_input.startswith('reset '):
                try:
                    indices = user_input.split()[1]
                    
                    if ':' in indices:
                        start, end = map(int, indices.split(':'))
                        start, end = start - 1, end - 1
                        
                        if 0 <= start < len(givenToPC) and 0 <= end < len(givenToPC) and start <= end:
                            for index in range(start, end + 1):
                                stateLog("Reset", index + 1)
                                log(f"Reset index {index + 1} from terminal.")
                                data_index.append(index)
                                givenToPC[index] = 'Reset'
                                completed_array[index] = False
                            display_colored_array(data_array)
                        else:
                            print(f"Invalid range. Ensure both indices are within 1-{len(givenToPC)} and start ≤ end.")
                    
                    else:
                        index = int(indices) - 1
                        if 0 <= index < len(givenToPC):
                            stateLog("Reset", index + 1)
                            log(f"Reset index {index + 1} from terminal.")
                            data_index.append(index)
                            givenToPC[index] = 'Reset'
                            completed_array[index] = False
                            display_colored_array(data_array)
                        else:
                            print(f"Index {index + 1} is out of bounds. Array length is 1-{len(givenToPC)}.")
                except (IndexError, ValueError):
                    print("Invalid command format. Use 'reset x' or 'reset x:y', where x and y are valid indices.")

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected. Shutting down the server...")
        server.shutdown()
        server.server_close()
        server_thread.join()
        print("Server stopped.")




