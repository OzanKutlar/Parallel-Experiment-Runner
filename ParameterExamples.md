# Experiment Parameter Configuration

The server expects a Python file (passed via the `--file` argument) that defines the specific jobs to be distributed. The server's internal logic generates a **Cartesian Product** (every possible combination) of the lists provided in your dictionaries.

Here are several patterns to help you define your experiments.

## 1. The Basic Grid Search
If you want to run every combination of a set of parameters, define a single dictionary.

```python
# parameters_grid.py

# Define the search space
params = {
    "dataset": ["CIFAR-10", "MNIST"],
    "learning_rate": [0.1, 0.01, 0.001],
    "batch_size": [32, 64]
}

# The server looks for 'data_array'
# shared_params is empty because everything is in 'params'
data_array, _ = generate_combined_data({}, 1, params)

# Result (12 experiments):
# CIFAR, 0.1, 32
# CIFAR, 0.1, 64
# CIFAR, 0.01, 32
# ...
# MNIST, 0.001, 64
```

## 2. Algorithm-Specific Parameters (Branching)
Often, different algorithms require different hyperparameters (e.g., a Random Forest needs `n_estimators`, but a Neural Network needs `epochs`). You can branch these so they don't mix.

```python
# parameters_algo.py

# Parameters common to ALL experiments
shared_settings = {
    "dataset": ["Weather_Data", "Stock_Data"],
    "folds": [5]
}

# Branch 1: Random Forest
rf_params = {
    "algorithm": ["RandomForest"],
    "n_estimators": [100, 200],
    "max_depth": [10, 20, None]
}

# Branch 2: SVM (Support Vector Machine)
svm_params = {
    "algorithm": ["SVM"],
    "C": [0.1, 1, 10],
    "kernel": ["linear", "rbf"]
}

# Generate combinations for RF
data_rf, id_counter = generate_combined_data(
    shared_settings, 
    1,             # Start ID at 1
    rf_params
)

# Generate combinations for SVM (pass updated id_counter)
data_svm, id_counter = generate_combined_data(
    shared_settings, 
    id_counter,    # Continue IDs where RF left off
    svm_params
)

# Combine them
data_array = data_rf + data_svm
```

## 3. Fixed Pairings (Zip-like behavior)
The default behavior is combinatorial. If you want specific pairs (e.g., `Large_Dataset` should *only* run with `High_RAM_Mode`, and `Small_Dataset` with `Low_RAM_Mode`), you must define them as separate branches.

```python
# parameters_paired.py

# Group A
group_a = {
    "dataset": ["Large_DB_1", "Large_DB_2"],
    "memory_mode": ["high_performance"],
    "batch_size": [1024]
}

# Group B
group_b = {
    "dataset": ["Small_DB_1"],
    "memory_mode": ["low_power"],
    "batch_size": [32]
}

data_a, id_counter = generate_combined_data({}, 1, group_a)
data_b, id_counter = generate_combined_data({}, id_counter, group_b)

data_array = data_a + data_b
```

## 4. Dynamic/Programmatic Generation
Since this is a standard Python file, you can use loops, list comprehensions, or math to generate parameters dynamically.

```python
# parameters_math.py
import numpy as np

# Generate logarithmic learning rates
lrs = list(np.logspace(-4, -1, 5))  # [0.0001, ..., 0.1]

# Generate seeds 1 to 50
seeds = list(range(1, 51))

params = {
    "learning_rate": lrs,
    "seed": seeds,
    "optimizer": ["adam"]
}

data_array, _ = generate_combined_data({}, 1, params)
```

## 5. Monte Carlo / Repeats
If you need to run the exact same configuration multiple times (e.g., to average stochastic results), simply add a `run_id` parameter.

```python
# parameters_repeats.py

params = {
    "problem": ["TSP", "Knapsack"],
    "solver": ["GeneticAlgo"],
    "run_id": list(range(1, 31)) # Run each combo 30 times
}

data_array, _ = generate_combined_data({}, 1, params)
```