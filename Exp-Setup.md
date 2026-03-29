# Optimization Experiment Integration Workflow

This document provides system context to LLM agents acting in the `Parallel-Experiment-Runner` codebase. It outlines how experiment setups are defined, configured on the distributed server, and successfully received and mapped on execution clients.

---

## 🏗 System Architecture

The pipeline consists of three primary components whenever optimizations/experiments are constructed:

1. **The Blueprint** (`runner/setup_experiments.m`): 
   A MATLAB script containing the raw algorithms and definitions. It features the nested combinations (functions, dimensions, iteration runs, modifiers like population scales, etc.) to project millions of parameter combinations.
2. **The Server Generation** (`server/parameters_[EXPERIMENT].py`): 
   A Python script mimicking the permutations array of the `setup_experiments.m` via dynamic lists. It leverages `generate_combined_data` to output a master `data_array` representing the work queue for the clients.
3. **The Client Execution Map** (`runner/GetFromServer.m`):
   The active queue-pulling MATLAB script. It takes a JSON payload representing a single array item from the Server, maps the properties into proper `op` and `algo` MATLAB structs, and runs the designated optimization algorithm.

---

## 🛠 Standard Task Workflow for LLMs

Whenever an LLM is asked to integrate or implement an experiment from `setup_experiments.m`, it must execute the following sequential plan:

### Step 1: Analyze `setup_experiments.m`
- **Extract Permutations:** Identify all scaling bounds (e.g., `dim: [2,5,10,20,40,80,100]`), scaling multipliers (e.g., `m_val = {@(d)4*d, @(d)8*d, @(d)16*d}`), component modalities, schema arrays, etc. Calculate the total mathematical product of combinations.
- **Extract Static Constraints:** Identify all the algorithm structures remaining untouched through the run logic (e.g., static configuration items like `verbose`, `plotting`, crossover variables `c_p`, mutation rates).

### Step 2: Create Server Mapping (`server/parameters_[NAME].py`)
- Create a clear, concise Python script mirroring the permutations exactly.
- To maintain brevity, group combinations algorithmically. Rather than creating 4 identical structs, group `data.algo = ["AlgoVariant1", "AlgoVariant2"]` inside singular configuration objects using lists.
- Process configurations mathematically using `generate_combined_data` to stitch shared parameters and distinct structural variants together. 
- Output the `data_array`. Verify that `len(data_array)` exactly matches the iterations outlined in `setup_experiments.m`.

### Step 3: Implement Client Execution (`runner/GetFromServer.m`)
- Target the `runExperiment()` function. 
- Discard outdated or unsupported configuration blocks tied to legacy algorithms.
- Establish conditions mapping to `data.algo` received from the server payload.
- Compute dynamic parameters mathematically based on server multipliers (e.g., calculating population sizes like `algo.pop_size = data.m_val * 4 * op.dim;`).
- Map all static parameters accurately mirroring the `setup_experiments.m` constraints.
- Trigger the distinct runner functions containing your modified struct inputs.

> **Crucial Rule:** Do NOT hallucinate variables or structures. If an item like `algo.fasten` is not listed within the initialization arrays of `setup_experiments.m`, do not carry it over into `GetFromServer.m`, even if older variables exist in legacy templates. Remove them to ensure a 1:1 parity with the definition file!
