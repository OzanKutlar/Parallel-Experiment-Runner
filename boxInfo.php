<?php
if (isset($_GET['data'])) {
    $data = json_decode($_GET['data'], true);
    echo '<pre>';
    print_r($data);
    echo '</pre>';
}
?>
