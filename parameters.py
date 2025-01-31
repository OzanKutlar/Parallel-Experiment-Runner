
shared_params = {
    "task":["firstTask", "secondTask", "thirdTask"],
    "pop": [500],
    "runs": [30],
    "generation": [350]
}

shared_params2 = {
    "task":["firstTask", "secondTask", "thirdTask"],
    "pop": [[500, 200], [200, 300]],
    "runs": [20],
    "generation": [350]
}

ga_params = {
    "algo": ["ga"],
    "mut": [-1.0, 0.2, 0.4, 0.6],
    "cross": [0.5, 0.419, 0.381],
    "elitist": ["elitist_full"]

}

de_params = {
    "algo": ["de"],
    "variant": [1, 2, 3, 4, 5, 6],
    "scalingFactor": [0.5, 0.75, 1.0]
    
}

pso_params = {
    "algo": ["pso"],
    "omega": [0.6, 0.8, 1.0],
    "cognitiveConstant": [0.5, 2.5, 5.0],
    "socialConstant": [0.5, 2.5, 5.0]

}

bbbc_params = {
    "runs": [50],
    "algo": ["bbbc"]

}


data_one, id_counter = generate_combined_data(
    shared_params,
    id_counter,
    ga_params,
    de_params,
    pso_params,
    bbbc_params
)

data_array = data_one