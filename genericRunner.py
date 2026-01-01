import requests
import json
import base64
import socket
import time
import subprocess
import os
import sys

# ==========================================
#              CONFIGURATION
# ==========================================
SERVER_IP = "127.0.0.1"
PORT = 3753

# Path to your executable (e.g., "bin/simulation.exe" or "./algo")
EXE_PATH = "python dummy_work.py" 

# The generic runner assumes your EXE generates a file.
# We need to know what that file is named to upload it.
# Use {id} as a placeholder if the EXE puts the ID in the filename.
OUTPUT_FILE_PATTERN = "output_{id}.txt" 

# Should we delete the output file after uploading?
DELETE_AFTER_UPLOAD = True
# ==========================================

SERVER_URL = f"http://{SERVER_IP}:{PORT}"
HOSTNAME = socket.gethostname()

def construct_command_line(job_params):
    """
    Converts JSON parameters into command line arguments.
    Example: {"lr": 0.01, "id": 5} -> ['--lr', '0.01', '--id', '5']
    """
    args = []
    for key, value in job_params.items():
        # Skip internal keys if necessary, but usually we pass everything
        args.append(f"--{key}")
        args.append(str(value))
    return args

def main():
    print(f"--- Generic Runner Wrapper on {HOSTNAME} ---")
    print(f"Target EXE: {EXE_PATH}")
    print(f"Connecting to: {SERVER_URL}")

    while True:
        try:
            # 1. GET Request
            headers = {"ComputerName": HOSTNAME}
            try:
                r = requests.get(SERVER_URL, headers=headers, timeout=10)
                r.raise_for_status()
                job = r.json()
            except requests.exceptions.RequestException as e:
                print(f"Server connection issue: {e}. Retrying in 5s...")
                time.sleep(5)
                continue

            # Check if finished
            if "message" in job:
                print(">> Message from server: No more data. Stopping.")
                break

            job_id = job['id']
            print(f"\n>> Processing Job ID: {job_id}")
            print(f"   Params: {job}")

            # 2. Construct Command
            # Split EXE_PATH in case it contains spaces (e.g. "python script.py")
            cmd = EXE_PATH.split() + construct_command_line(job)
            
            print(f"   Executing: {' '.join(cmd)}")

            # 3. Run Executable
            start_time = time.time()
            try:
                # Run and wait for completion. Capture output if needed for debugging.
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                # print("   Stdout:", result.stdout) # Uncomment for debug
            except subprocess.CalledProcessError as e:
                print(f"   [ERROR] Execution failed for ID {job_id}")
                print(f"   Stderr: {e.stderr}")
                # We skip uploading if the execution crashed
                continue
            
            duration = time.time() - start_time
            print(f"   Execution finished in {duration:.2f}s")

            # 4. Locate Output File
            expected_filename = OUTPUT_FILE_PATTERN.format(id=job_id)
            
            if not os.path.exists(expected_filename):
                print(f"   [ERROR] Expected output file '{expected_filename}' not found!")
                continue

            # 5. Read and Encode
            with open(expected_filename, "rb") as f:
                file_binary = f.read()
                
            b64_content = base64.b64encode(file_binary).decode('utf-8')

            # 6. Upload
            payload = {
                "file_name": expected_filename,
                "file": b64_content
            }
            
            post_headers = {
                "ComputerName": HOSTNAME,
                "ID": str(job_id)
            }
            
            requests.post(SERVER_URL, json=payload, headers=post_headers)
            print(f"   [Success] Uploaded {expected_filename}")

            # 7. Cleanup
            if DELETE_AFTER_UPLOAD:
                os.remove(expected_filename)
                print(f"   [Cleanup] Deleted local file.")

        except KeyboardInterrupt:
            print("\nRunner stopped by user.")
            break
        except Exception as e:
            print(f"Critical error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()