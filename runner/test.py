import socket
import json
import argparse
import threading
import sys
import os
import base64
import subprocess
import tempfile
import shutil
from mat4py import savemat

client_id = 0

def sendUpstream(obj, upstream_socket):
    upstream_socket.send((json.dumps(obj) + "\n").encode('utf-8'))

def listen_to_server(sock):
    global client_id
    try:
        while True:
            data = sock.recv(1024).decode('utf-8')
            if not data:
                print("Server closed the connection.")
                break

            try:
                response = json.loads(data)
                if 'command' in response:
                    command = response['command']

                    if command == 'shutdown':
                        print("Received shutdown command. Exiting...")
                        sock.close()
                        os._exit(0)

                    elif command.startswith('file '):
                        filename = command[5:].strip()
                        if os.path.isfile(filename):
                            with open(filename, 'rb') as f:
                                file_content = base64.b64encode(f.read()).decode('utf-8')
                            file_response = {
                                'req': 'file',
                                'filename': "file" + str(client_id),
                                'file': file_content
                            }
                            sendUpstream(file_response, sock)
                            print(f"Sent file '{filename}' in base64 format.")
                        else:
                            print(f"File '{filename}' not found in current directory.")
                    else:
                        print("Unknown command:", command)

                # Check if the response contains 'data'
                elif 'data' in response:
                    data = response['data']
                    print("Received 'data' field, running MATLAB function...")

                    # Prepare the data to be passed to MATLAB
                    try:
                        # Convert the data to a temporary MATLAB-readable .mat file
                        temp_mat_file = create_temp_mat_file(data)

                        # Define the MATLAB command to execute the function in batch mode
                        current_dir = os.getcwd()
                        command = f"matlab -batch \"cd('{current_dir}'); result_filename = runExp('{temp_mat_file}'); disp(result_filename);\""

                        print(f"Running MATLAB command: {command}")

                        # Run the MATLAB command using subprocess
                        result = subprocess.run(command, shell=True, capture_output=True, text=True)

                        # Check for any errors in MATLAB's output
                        if result.returncode != 0:
                            print(f"MATLAB error: {result.stderr}")
                        else:
                            print(f"MATLAB output:\n{result.stdout}")
                            # Extract the filename from MATLAB output
                            result_filename = extract_filename_from_output(result.stdout)
                            # Use only the basename for filename
                            filename = os.path.basename(result_filename)
                            print(f"Received filename from MATLAB: {result_filename}")
                            print(f"Using filename: {filename}")

                            if os.path.isfile(result_filename):
                                with open(result_filename, 'rb') as f:
                                    file_content = base64.b64encode(f.read()).decode('utf-8')
                                file_response = {
                                    'req': 'file',
                                    'filename': filename,
                                    'file': file_content
                                }
                                sendUpstream(file_response, sock)
                                print(f"Sent file '{filename}' in base64 format.")

                        # Cleanup the temporary .mat file
                        os.remove(temp_mat_file)

                    except Exception as e:
                        print(f"Error while running MATLAB function: {e}")

                else:
                    print("Response from server:", response)

            except json.JSONDecodeError:
                print("Invalid JSON received.")
    except Exception as e:
        print("Error in listening thread:", e)
        sock.close()
        sys.exit(1)

def create_temp_mat_file(data):
    """
    Creates a temporary .mat file from the provided data (which should be a dictionary)
    to be used by the MATLAB batch command.
    """
    # Create a temporary directory to hold the .mat file
    temp_dir = tempfile.mkdtemp()

    # Save the Python dictionary as a .mat file
    temp_mat_file = os.path.join(temp_dir, "data.mat")
    
    try:
        # Save the data as a .mat file
        savemat(temp_mat_file, {'data': data})
    except ImportError:
        print("scipy module is required for saving .mat files.")
        raise

    return temp_mat_file

def extract_filename_from_output(output):
    """
    Extracts the last non-whitespace line from MATLAB's output.
    This assumes the last meaningful line contains the filename.
    """
    lines = output.strip().splitlines()
    for line in reversed(lines):
        if line.strip():  # Check if the line is not just whitespace
            return line.strip()
    return ""



def send_to_server(sock):
    try:
        while True:
            msg = input("Enter message (or 'quit' to exit): ").strip()
            if msg.lower() == 'quit':
                print("Disconnecting...")
                sock.close()
                break

            request = {'req': msg, 'ComputerName': os.getenv('COMPUTERNAME')}
            sendUpstream(request, sock)
    except Exception as e:
        print("Error in sending thread:", e)
        sock.close()



def test_client(proxy_host='127.0.0.1', proxy_port=65431):
    global client_id
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((proxy_host, proxy_port))

        # Receive the client ID from proxy
        data = s.recv(1024).decode('utf-8')
        try:
            response = json.loads(data)
            if 'client_id' in response:
                client_id = response['client_id']
                print(f"Connected to proxy. Your client ID is: {client_id}")
            else:
                print("Failed to receive client ID.")
                return
        except json.JSONDecodeError:
            print("Invalid JSON received from proxy.")
            return

        # Start listening thread
        listen_thread = threading.Thread(target=listen_to_server, args=(s,), daemon=True)
        listen_thread.start()

        # Main thread handles sending
        send_to_server(s)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test client for proxy connection")
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Proxy server host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=65431, help='Proxy server port (default: 65431)')

    args = parser.parse_args()

    test_client(proxy_host=args.host, proxy_port=args.port)
