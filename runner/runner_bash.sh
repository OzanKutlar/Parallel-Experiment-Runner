#!/bin/bash

# Configuration
SERVER="http://127.0.0.1:3753"
HOST=$(hostname)

echo "--- Bash Runner Started on $HOST ---"

while true; do
    # 1. Fetch Job
    # We use curl to get data. If server is down, this might fail, so we sleep on failure.
    RESPONSE=$(curl -s --max-time 10 -H "ComputerName: $HOST" "$SERVER")
    
    if [ -z "$RESPONSE" ]; then
        echo "Server unreachable. Retrying in 5s..."
        sleep 5
        continue
    fi

    # Check for "message" indicating end of experiments
    MSG=$(echo "$RESPONSE" | jq -r '.message // empty')
    if [ "$MSG" == "No more data left." ]; then
        echo ">> Done. No more jobs."
        break
    fi

    ID=$(echo "$RESPONSE" | jq -r '.id')
    echo ">> Running Job $ID..."

    # 2. Run Experiment (Example: just writing to a file)
    # In a real scenario, you might do: ./my_program --id $ID
    echo "This is the result for job $ID running on $HOST" > "temp_result.txt"
    
    # 3. Encode to Base64
    # -w 0 ensures no newlines in base64 output
    B64=$(base64 -w 0 "temp_result.txt")
    
    # 4. Construct JSON Payload
    JSON="{\"file_name\": \"res_${ID}.txt\", \"file\": \"$B64\"}"
    
    # 5. Upload
    curl -s -X POST \
         -H "Content-Type: application/json" \
         -H "ID: $ID" \
         -H "ComputerName: $HOST" \
         -d "$JSON" \
         "$SERVER"
    
    echo "   [Upload] Job $ID uploaded."
    
    # Cleanup
    rm "temp_result.txt"
done