# 🏃 How to Build a Custom Experiment Runner

This guide explains how to build a client ("Runner") for the distributed experiment system. A Runner is a script or program that sits on a worker machine, repeatedly fetches jobs from the Server, executes them, and uploads the results.

## 📡 The API Protocol

The server communicates via standard HTTP (REST). Your runner needs to implement a simple `while(true)` loop.

### 1. Fetch a Job (GET)
**Endpoint:** `GET http://<SERVER_IP>:<PORT>/`
**Headers:**
*   `ComputerName`: The name of the worker machine (used for logging).

**Response (JSON):**
*   **Case A (Job Available):**
    ```json
    {
      "id": 15,
      "learning_rate": 0.01,
      "batch_size": 32,
      "algo": "CNN"
    }
    ```
*   **Case B (Finished):**
    ```json
    {
      "message": "No more data left."
    }
    ```

### 2. Execute Logic
Run your simulation, calculation, or executable using the parameters provided in the JSON response.
*   **Important:** You must generate a result file (text, json, image, binary, etc.).

### 3. Upload Results (POST)
**Endpoint:** `POST http://<SERVER_IP>:<PORT>/`
**Headers:**
*   `ComputerName`: The name of the worker machine.
*   `ID`: The `id` of the job you just finished (e.g., `15`).

**Body (JSON):**
The body must contain the filename and the **Base64 encoded** content of the file.

```json
{
  "file_name": "result_15.txt",
  "file": "<BASE64_STRING_OF_YOUR_FILE_CONTENT>"
}