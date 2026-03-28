cec_functions = [f"BBOB_{i}" for i in range(1, 25)]
dimensions = [2, 5, 10, 20, 40, 80, 100]
m_vals = [4, 8, 16]

shared_params_run1 = {
    "fun": cec_functions,
    "dim": dimensions,
    "inst": [1],
    "m_val": m_vals
}

shared_params_rest = {
    "fun": cec_functions,
    "dim": dimensions,
    "inst": list(range(2, 16)),
    "m_val": m_vals
}

single_params = {
    "algo": ["RGA_generational", "RGA_steady_state"]
}

mixed_params = {
    "algo": ["MISEGA_generational", "MISEGA_steady_state"],
    "recomb": ["intra", "inter"],
    "modality": ["uniform", "adaptive", "restart"]
}

data_array = []

# Batch 1: Run 1 for all configurations
data_single_run1, id_counter = generate_combined_data(shared_params_run1, id_counter, single_params)
data_mixed_run1, id_counter = generate_combined_data(shared_params_run1, id_counter, mixed_params)
data_array += data_single_run1 + data_mixed_run1

# Batch 2: Runs 2-15 for all configurations
data_single_rest, id_counter = generate_combined_data(shared_params_rest, id_counter, single_params)
data_mixed_rest, id_counter = generate_combined_data(shared_params_rest, id_counter, mixed_params)
data_array += data_single_rest + data_mixed_rest
