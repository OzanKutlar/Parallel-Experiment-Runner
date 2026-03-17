cec_functions = [f"BBOB_{i}" for i in range(1, 25)]
dimensions = [2,5,10,20,40,80, 100];
populations = [100, 500]
n_runs = [15]

shared_params = {
    "fun": cec_functions,
    "dim": dimensions,
    "inst": n_runs
}


bbbc_params = {
    "algo": ["BBBC"],
    "bbbc_survival": ["replacement", "non-elitist"]
}

es_params = {
    "algo": ["ES", "ES-SA"],
    "es_survival": ["(µ+λ)", "(µ,λ)"],
    "mu_type": [1, 2]
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


data_array = data_bbbc + data_es + data_es_other