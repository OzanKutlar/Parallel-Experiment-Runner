cec_functions = [f"BBOB_{i}" for i in range(1, 25)]
dimensions = [2, 5, 10, 20, 40, 80, 100]
n_runs = range(1, 16)
m_vals = [4, 8, 16]

shared_params = {
    "fun": cec_functions,
    "dim": dimensions,
    "inst": list(n_runs),
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

data_single, id_counter = generate_combined_data(shared_params, id_counter, single_params)
data_mixed, id_counter = generate_combined_data(shared_params, id_counter, mixed_params)

data_array = data_single + data_mixed
