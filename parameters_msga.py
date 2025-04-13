shared_params = {
    "pop": [100, 200, 500],
    # "repeat": [5],
    "algo1": [1,2,3,4],
    "algo2": [1,2,3,4],
    "algo3": [1,2,3,4],
    "algo4": [1,2,3,4]
}

cec2008 = {
    "year": ["2008"],
    "maxFE": [5_000_000],
    "func": list(range(1,7)),
    "repeat": [30],
    "D": [1000]
}

cec2008_f7 = {
    "year": ["2008"],
    "maxFE": [37_500_000],
    "func": [7],
    "repeat": [30],
    "D": [7500]
}

cec2010 = {
    "maxFE": [300_000],
    "func": list(range(1, 19)),
    "repeat": [25],
    "year": ["2010"],
    "D": [30]
}

cec2013 = {
    "maxFE": [3_000_000],
    "func": list(range(1, 16)),
    "repeat": [25],
    "year": ["2013"],
    "D": [1000]
}


cec2017 = {
    "maxFE": [2_000_000],
    "func": list(range(1, 29)),
    "repeat": [25],
    "year": ["2017"],
    "D": [100]
}

cec2020 = {
    "maxFE": [1_000_000],
    "func": list(range(1, 11)),
    "repeat": [30],
    "year": ["2020"],
    "D": [100]
}

empty_param = {}



data_one, id_counter = generate_combined_data(
    shared_params,
    id_counter,
    cec2008,
    cec2008_f7,
    cec2010,
    cec2013,
    cec2017,
    cec2020
)


pruned_list = []
id_counter = 1
funcVal = None

grouped_sets = {}

for obj in data_one:
    vec = sorted([obj['algo1'], obj['algo2'], obj['algo3'], obj['algo4'], obj['pop']])
    vec_tuple = tuple(vec)

    # Create the group key
    group_key = f"{obj['year']}_F{obj['func']}"

    # Initialize the group if it doesn't exist
    if group_key not in grouped_sets:
        grouped_sets[group_key] = set()

    if vec_tuple in grouped_sets[group_key]:
        continue
    else:
        obj['id'] = id_counter
        id_counter += 1
        grouped_sets[group_key].add(vec_tuple)
        pruned_list.append(obj)




# print_list_as_json(pruned_list);
# exit();

# data_two, id_counter = generate_combined_data(
    # shared_params2,
    # id_counter,
    # ga_params,
    # de_params,
    # pso_params,
    # bbbc_params
# )

# data_array = data_one + data_two
data_array = pruned_list