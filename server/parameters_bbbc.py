cec_functions = [f"CEC2013_{i}" for i in range(1, 16)]
dimensions = [2, 25, 50, 100, 500, 1000]
populations = [100, 500]
n_runs = [25]

shared_params = {
    "fun": cec_functions,
    "dim": dimensions,
    "repeat": n_runs
}


bbbc_params = {
    "algo": ["BBBC"],
    "pop_size": populations,
    "survival": ["replacement", "non-elitist"]
}

es_params = {
    "algo": ["ES"],
    "off_size": populations, 
    "survival": ["(µ+λ)", "(µ,λ)"],
    "mu_type": [1],
    "sigma_type": [1, 2, 3]
}


data_bbbc, id_counter = generate_combined_data(
    shared_params,
    id_counter,
    bbbc_params
)

data_es, id_counter = generate_combined_data(
    shared_params,
    id_counter,
    es_params
)

data_array = data_bbbc + data_es