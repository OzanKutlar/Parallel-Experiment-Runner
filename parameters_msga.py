shared_params = {
    "maxFE": [200000],
    "pop": [100],
    "func": list(range(1,11)),
    "algo1": [1,2,3,4],
    "algo2": [1,2,3,4],
    "algo3": [1,2,3,4],
    "algo4": [1,2,3,4]
}

empty_param = {}



data_one, id_counter = generate_combined_data(
    shared_params,
    id_counter,
    empty_param
)


seen = set()
pruned_list = []
id_counter = 1
funcVal = None

for obj in data_one:
    
    if not funcVal or funcVal != obj['func']:
        seen = set()
        funcVal = obj['func']

    vec = sorted([obj['algo1'], obj['algo2'], obj['algo3'], obj['algo4']])
    vec_tuple = tuple(vec)  # Tuples are hashable and can go in a set

    if vec_tuple in seen:
        continue
    else:
        obj['id'] = id_counter
        id_counter += 1
        seen.add(vec_tuple)
        pruned_list.append(obj)




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