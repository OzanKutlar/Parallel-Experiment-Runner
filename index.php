<?php
    $numBoxes = file_get_contents('http://localhost:3753/getNum');
    $numBoxes = is_numeric($numBoxes) ? (int)$numBoxes : 10; // Fallback to 10 if invalid
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Experiment Checker</title>
    <style>
        body {
            display: flex;
            margin: 0;
            font-family: Arial, sans-serif;
        }
        .container {
            display: grid;
            grid-template-columns: 7fr 1fr;
            width: 100vw;
            height: 100vh;
        }
        .left {
            display: flex;
            flex-wrap: wrap;
            padding: 20px;
            gap: 10px;
        }
		.red-box {
            width: 100px;
            height: 100px;
            background-color: red;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 20px;
            flex-direction: column;
            border-radius: 15px; /* Rounded corners */
        }
        .right {
            width: 12.5%; /* 1/8th of the screen */
            position: fixed;
            right: 0;
            top: 0;
            bottom: 0;
            background-color: #f1f1f1;
            padding: 10px;
            overflow: hidden;
        }
        #announcements {
            max-height: 90vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .announcement {
            background: white;
            padding: 10px;
            border: 1px solid #ccc;
            opacity: 0;
            transition: opacity 1s;
        }
        button {
            margin-top: 10px;
            width: 100%;
            padding: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="left">
            <?php for ($i = 1; $i <= $numBoxes; $i++): ?>
                <div class="red-box">
                    <div>Box <?php echo $i; ?></div>
                </div>
            <?php endfor; ?>
        </div>
        <div class="right">
            <h3>Log</h3>
            <div id="announcements"></div>
            <button onclick="addAnnouncement()">Add Announcement</button>
        </div>
    </div>
    
    <script>
        function addAnnouncement() {
            let announcements = document.getElementById("announcements");
            let announcement = document.createElement("div");
            announcement.classList.add("announcement");
            announcement.innerHTML = "New announcement at " + new Date().toLocaleTimeString();
            
            if (announcements.children.length >= 5) {
                announcements.removeChild(announcements.lastChild);
            }
            
            announcements.prepend(announcement);
            setTimeout(() => announcement.style.opacity = 1, 100);
        }
    </script>
</body>
</html>
