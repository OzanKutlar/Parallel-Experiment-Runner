# Generic Distributed Experiment Runner

This system is a language-agnostic framework designed to distribute large-scale computational experiments across multiple computers. It uses a central Python-based HTTP server to manage a job queue, while clients (runners) written in **any language** fetch parameters, execute tasks, and upload results.

---

## 📂 Project Structure

```text
├── server/                 # Central Orchestrator
│   ├── server.py           # Main HTTP server logic
│   ├── data/               # Stores result files uploaded by clients
│   └── parameters_exp.py   # Define your experiment search space here
├── utility/                # Dashboards
│   ├── overview.php        # Modern Dark/Light mode Dashboard
│   └── index.php           # Legacy Dashboard
├── clients/                # Example Runners (You write these)
    ├── runner.py           # Python example
    ├── runner.m            # MATLAB example
    ├── runner.sh           # Bash example
    └── runner.cpp          # C++ example
└── ParameterExamples.md    # 📖 Guide to defining experiment parameters
```

---

## 🔧 Step 1: Configure & Start the Server

### 1. Define Parameters
Create a Python file in the `server/` directory (e.g., `parameters_exp.py`). The server will generate every permutation of lists provided.

```python
# parameters_exp.py
shared_params = {
    "dataset": ["Data_A", "Data_B"],
    "learning_rate": [0.01, 0.001],
    "optimizer": ["adam", "sgd"]
}
# This generates 8 distinct jobs.
# IMPORTANT: Must result in a variable named 'data_array'
data_array, _ = generate_combined_data({}, 1, shared_params)
```

> 📘 **See [ParameterExamples.md](ParameterExamples.md) for advanced configurations (Branching, Fixed Pairs, Math generation).**

### 2. Start the Server
```bash
cd server
python server.py --file parameters_exp.py --port 3753
```

---

## 💻 Step 2: Implement the Client (Runner)

The server exposes a simple REST API. Your client needs to perform a loop of **GET** (fetch job) and **POST** (upload result).

### API Protocol
1.  **GET** `http://SERVER_IP:PORT/`
    *   **Response:** JSON object containing parameters and a unique `id`.
    *   *If response contains `{"message": "No more data left."}`, stop.*
2.  **Run Experiment** using the received parameters.
3.  **POST** `http://SERVER_IP:PORT/`
    *   **Headers:** `ID: <job_id>`, `ComputerName: <hostname>`
    *   **Body (JSON):**
        ```json
        {
          "file_name": "result_<id>.json",
          "file": "<base64_encoded_content_of_result>"
        }
        ```

### Example Runner Code

#### 🐍 Python
```python
import requests, json, base64, socket, time

SERVER_URL = "http://127.0.0.1:3753"
HOSTNAME = socket.gethostname()

while True:
    # 1. Get Job
    try:
        r = requests.get(SERVER_URL, headers={"ComputerName": HOSTNAME})
        job = r.json()
    except:
        print("Server unreachable, retrying..."); time.sleep(5); continue

    if "message" in job:
        print("Done."); break

    print(f"Running Job ID {job['id']} with {job}")
    
    # 2. Do Work (Simulation/Calc)
    result_content = f"Result for {job['id']}: Success".encode('utf-8')
    
    # 3. Upload Result
    payload = {
        "file_name": f"res_{job['id']}.txt",
        "file": base64.b64encode(result_content).decode('utf-8')
    }
    requests.post(SERVER_URL, json=payload, headers={"ID": str(job['id']), "ComputerName": HOSTNAME})
```

#### 🐚 Bash (curl + jq)
```bash
SERVER="http://127.0.0.1:3753"
HOST=$(hostname)

while true; do
    # 1. Get Job
    RESPONSE=$(curl -s -H "ComputerName: $HOST" "$SERVER")
    MSG=$(echo "$RESPONSE" | jq -r '.message // empty')
    
    if [ "$MSG" == "No more data left." ]; then break; fi
    
    ID=$(echo "$RESPONSE" | jq -r '.id')
    echo "Running Job $ID..."
    
    # 2. Run Experiment & Encode Result
    echo "Result data" > result.txt
    B64=$(base64 -w 0 result.txt)
    
    # 3. Upload
    JSON="{\"file_name\": \"res_$ID.txt\", \"file\": \"$B64\"}"
    curl -s -X POST -H "Content-Type: application/json" -H "ID: $ID" -d "$JSON" "$SERVER"
done
```

