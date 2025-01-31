<?php
if (isset($_GET['data'])) {
    $data = json_decode($_GET['data'], true);
    // Now you can use $data in your PHP code
    echo '<pre>';
    print_r($data);
    echo '</pre>';
}
?>
