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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --primary-color: #2c3e50;
            --secondary-color: #ecf0f1;
            --accent-color: #3498db;
            --success-color: #27ae60;
            --warning-color: #e74c3c;
            --running-color: #9b59b6;
            --waiting-color: #e74c3c;
            --border-radius: 12px;
            --box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            --transition-speed: 0.3s;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
            color: var(--primary-color);
            line-height: 1.6;
        }

        .container {
            display: grid;
            grid-template-columns: 7fr 1fr;
            width: 100vw;
            height: 100vh;
            overflow: hidden;
        }

        .left {
            display: flex;
            flex-wrap: wrap;
            padding: 20px;
            gap: 15px;
            align-content: flex-start;
            overflow-y: auto;
        }

        .experiment-box {
            width: 120px;
            height: 120px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 16px;
            flex-direction: column;
            border-radius: var(--border-radius);
            cursor: pointer;
            text-align: center;
            word-wrap: break-word;
            white-space: normal;
            box-shadow: var(--box-shadow);
            transition: all var(--transition-speed) ease;
            background-color: var(--waiting-color);
            position: relative;
            overflow: hidden;
        }

        .experiment-box:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }

        .experiment-box.running {
            background-color: var(--running-color);
        }

        .experiment-box.finished {
            background-color: var(--success-color);
        }

        .experiment-box .status-icon {
            font-size: 24px;
            margin-bottom: 5px;
        }

        .right {
            width: 12.5%;
            position: fixed;
            right: 0;
            top: 0;
            bottom: 0;
            background-color: var(--secondary-color);
            padding: 15px;
            box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
        }

        .sidebar-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            color: var(--primary-color);
            border-bottom: 2px solid var(--accent-color);
            padding-bottom: 10px;
        }

        .sidebar-header i {
            margin-right: 8px;
            color: var(--accent-color);
        }

        #announcements {
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
            padding-right: 5px;
        }

        .announcement {
            background: white;
            padding: 12px;
            border-left: 4px solid var(--accent-color);
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            opacity: 0;
            transition: opacity 0.5s ease;
            font-size: 14px;
        }

        .announcement .time {
            font-size: 12px;
            color: #7f8c8d;
            margin-top: 5px;
        }

        .control-button {
            background-color: var(--accent-color);
            color: white;
            border: none;
            padding: 12px;
            border-radius: var(--border-radius);
            cursor: pointer;
            font-weight: bold;
            margin-top: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background-color var(--transition-speed);
        }

        .control-button:hover {
            background-color: #2980b9;
        }

        .control-button i {
            margin-right: 8px;
        }

        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb {
            background: #b3b3b3;
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #888;
        }

        @media (max-width: 1200px) {
            .container {
                grid-template-columns: 3fr 1fr;
            }
            
            .right {
                width: 25%;
            }
        }

        @media (max-width: 768px) {
            .container {
                grid-template-columns: 1fr;
                grid-template-rows: 3fr 1fr;
            }
            
            .right {
                position: relative;
                width: 100%;
                height: 100%;
            }
            
            .experiment-box {
                width: calc(50% - 15px);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="left">
            <?php for ($i = 1; $i <= $numBoxes; $i++): ?>
                <div class="experiment-box" id="box-<?php echo $i; ?>" onclick="redbox(<?php echo $i; ?>)">
                    <div class="status-icon"><i class="fas fa-hourglass-half"></i></div>
                    <div class="box-content"><?php echo $i; ?> is Waiting</div>
                </div>
            <?php endfor; ?>
        </div>
        <div class="right">
            <div class="sidebar-header">
                <i class="fas fa-clipboard-list"></i>
                <h3>Activity Log</h3>
            </div>
            <div id="announcements"></div>
            <button class="control-button" onclick="fetchAll()">
                <i class="fas fa-sync"></i>Refresh All
            </button>
        </div>
    </div>
    
    <script>
        let lastLog = -1;
        let lastState = -1;
        
        function fetchAll() {
            fetchLogs();
            fetchStates();
        }
        
        function fetchLogs() {
            const serverUrl = "http://" + window.location.hostname + ":3753/logs";
            const headers = {
                'lastLog': lastLog
            };

            fetch(serverUrl, {
                method: 'GET',
                headers: headers
            })
            .then(response => response.json())
            .then(data => {
                console.log("Logs received:", data);
                addAnnouncements(data);
            })
            .catch(error => {
                console.error("Error fetching logs:", error);
                showErrorAnnouncement("Failed to fetch logs");
            });
        }
        
        function fetchStates() {
            const serverUrl = "http://" + window.location.hostname + ":3753/status";
            const headers = {
                'lastLog': lastState
            };

            fetch(serverUrl, {
                method: 'GET',
                headers: headers
            })
            .then(response => response.json())
            .then(data => {
                console.log("States received:", data);
                changeStates(data);
            })
            .catch(error => {
                console.error("Error fetching states:", error);
                showErrorAnnouncement("Failed to fetch states");
            });
        }
        
        function changeStates(states) {
            states.forEach(state => {
                console.log("Updating ID " + state.index);
                changeBox(state);
                lastState = state.ID;
            });
        }
        
        function changeBox(state) {
            let boxNumber = state.index;
            var box = document.getElementById('box-' + boxNumber);
            if (!box) return;
            
            let textToPut = '';
            let iconClass = '';
            
            // Remove all state classes first
            box.classList.remove('running', 'finished');
            
            if (state.state === "Finished") {
                textToPut = `${boxNumber} was Finished by ${state.sentTo}`;
                iconClass = 'fas fa-check-circle';
                box.classList.add('finished');
            } else if (state.state === "Running") {
                textToPut = `${boxNumber} is Running on ${state.sentTo}`;
                iconClass = 'fas fa-cog fa-spin';
                box.classList.add('running');
            } else if (state.state === "Reset") {
                textToPut = `${boxNumber} is Waiting`;
                iconClass = 'fas fa-hourglass-half';
                // Default class is already waiting
            }

            box.querySelector('.box-content').textContent = textToPut;
            box.querySelector('.status-icon').innerHTML = `<i class="${iconClass}"></i>`;
        }
        
        function redbox(boxNumber) {
            const serverUrl = "http://" + window.location.hostname + ":3753/info";
            const headers = {
                'index': boxNumber
            };

            fetch(serverUrl, {
                method: 'GET',
                headers: headers
            })
            .then(response => response.json())
            .then(data => {
                console.log("Box info received:", data);

                const width = 600;
                const height = 400;

                const left = (window.innerWidth / 2) - (width / 2);
                const top = (window.innerHeight / 2) - (height / 2);
                
                const encodedData = encodeURIComponent(JSON.stringify(data));
                
                const newWindow = window.open("boxInfo.php?data=" + encodedData, "_blank", `width=${width},height=${height},left=${left},top=${top}`);
                
                if (newWindow) {
                    const interval = setInterval(() => {
                        if (newWindow.closed) {
                            fetchStates();
                            clearInterval(interval);
                        }
                    }, 100);
                } else {
                    showErrorAnnouncement("Popup blocked. Please allow popups for this site.");
                }
            })
            .catch(error => {
                console.error("Error fetching box info:", error);
                showErrorAnnouncement("Failed to load box information");
            });
        }

        function addAnnouncements(logs) {
            let announcements = document.getElementById("announcements");

            logs.forEach(log => {
                let announcement = document.createElement("div");
                announcement.classList.add("announcement");
                
                const message = document.createElement("div");
                message.className = "message";
                message.textContent = log.Text;
                
                const time = document.createElement("div");
                time.className = "time";
                time.textContent = log.time;
                
                announcement.appendChild(message);
                announcement.appendChild(time);

                if (announcements.children.length >= 30) {
                    announcements.removeChild(announcements.lastChild);
                }
                
                announcements.prepend(announcement);
                setTimeout(() => announcement.style.opacity = 1, 50);
                lastLog = log.ID;
            });
        }
        
        function showErrorAnnouncement(message) {
            let announcements = document.getElementById("announcements");
            let announcement = document.createElement("div");
            announcement.classList.add("announcement");
            announcement.style.borderLeft = "4px solid #e74c3c";
            
            const messageEl = document.createElement("div");
            messageEl.className = "message";
            messageEl.textContent = message;
            
            const time = document.createElement("div");
            time.className = "time";
            time.textContent = new Date().toLocaleTimeString();
            
            announcement.appendChild(messageEl);
            announcement.appendChild(time);
            
            announcements.prepend(announcement);
            setTimeout(() => announcement.style.opacity = 1, 50);
        }
        
        window.onload = function() {
            fetchAll();
            setInterval(fetchAll, 2000);  // Changed to 2 seconds to be less resource-intensive
        }
    </script>
</body>
</html>