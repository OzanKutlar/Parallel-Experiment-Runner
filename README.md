# Parallel Experiment Runner

This project is designed to easily distribute and run large numbers of experiments across multiple computers in parallel using a simple API server. Each machine retrieves parameters, runs an experiment, and sends back results.

---

## 🔧 Step 1: Define Your Experiment Parameters

Start by creating your experiment parameters file. You can tweak the existing example and save it as something like `parameters_experiment.py`.

### Example `parameters_experiment.py`

```python
example_shared_params = {
    "combIdx": list(range(1, 5)),   # Will result in 4 different experiments
    "sp": ["env1", "env2", "env3", "env4"],  # Each experiment will get a different environment
    "algo": [15]  # This parameter remains constant across all experiments
}
```

> Note: Each experiment is also automatically assigned a unique `id` parameter by the server.

---

## 🌐 Step 2: Modify Your Project to Use the API

Each experiment must communicate with the central API server:

- **GET requests** fetch a new experiment to run.
- **POST requests** send back results.

### 📥 GET Request (First Time)

All experiment requests should hit the root endpoint, e.g., `http://localhost:3753`.

> **Include a random startup delay to avoid flooding the server!**  
> Use a delay of about **1/5 the number of total computers**.

### ✅ Example MATLAB GET Code (First Request Only)

```matlab
url = sprintf('http://localhost:3753');
computerName = getenv('COMPUTERNAME');
options = weboptions('HeaderFields', {'ComputerName', computerName});
data = webread(url, options);
```

Example server response:
```json
{
  "combIdx": 1,
  "sp": "env1",
  "algo": "rrt",
  "id": 1
}
```

MATLAB automatically parses the response, so you can access `data.sp`, `data.id`, etc.

---

### 🔄 GET Request (Subsequent Calls)

**Important:** After your experiment finishes, you must **include the `ID` header** in the next GET request. This tells the server what experiment you just finished and prevents data loss.

```matlab
options = weboptions('HeaderFields', {
    'ComputerName', computerName;
    'ID', num2str(data.id)
});
data = webread(url, options);
```

---

## 📤 POST Request – Sending Results

Once an experiment is done, send back the result file with a POST request.

**POST Requirements:**

- Headers:
  - `ComputerName`
  - `ID` (the experiment ID)
- JSON Body:
  ```json
  {
    "file_name": "exp_1.mat",
    "file": "<base64_encoded_file_contents>"
  }
  ```

> If you do **not** implement this step, see shutdown guidance below.

---

## 🛑 No More Experiments

When there are no more experiments left, the server will respond with:

```json
{ "message": "No more data left." }
```

### Example MATLAB Handling

```matlab
if isfield(data, 'message')
    fprintf('Stopping with message: %s\nI ran %d experiments.\n', data.message, i);
    !start selfDestruct.bat
    return
end
```

> If you're not using POST, replace the line with:
```matlab
!shutdown /s /t 360
!taskkill /F /im "matlab.exe"
```

---

## 💣 Step 3: Self-Destruct (Recommended)

To clean up automatically, write a script similar to `selfDestruct.bat` that deletes the experiment folder after it's done.

---

## 📦 Step 4: Distribute the Project

Once everything is ready:
- Zip the entire folder.
- Send it to all target machines (e.g., using [Veyon](https://veyon.io)).

---

## 📂 Step 5: Unzip on Each Machine

Use PowerShell to unzip the archive on each remote machine:

```powershell
powershell -Command Expand-Archive "%Absolute Path to zip%"
```

---

## ▶️ Step 6: Start the Experiment

Launch the experiment runner from MATLAB like this:

```bash
matlab -sd "%Path_to_running_folder%" -r "GetFromServer('171.22.173.112', 30)"
```

- `Path_to_running_folder`: The path where the zip was extracted.
- `171.22.173.112`: Replace with the server's IP.
- `30`: Random delay.

---

## ✅ Summary

- Define experiment parameters
- Connect your experiment to the API (GET + POST)
- Add a delay to avoid server overload
- Include `ID` header in subsequent GETs
- Handle end-of-experiment response
- Distribute, unzip, and run

---

For any bugs or contributions, feel free to open an issue or pull request.

Happy experimenting! 🚀