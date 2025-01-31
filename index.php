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
            font-size: 15px;
            flex-direction: column;
            border-radius: 15px; /* Rounded corners */
            cursor: pointer; /* Indicate that the box is clickable */
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
                <div class="red-box" id="box-<?php echo $i; ?>" onclick="redbox(<?php echo $i; ?>)">
                    <div>Box <?php echo $i; ?></div>
                </div>
            <?php endfor; ?>
        </div>
        <div class="right">
            <h3>Log</h3>
            <div id="announcements"></div>
            <button onclick="fetchLogs()">Add Announcement</button>
        </div>
    </div>
    
    <script>
		let lastLog = -1; // Initialize lastLog variable
		let lastState = -1; // Initialize lastLog variable
		
        function fetchLogs() {
            let serverUrl = "http://" + window.location.hostname + ":3753/logs";
			
			const headers = {};
			
			headers['lastLog'] = lastLog;
			

			fetch(serverUrl, {
				method: 'GET',
				headers: headers
			})
            .then(response => response.json())
            .then(data => {
                console.log("Logs received:", data);
                addAnnouncements(data); // Process and add logs
            })
            .catch(error => console.error("Error fetching logs:", error));
			
			
			// States of the red boxes.
			
			headers['lastLog'] = lastState;
			
			serverUrl = "http://" + window.location.hostname + ":3753/status";

			fetch(serverUrl, {
				method: 'GET',
				headers: headers
			})
            .then(response => response.json())
            .then(data => {
                console.log("States received:", data);
                changeStates(data); // Process and add logs
            })
            .catch(error => console.error("Error fetching logs:", error));
        }
		
		function changeStates(states) {
            states.forEach(state => {
				console.log("Checking ID " + state.index)
				changeBox(state)
				lastState = state.ID;
            });
        }
		
		function changeBox(state) {
			let boxNumber = state.index + 1
			var box = document.getElementById('box-' + boxNumber);
			
			const textToPut = `<div><strong>ID</strong>: ${state.index}</div><div><strong>State</strong>: ${state.state}</div><div><strong>PC</strong>: ${state.sentTo}</div>`;
			
			box.querySelector('div').innerHTML = textToPut;

			box.style.transition = 'background-color 1s ease';
			if (state.state === "Finished") {
				box.style.backgroundColor = 'green';
			} else if (state.state === "Running") {
				box.style.backgroundColor = 'purple';
			} else if (state.state === "Reset") {
				box.style.backgroundColor = 'red';
			}
		}

		
		function redbox(boxNumber) {
            const serverUrl = "http://" + window.location.hostname + ":3753/info";
			
			const headers = {};
			
			headers['index'] = boxNumber;
			

			fetch(serverUrl, {
				method: 'GET',
				headers: headers
			})
            .then(response => response.json())
            .then(data => {
				console.log("Logs received:", data);

				const width = 600;
				const height = 400;

				const left = (window.innerWidth / 2) - (width / 2);
				const top = (window.innerHeight / 2) - (height / 2);
				
				const encodedData = encodeURIComponent(JSON.stringify(data));
				
				window.open("boxInfo.php?data=" + encodedData, "_blank", `width=${width},height=${height},left=${left},top=${top}`);
			})
            .catch(error => console.error("Error fetching logs:", error));
        }

        function addAnnouncements(logs) {
            let announcements = document.getElementById("announcements");

            logs.forEach(log => {
                let announcement = document.createElement("div");
                announcement.classList.add("announcement");
                announcement.innerHTML = `<strong>ID:</strong> ${log.ID} <br> <strong>Message:</strong> ${log.Text}`;

                if (announcements.children.length >= 5) {
                    announcements.removeChild(announcements.lastChild);
                }
                announcements.prepend(announcement);
                setTimeout(() => announcement.style.opacity = 1, 100);
				lastLog = log.ID;
            });
        }
		
		
    </script>
</body>
</html>
