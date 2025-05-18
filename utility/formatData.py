import os
import scipy.io
import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter

# Configuration
directory = "../server/data"
max_number = 1000  # adjust based on how many exp files you have
output_excel = "experiment_summary.xlsx"

# Gather data grouped by (year, func)
grouped_data = {}

for i in range(1, max_number + 1):
    file_name = f"exp-{i}.mat"
    file_path = os.path.join(directory, file_name)

    if not os.path.exists(file_path):
        continue

    mat = scipy.io.loadmat(file_path)
    data = mat['data']

    # Flatten structured array if necessary
    if isinstance(data, np.ndarray) and data.dtype.names:
        data = data[0, 0]

    year = str(data['year'][0])
    func = int(data['func'][0][0])
    repeats = int(data['repeat'][0][0])
    selection_methods = str(data['selectionMethods']) if data['adaptive'] == 0 else "Adaptive"
    final_fitness = data['finalFitness']

    # Extract the best fitness value from each repetition
    best_fitness_per_repeat = []
    for j in range(repeats):
        fitness_values = final_fitness[0][j].flatten()
        if fitness_values.size > 0:
            best_fitness_per_repeat.append(min(fitness_values))
        else:
            best_fitness_per_repeat.append(None)

    key = (year, func)
    grouped_data.setdefault(key, []).append({
        'selection_method': selection_methods,
        'best_fitnesses': best_fitness_per_repeat
    })

# Create Excel Workbook
wb = Workbook()
ws = wb.active
ws.title = "Experiment Results"

row_pointer = 1

for (year, func), experiments in grouped_data.items():
    title = f"CEC{year}_F{func}"
    num_repeats = len(experiments[0]['best_fitnesses'])



    # Create DataFrame
    columns = [f"{m['selection_method']}" for m in experiments]
    df = pd.DataFrame(index=[f"Repeat {i+1}" for i in range(num_repeats)])
    
    
    for e in experiments:
        df[e["selection_method"]] = e["best_fitnesses"]

    # Merge header and write title
    start_col = 1
    end_col = start_col + df.shape[1]
    ws.merge_cells(start_row=row_pointer, start_column=start_col, end_row=row_pointer, end_column=end_col)
    cell = ws.cell(row=row_pointer, column=start_col)
    cell.value = title
    cell.alignment = Alignment(horizontal='center')
    row_pointer += 1

    # Write DataFrame
    for r in dataframe_to_rows(df.reset_index(), index=False, header=True):
        for c_idx, value in enumerate(r, start=1):
            ws.cell(row=row_pointer, column=c_idx, value=value)
        row_pointer += 1

    row_pointer += 2  # spacing between tables

# Save workbook
wb.save(output_excel)
print(f"Excel report saved to: {output_excel}")
