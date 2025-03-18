
shared_params = {
    "iteration":[500, 1000, 1500],
    "stepSize": [2, 4, 8, 16, 32],
    "pOfGoal": [0.1],
    "pOfVC": [0.2],
    "sp": ["env1", "env2", "env3", "env4"],
    "algo": ["rrt", "rrt-soft", "rrt-star", "rrt-star-soft", "bi-rrt-star", "bi-rrt-star-soft"]
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