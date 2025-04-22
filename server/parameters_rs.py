
shared_params = {
    "Dataset": ["Kilyos"],
    "sp": ["env1", "env2", "env3", "env4"],
    "algo": [15]
}

empty_param = {}



data_one, id_counter = generate_combined_data(
    shared_params,
    id_counter,
    empty_param
)

# data_two, id_counter = generate_combined_data(
    # shared_params2,
    # id_counter,
    # ga_params,
    # de_params,
    # pso_params,
    # bbbc_params
# )

# data_array = data_one + data_two
data_array = data_one