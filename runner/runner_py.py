import requests
import json
import base64
import socket
import time
import os

# --- CONFIGURATION ---
SERVER_IP = "127.0.0.1"
PORT = 3753
# ---------------------

SERVER_URL = f"http://{SERVER_IP}:{PORT}"
HOSTNAME = socket.gethostname()

def run_experiment_logic(params):
    """
    Replace this function with your actual experiment logic.
    """
    print(f"   [Worker] Processing: {params}")
    
    # Simulate work
    time.sleep(1)
    
    # Example: Create a simple result string based on params
    result_data = {
        "id": params['id'],
        "status": "success",
        "processed_val": "Calculated results here"
    }
    
    # Return the binary content of the 'file' we want to upload
    return json.dumps(result_data, indent=2).encode('utf-8')

def main():
    print(f"--- Python Runner Started on {HOSTNAME} ---")
    print(f"Connecting to {SERVER_URL}")

    while True:
        try:
            # 1. Get Job
            headers = {"ComputerName": HOSTNAME}
            try:
                r = requests.get(SERVER_URL, headers=headers, timeout=10)
                r.raise_for_status()
                job = r.json()
            except requests.exceptions.RequestException as e:
                print(f"Server unreachable ({e}). Retrying in 5s...")
                time.sleep(5)
                continue

            # Check if finished
            if "message" in job:
                print(">> Server Message: No more data left. Exiting.")
                break

            job_id = job['id']
            print(f">> Received Job ID: {job_id}")

            # 2. Run Experiment
            file_content_binary = run_experiment_logic(job)
            
            # 3. Prepare Upload
            # Encode binary content to Base64 string
            b64_content = base64.b64encode(file_content_binary).decode('utf-8')
            
            payload = {
                "file_name": f"result_{job_id}.json",
                "file": b64_content
            }
            
            # 4. Upload Result
            post_headers = {
                "ComputerName": HOSTNAME,
                "ID": str(job_id)
            }
            
            requests.post(SERVER_URL, json=payload, headers=post_headers)
            print(f"   [Upload] Job {job_id} completed and uploaded.\n")

        except KeyboardInterrupt:
            print("\nStopped by user.")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()