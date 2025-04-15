shared_params = {
    "pop": [100, 200, 500],
    # "repeat": [5],
    "algo1": [1,2,3,4],
    "algo2": [1,2,3,4],
    "algo3": [1,2,3,4],
    "algo4": [1,2,3,4]
}

# https://www.researchgate.net/publication/228932005_Benchmark_functions_for_the_CEC'2008_special_session_and_competition_on_large_scale_global_optimization
cec2008 = {
    "year": ["2008"],
    "maxFE": [3_000_000],
    "func": list(range(1,7)),
    "repeat": [25],
    "D": [1000]
}

cec2008_f7 = {
    "year": ["2008"],
    "maxFE": [22_500_000],
    "func": [7],
    "repeat": [25],
    "D": [7500]
}


# https://www.researchgate.net/profile/Ponnuthurai-Suganthan/publication/228849876_Problem_definitions_and_evaluation_criteria_for_the_CEC_2010_Competition_on_Constrained_Real-Parameter_Optimization/links/0fcfd51234eca3860e000000/Problem-definitions-and-evaluation-criteria-for-the-CEC-2010-Competition-on-Constrained-Real-Parameter-Optimization.pdf?origin=publication_detail&_tp=eyJjb250ZXh0Ijp7ImZpcnN0UGFnZSI6InB1YmxpY2F0aW9uIiwicGFnZSI6InB1YmxpY2F0aW9uRG93bmxvYWQiLCJwcmV2aW91c1BhZ2UiOiJwdWJsaWNhdGlvbiJ9fQ
cec2010 = {
    "maxFE": [600_000],
    "func": list(range(1, 19)),
    "repeat": [25],
    "year": ["2010"],
    "D": [30]
}

# https://www.researchgate.net/publication/261562928_Benchmark_Functions_for_the_CEC'2013_Special_Session_and_Competition_on_Large-Scale_Global_Optimization
cec2013 = {
    "maxFE": [3_000_000],
    "func": list(range(1, 16)),
    "repeat": [25],
    "year": ["2013"],
    "D": [1000]
}

# https://github.com/P-N-Suganthan/CEC2017-BoundContrained/blob/master/Definitions%20of%20%20CEC2017%20benchmark%20suite%20final%20version%20updated.pdf
cec2017 = {
    "maxFE": [1_000_000],
    "func": list(range(1, 29)),
    "repeat": [25],
    "year": ["2017"],
    "D": [100]
}


# https://github.com/P-N-Suganthan/2020-Bound-Constrained-Opt-Benchmark/blob/master/Definitions%20of%20%20CEC2020%20benchmark%20suite%20Bound%20Constrained.pdf
cec2020 = { 
    "maxFE": [10_000_000],
    "func": list(range(1, 11)),
    "repeat": [30],
    "year": ["2020"],
    "D": [20]
}

empty_param = {
    "maxFE": [1000],
    "func": [1],
    "repeat": [2],
    "year": ["2020"],
    "D": [20]
}



data_one, id_counter = generate_combined_data(
    shared_params,
    id_counter,
    # empty_param
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

prime_list = {1: 2, 2: 3, 3: 5, 4: 7}

grouped_sets = {}


for obj in data_one:
    vec = prime_list[obj['algo1']] * prime_list[obj['algo2']] * prime_list[obj['algo3']] * prime_list[obj['algo4']]

    # Create the group key
    group_key = f"{obj['year']}_F{obj['func']}_P{obj['pop']}"

    # Initialize the group if it doesn't exist
    if group_key not in grouped_sets:
        grouped_sets[group_key] = set()

    if vec in grouped_sets[group_key]:
        continue
    else:
        obj['id'] = id_counter
        id_counter += 1
        grouped_sets[group_key].add(vec)
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