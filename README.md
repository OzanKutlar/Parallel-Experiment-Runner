# 🧪 Parallel Experiment Runner

A lightweight Python server and a simple API-based protocol for distributing and executing experiments in parallel across multiple computers—perfect for large-scale simulations or distributed research tasks.

---

## 🚀 Getting Started

This guide will walk you through setting up your experiments and running them on multiple machines.

### 1. Define Your Experiment Parameters

Start by creating a parameter definition file based on the example.

```python
# parameters_experiment.py

example_shared_params = {
    "combIdx": list(range(1, 5)),        # Multiple values: creates 4 experiments
    "sp": ["env1", "env2", "env3", "env4"],  # Another variable to test over
    "algo": [15],                        # Static value for all experiments
}
```

> 💡 Each experiment will be automatically assigned a unique `id` in addition to the parameters you define.

---

### 2. Modify Your Project to Communicate with the Server

Each client machine (running experiments) must:

#### ✅ GET a Task

Send a GET request to the root endpoint (`http://<server_ip>:3753`). The server responds with a JSON object representing an experiment configuration.

**✅ Add these headers:**
- `ComputerName`: your machine's name (`getenv('COMPUTERNAME')` in MATLAB)
- Optional: `ID` of the previous experiment (if re-requesting or retrying)

**🧪 Example MATLAB GET Request:**
```matlab
url = sprintf('http://localhost:3753');
computerName = getenv('COMPUTERNAME');
options = weboptions('HeaderFields', {'ComputerName', computerName});
data = webread(url, options);

% Access values like:
% data.combIdx, data.sp, data.algo, data.id
```

> 🧊 If no tasks remain, the server will respond with:
```json
{"message": "No more data left."}
```
You should exit the client at this point.

```matlab
if isfield(data, 'message')
    fprintf('Stopping with message : %s\nI ran %d experiments.\n', data.message, i);
    !start selfDestruct.bat
    return
end
```

> 🔄 Not using POST to report results? Replace `!start selfDestruct.bat` with:
```matlab
!shutdown /s /t 360
!taskkill /F /im "matlab.exe"
```

#### 📤 POST Results (Optional)

If you’re using POST, check the `uploadFileToServerAsJSON` function in `GetFromServer.m` for uploading your result files back to the server.

---

### 3. (Optional) Auto-Termination After Completion

Add a `selfDestruct.bat` file to your project so that it gracefully shuts down the client machine once all experiments are done. You can also directly embed the shutdown code as shown above.

---

### 4. Distribute Your Project

Compress your entire experiment project folder:

```bash
# Example structure:
MyExperiment/
├── GetFromServer.m
├── parameters_experiment.py
├── selfDestruct.bat
├── your_scripts.m
└── ...
```

> ✅ Zip it up and distribute to remote machines using tools like **Veyon**.

---

### 5. Unzip Remotely

On the client machine, unzip with PowerShell:

```powershell
powershell -Command Expand-Archive "C:\path\to\your.zip"
```

---

### 6. Run the Experiment Client

Launch MATLAB and run your fetch-execute loop:

```bash
matlab -sd "C:\path\to\unzipped_folder" -r "GetFromServer('171.22.173.112', 30)"
```

- Replace `171.22.173.112` with your server’s IP.
- `30` is an optional delay between retries or failed attempts.

---

## 📂 Repository Structure

```
Parallel-Experiment-Runner/
├── server.py                  # API server that distributes experiments
├── create_comb_from_shared.py # Builds experiment combinations
├── parameters_example.py      # Parameter file template
├── README.md                  # You're reading it!
└── ...
```

---

## 🛠 Requirements

- Python 3.x (for the server)
- MATLAB (on client machines)

---

## 📬 Contact

Feel free to open an issue or fork the repo for improvements.

👉 [GitHub Repo](https://github.com/OzanKutlar/Parallel-Experiment-Runner)

