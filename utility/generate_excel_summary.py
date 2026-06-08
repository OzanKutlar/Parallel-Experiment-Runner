import urllib.request
import json
import argparse
import os

try:
    import pandas as pd
except ImportError:
    print("Error: 'pandas' module not found. Please install it using 'pip install pandas openpyxl'")
    exit(1)


def fetch_batch_info(server_url):
    print(f"Fetching data from {server_url}/batchInfo...")
    try:
        req = urllib.request.Request(f"{server_url}/batchInfo")
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except Exception as e:
        print(f"Failed to connect to the server: {e}")
        return []


def generate_excel(server_url, output_file):
    data = fetch_batch_info(server_url)
    if not data:
        print("No data fetched. Exiting.")
        return

    rows = []
    for item in data:
        algo = item.get("algo", "")
        
        # Parse algo type
        if "generational" in algo:
            algo_type = "generational"
        elif "steady_state" in algo:
            algo_type = "steady state"
        else:
            algo_type = "-"
            
        # Parse selectino
        if "MISEGA" in algo:
            selectino = "mixed"
        elif "RGA" in algo:
            selectino = "single"
        else:
            selectino = "-"
            
        # Map fields to match the exact Excel column layout
        row = {
            "exp id": item.get("id", item.get("index", "-")),
            "algo type": algo_type,
            "selectino": selectino,
            "function": item.get("fun", "-"),
            "dim": item.get("dim", "-"),
            "inst": item.get("inst", "-"),
            "pop": item.get("m_val", "-"),
            "recomb": item.get("recomb", "-"),
            "modality": item.get("modality", "-")
        }
        rows.append(row)
        
    df = pd.DataFrame(rows)
    
    try:
        df.to_excel(output_file, index=False)
        print(f"Successfully saved {len(rows)} records to {output_file}")
    except Exception as e:
        print(f"Failed to save Excel file: {e}\n(Make sure 'openpyxl' is installed: pip install openpyxl)")


def main():
    parser = argparse.ArgumentParser(description="Generate Excel summary of experiments from server data.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host IP")
    parser.add_argument("--port", type=int, default=3753, help="Server port")
    
    # Default to placing it alongside the script in the utility folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_output = os.path.join(script_dir, "id_experiment.xlsx")
    
    parser.add_argument("--output", type=str, default=default_output, help="Path to output Excel file")
    
    args = parser.parse_args()
    server_url = f"http://{args.host}:{args.port}"
    
    generate_excel(server_url, args.output)


if __name__ == "__main__":
    main()
