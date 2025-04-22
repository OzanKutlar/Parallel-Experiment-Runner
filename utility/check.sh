#!/bin/bash

# Check if the correct number of arguments is provided
if [[ $# -ne 2 ]]; then
    echo "Usage: $0 /path/to/folder max_number"
    exit 1
fi

# Assign arguments to variables
folder_path="$1"
end="$2"

# Ensure the maximum number is a positive integer
if ! [[ "$end" =~ ^[0-9]+$ ]]; then
    echo "Error: max_number must be a positive integer."
    exit 1
fi

# Define the start of the range
start=1

# Loop through the range
for ((i=start; i<=end; i++)); do
    file_name="exp-${i}.mat"
    if [[ ! -f "$folder_path/$file_name" ]]; then
        echo "Missing: $file_name"
        ((missing_count++))
    fi
done

# Print the total number of missing files
echo "Total missing files: $missing_count"
