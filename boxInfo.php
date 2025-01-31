<?php
if (isset($_GET['data'])) {
    $data = json_decode($_GET['data'], true);
    $dataId = $data['id']; // Extract data.id

    echo '<pre>';
    print_r($data);
    echo '</pre>';
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Info on Data <?php echo json_encode($dataId); ?></title>
</head>
<body>
    <button id="resetButton">Reset</button>

    <script>
        const dataId = <?php echo json_encode($dataId); ?>; // Inject PHP data.id into JavaScript

        document.getElementById('resetButton').addEventListener('click', function() {
            const serverUrl = "http://" + window.location.hostname + ":3753/reset"; // Use 'reset' endpoint
            const headers = {
                'index': dataId // Pass the extracted data.id as 'index' header
            };

            fetch(serverUrl, {
                method: 'GET',
                headers: headers
            })
            .then(response => {
                alert('Reset successful');
                window.close(); // Close the tab after success
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error occurred during reset');
            });
        });
    </script>
</body>
</html>
