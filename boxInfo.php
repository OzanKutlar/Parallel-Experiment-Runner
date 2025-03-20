<?php
if (isset($_GET['data'])) {
    $data = json_decode($_GET['data'], true);
    $dataId = $data['id']; // Extract data.id
    echo '<pre class="data-display">';
    print_r($data);
    echo '</pre>';
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Info on Data <?php echo isset($dataId) ? htmlspecialchars($dataId) : ''; ?></title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: #fff;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #2c3e50;
            margin-top: 0;
        }
        .data-display {
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            padding: 15px;
            border-radius: 4px;
            overflow: auto;
            font-family: monospace;
            margin-bottom: 20px;
        }
        button {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #2980b9;
        }
        .status {
            margin-top: 15px;
            padding: 10px;
            border-radius: 4px;
            display: none;
        }
        .success {
            background-color: #d4edda;
            color: #155724;
        }
        .error {
            background-color: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="container">
        
        <button id="resetButton">Reset Data</button>
        <div id="statusMessage" class="status"></div>
    </div>

    <script>
        const dataId = <?php echo isset($dataId) ? json_encode($dataId) : 'null'; ?>;
        
        document.getElementById('resetButton').addEventListener('click', function() {
            if (!dataId) {
                showStatus('No data ID available', 'error');
                return;
            }
            
            const serverUrl = "http://" + window.location.hostname + ":3753/reset";
            const headers = {
                'index': dataId
            };
            
            fetch(serverUrl, {
                method: 'GET',
                headers: headers
            })
            .then(response => {
                if (response.ok) {
                    showStatus('Reset successful', 'success');
                    setTimeout(() => window.close(), 1500);
                } else {
                    throw new Error('Server returned ' + response.status);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showStatus('Error occurred during reset: ' + error.message, 'error');
            });
        });
        
        function showStatus(message, type) {
            const statusEl = document.getElementById('statusMessage');
            statusEl.textContent = message;
            statusEl.className = 'status ' + type;
            statusEl.style.display = 'block';
        }
    </script>
</body>
</html>