#### 🔢 MATLAB
```matlab
server = 'http://127.0.0.1:3753';
options = weboptions('HeaderFields', {'ComputerName', getenv('COMPUTERNAME')}, 'Timeout', 30);

while true
    % 1. Get Job
    job = webread(server, options);
    if isfield(job, 'message'), break; end
    
    fprintf('Job %d\n', job.id);
    
    % 2. Do Work
    resultData = rand(5); 
    save('temp.mat', 'resultData');
    
    % 3. Encode & Upload
    fid = fopen('temp.mat', 'rb'); 
    raw = fread(fid, '*uint8'); 
    fclose(fid);
    
    b64 = matlab.net.base64encode(raw);
    structData = struct('file_name', sprintf('res_%d.mat', job.id), 'file', b64);
    
    postOpts = weboptions('MediaType', 'application/json', 'HeaderFields', {'ID', num2str(job.id)});
    webwrite(server, jsonencode(structData), postOpts);
end
```

#### 🇨 C++ (using cpr/libcurl)
```cpp
#include <cpr/cpr.h>
#include <nlohmann/json.hpp>
#include <iostream>
#include "base64.h" // Assumes a base64 helper exists

using json = nlohmann::json;

int main() {
    std::string url = "http://127.0.0.1:3753";
    
    while(true) {
        // 1. Get Job
        auto r = cpr::Get(cpr::Url{url}, cpr::Header{{"ComputerName", "CppNode"}});
        auto job = json::parse(r.text);
        
        if (job.contains("message")) break;
        
        int id = job["id"];
        std::cout << "Processing ID: " << id << std::endl;
        
        // 2. Do Work & Encode
        std::string result = "Calculation Data";
        std::string b64_result = base64_encode(result);
        
        // 3. Upload
        json payload = {
            {"file_name", "res_" + std::to_string(id) + ".txt"},
            {"file", b64_result}
        };
        
        cpr::Post(cpr::Url{url}, 
                  cpr::Body{payload.dump()},
                  cpr::Header{{"Content-Type", "application/json"}, {"ID", std::to_string(id)}});
    }
    return 0;
}
```

#### 🇨 C (using standard libcurl)
*Note: Requires generic linked list or string parsing for JSON without a heavy library.*
```c
#include <stdio.h>
#include <curl/curl.h>

int main(void) {
    CURL *curl;
    CURLcode res;
    
    curl = curl_easy_init();
    if(curl) {
        // Simple logic: Perform GET, parse ID manually, Perform POST
        // 1. GET
        curl_easy_setopt(curl, CURLOPT_URL, "http://127.0.0.1:3753");
        // ... (Callback to store response string omitted for brevity)
        // res = curl_easy_perform(curl);
        
        // 2. POST (Assume we have ID and Base64 string)
        struct curl_slist *headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        headers = curl_slist_append(headers, "ID: 1"); // Example ID
        
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, "{\"file_name\": \"res.txt\", \"file\": \"...\"}");
        
        res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);
    }
    return 0;
}
```

---

## 📊 Step 3: Launching the Dashboard

You can monitor the progress of experiments using the PHP files in the `utility/` folder.

### General Launch
If you have PHP installed, navigate to the `utility` folder and run:
```bash
cd utility
php -S 0.0.0.0:8080
```
Then access `http://localhost:8080/overview.php` in your browser.

### 🧬 Specific Launch for Evolab (WSL)
For the Evolab environment running via WSL, use the following command to launch the dashboard on port 34000 under the user 'ozan':

```bash
wsl -u ozan php -S 0.0.0.0:34000 utility/overview.php
```
*(Note: Using `overview.php` as the router script allows you to access it directly at `http://localhost:34000`)*.

---

## ⚠️ Requirements
*   **Server**: Python 3.x, `numpy`
*   **Dashboard**: PHP 7.0+
*   **Clients**: Any language supporting HTTP requests.