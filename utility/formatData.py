import scipy.io
import pandas as pd
import os
from collections import defaultdict

def extract_data_from_mat(file_path):
    import numpy as np
    mat_data = scipy.io.loadmat(file_path, squeeze_me=True, struct_as_record=False)
    data = mat_data['data']

    func = int(data.func)
    year = str(data.year)
    adaptive = int(data.adaptive)
    pop = int(data.pop)  # <-- NEW

    if adaptive == 0:
        selectionMethods = data.selectionMethods
        selectionMethods_key = ','.join([f"{x:.4f}" for x in selectionMethods])
    else:
        selectionMethods_key = 'adaptive'

    finalFitness_raw = data.finalFitness

    fitness_list = []

    if isinstance(finalFitness_raw, np.ndarray):
        for cell in finalFitness_raw.flatten():
            if isinstance(cell, np.ndarray):
                fitness_list.append(cell)
            else:
                fitness_list.append(np.array(cell))
    else:
        fitness_list = [np.array(finalFitness_raw)]

    min_fitnesses = []
    for arr in fitness_list:
        try:
            arr_flat = arr.ravel()
            min_val = float(arr_flat.min())
            min_fitnesses.append(min_val)
        except Exception as e:
            print(f"Error reading fitness array in {file_path}: {e}")

    # Now includes pop in the key!
    return (func, year, selectionMethods_key, pop), min_fitnesses




def process_all_mat_files(folder_path):
    from collections import defaultdict
    results = defaultdict(list)

    for filename in os.listdir(folder_path):
        if filename.endswith('.mat'):
            file_path = os.path.join(folder_path, filename)
            try:
                key, min_fitnesses = extract_data_from_mat(file_path)
                results[key].extend(min_fitnesses)
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    # Convert grouped data into a DataFrame
    rows = []
    for (func, year, selectionMethods, pop), mins in results.items():
        row = {
            'func': func,
            'year': year,
            'selectionMethods': selectionMethods,
            'pop': pop,
            'repeat': len(mins),
        }
        for i, val in enumerate(mins, 1):
            row[f'min{i}'] = val
        rows.append(row)

    return pd.DataFrame(rows)


# === Set the folder path here ===
folder = "../server/data"

df = process_all_mat_files(folder)

# === Export to Excel ===
df.to_excel("final_fitness_summary_grouped.xlsx", index=False)
