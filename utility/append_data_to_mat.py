import os
import argparse
import json
import urllib.request
import scipy.io


def fetch_batch_info(server_url):
    """
    Fetches the full array of generated parameters from the server.
    """
    print(f"Fetching data from {server_url}/batchInfo...")
    try:
        req = urllib.request.Request(f"{server_url}/batchInfo")
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Failed to connect to the server: {e}")
        return {}
    
    # Build a mapping of id -> parameter dictionary
    param_map = {}
    for item in data:
        # Check for 'id' first, fallback to 'index' if necessary
        item_id = item.get('id', item.get('index'))
        if item_id is not None:
            param_map[int(item_id)] = item
            
    print(f"Fetched {len(param_map)} parameter configurations from the server.")
    return param_map


def append_data_to_mat(server_url, data_dir):
    """
    Scans the data directory for .mat files, matches them to the server data,
    and injects the data variable into the file.
    """
    if not os.path.isdir(data_dir):
        print(f"Error: Directory '{data_dir}' does not exist.")
        return

    param_map = fetch_batch_info(server_url)
    if not param_map:
        print("No parameters found or server unreachable. Exiting.")
        return

    success_count = 0
    error_count = 0
    skip_count = 0

    print(f"\nScanning '{data_dir}' for .mat files...")
    
    for filename in os.listdir(data_dir):
        if filename.startswith("exp-") and filename.endswith(".mat"):
            try:
                # Extract ID from filename (e.g., exp-15.mat -> 15)
                id_str = filename.replace("exp-", "").replace(".mat", "")
                file_id = int(id_str)
            except ValueError:
                continue
            
            if file_id in param_map:
                file_path = os.path.join(data_dir, filename)
                try:
                    # Load existing .mat file
                    mat_data = scipy.io.loadmat(file_path)
                    
                    # Inject the parameter dictionary as the 'data' variable
                    mat_data['data'] = param_map[file_id]
                    
                    # Overwrite the file with the new data included
                    scipy.io.savemat(file_path, mat_data)
                    success_count += 1
                except Exception as e:
                    print(f"Error modifying {filename}: {e}")
                    error_count += 1
            else:
                skip_count += 1

    print(f"\nOperation Complete:")
    print(f"  Successfully updated: {success_count} files")
    print(f"  Skipped (No ID match): {skip_count} files")
    print(f"  Errors encountered: {error_count} files")


def main():
    parser = argparse.ArgumentParser(description="Inject server parameters into corresponding .mat files.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host IP")
    parser.add_argument("--port", type=int, default=3753, help="Server port")
    
    # Default data directory to ../server/data relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_data = os.path.normpath(os.path.join(script_dir, "..", "server", "data"))
    
    parser.add_argument("--data-dir", type=str, default=default_data, help="Path to the data directory containing .mat files")
    
    args = parser.parse_args()
    server_url = f"http://{args.host}:{args.port}"
    
    append_data_to_mat(server_url, args.data_dir)


if __name__ == "__main__":
    main()
