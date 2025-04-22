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
            flex-direction: column;
            height: 100%;
            position: relative;
        }

        .boxes-container {
            display: flex;
            flex-wrap: wrap;
            padding: 20px;
            gap: 10px;
            align-content: flex-start;
            overflow-y: auto;
            flex: 1;
            padding-bottom: 80px; /* Make room for the fixed pagination */
        }

        .pagination-container {
            padding: 15px 20px;
            background-color: var(--secondary-color);
            display: flex;
            justify-content: center;
            align-items: center;
            border-top: 1px solid #ddd;
            position: fixed;
            bottom: 0;
            left: 0;
            width: 87.5%; /* Match the width of the left container */
            z-index: 100;
        }

        .experiment-box {
            width: 100px;
            height: 100px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 14px;
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
            font-size: 20px;
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

        /* Pagination styles */
        .pagination {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .page-link {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 36px;
            height: 36px;
            background-color: white;
            color: var(--primary-color);
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            border: 1px solid #ddd;
            transition: all 0.2s;
            padding: 0 10px;
        }

        .page-link:hover {
            background-color: #f1f1f1;
        }

        .page-link.active {
            background-color: var(--accent-color);
            color: white;
            border-color: var(--accent-color);
        }

        .page-link.disabled {
            color: #aaa;
            cursor: not-allowed;
        }

        .page-jump {
            display: flex;
            align-items: center;
            margin-left: 10px;
        }

        .page-jump input {
            width: 100px; /* Increased from 60px */
            height: 36px;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 0 10px;
            margin: 0 5px;
            text-align: center;
        }

        .page-jump button {
            height: 36px;
            background-color: var(--accent-color);
            color: white;
            border: none;
            border-radius: 5px;
            padding: 0 15px;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        .page-jump button:hover {
            background-color: #2980b9;
        }

        .page-info {
            color: #666;
            margin-right: 15px;
        }

        /* Server IP Settings */
        .server-settings {
            display: flex;
            align-items: center;
            margin-left: 20px;
            padding-left: 20px;
            border-left: 1px solid #ddd;
        }

        .server-settings input {
            width: 150px;
            height: 36px;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 0 10px;
            margin: 0 5px;
        }

        .server-settings button {
            height: 36px;
            background-color: var(--accent-color);
            color: white;
            border: none;
            border-radius: 5px;
            padding: 0 15px;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        .server-settings button:hover {
            background-color: #2980b9;
        }

        .server-ip-label {
            color: #666;
            font-weight: bold;
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
            
            .pagination-container {
                width: 75%;
            }
            
            .server-settings {
                margin-left: 10px;
                padding-left: 10px;
            }
            
            .server-settings input {
                width: 120px;
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

            .pagination {
                flex-wrap: wrap;
                justify-content: center;
            }

            .page-jump {
                width: 100%;
                justify-content: center;
                margin-top: 10px;
            }
            
            .pagination-container {
                position: static;
                width: 100%;
                flex-direction: column;
                gap: 10px;
            }
            
            .server-settings {
                margin-left: 0;
                padding-left: 0;
                border-left: none;
                border-top: 1px solid #ddd;
                padding-top: 10px;
                margin-top: 10px;
                width: 100%;
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="left">
            <div class="boxes-container" id="boxes-container">
                <!-- Boxes will be generated via JavaScript -->
            </div>
            
            <div class="pagination-container">
                <div class="page-info" id="page-info">
                    Loading experiment data...
                </div>
                <div class="pagination" id="pagination">
                    <!-- Pagination will be generated via JavaScript -->
                </div>
                <div class="server-settings">
                    <span class="server-ip-label">Server IP:</span>
                    <input type="text" id="serverIpInput" placeholder="Server IP">
                    <button onclick="updateServerIp()">Update</button>
                </div>
            </div>
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
        let currentPage = 1;
        let boxesPerPage = 100;
        let totalPages = 1;
        let numBoxes = 10; // Default value
        let serverIp = localStorage.getItem('serverIp') || 'evolab'; // Default to evolab if not set
        
        // Initialize the server IP input field
        document.getElementById('serverIpInput').value = serverIp;
        
        function updateServerIp() {
            const newIp = document.getElementById('serverIpInput').value.trim();
            if (newIp) {
                serverIp = newIp;
                localStorage.setItem('serverIp', serverIp);
                showNotification(`Server IP updated to ${serverIp}`);
                loadInitialData(); // Reload data with new IP
            } else {
                showErrorAnnouncement("Please enter a valid server IP");
            }
        }
        
        function showNotification(message) {
            const announcements = document.getElementById("announcements");
            const announcement = document.createElement("div");
            announcement.classList.add("announcement");
            announcement.style.borderLeft = "4px solid #2ecc71";
            
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
        
        function getUrlParam(name) {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get(name);
        }
        
        function loadInitialData() {
            // Get page from URL or default to 1
            currentPage = parseInt(getUrlParam('page')) || 1;
            
            // Fetch the number of boxes first
            fetch(`http://${serverIp}:3753/getNum`)
                .then(response => response.text())
                .then(data => {
                    numBoxes = parseInt(data);
                    if (isNaN(numBoxes)) numBoxes = 10; // Fallback to 10 if invalid
                    
                    totalPages = Math.ceil(numBoxes / boxesPerPage);
                    currentPage = Math.max(1, Math.min(totalPages, currentPage)); // Ensure valid page
                    
                    updatePagination();
                    generateBoxes();
                    fetchAll();
                })
                .catch(error => {
                    console.error("Error fetching box count:", error);
                    showErrorAnnouncement(`Failed to connect to server at ${serverIp}:3753`);
                    // Still generate UI with default values
                    updatePagination();
                    generateBoxes();
                });
        }
        
        function generateBoxes() {
            const container = document.getElementById('boxes-container');
            container.innerHTML = ''; // Clear existing boxes
            
            // Calculate start and end box indices
            const startBox = (currentPage - 1) * boxesPerPage + 1;
            const endBox = Math.min(startBox + boxesPerPage - 1, numBoxes);
            
            // Update page info
            document.getElementById('page-info').textContent = `Showing boxes ${startBox} to ${endBox} of ${numBoxes}`;
            
            // Generate boxes
            for (let i = startBox; i <= endBox; i++) {
                const box = document.createElement('div');
                box.className = 'experiment-box';
                box.id = `box-${i}`;
                box.onclick = () => redbox(i);
                
                const statusIcon = document.createElement('div');
                statusIcon.className = 'status-icon';
                statusIcon.innerHTML = '<i class="fas fa-hourglass-half"></i>';
                
                const boxContent = document.createElement('div');
                boxContent.className = 'box-content';
                boxContent.textContent = `${i} is Waiting`;
                
                box.appendChild(statusIcon);
                box.appendChild(boxContent);
                
                container.appendChild(box);
            }
        }
        
        function updatePagination() {
            const pagination = document.getElementById('pagination');
            pagination.innerHTML = ''; // Clear existing pagination
            
            if (numBoxes <= boxesPerPage) {
                return; // No pagination needed
            }
            
            // Previous button
            const prevDisabled = currentPage <= 1 ? 'disabled' : '';
            const prevPage = Math.max(1, currentPage - 1);
            const prevLink = document.createElement('a');
            prevLink.href = `?page=${prevPage}`;
            prevLink.className = `page-link ${prevDisabled}`;
            prevLink.innerHTML = '<i class="fas fa-chevron-left"></i>';
            if (!prevDisabled) {
                prevLink.onclick = (e) => {
                    e.preventDefault();
                    navigateToPage(prevPage);
                };
            }
            pagination.appendChild(prevLink);
            
            // Page numbers
            const startPageButton = Math.max(1, currentPage - 2);
            const endPageButton = Math.min(totalPages, startPageButton + 4);
            
            if (startPageButton > 1) {
                const firstPageLink = document.createElement('a');
                firstPageLink.href = '?page=1';
                firstPageLink.className = 'page-link';
                firstPageLink.textContent = '1';
                firstPageLink.onclick = (e) => {
                    e.preventDefault();
                    navigateToPage(1);
                };
                pagination.appendChild(firstPageLink);
                
                if (startPageButton > 2) {
                    const ellipsis = document.createElement('span');
                    ellipsis.className = 'page-link disabled';
                    ellipsis.textContent = '...';
                    pagination.appendChild(ellipsis);
                }
            }
            
            for (let p = startPageButton; p <= endPageButton; p++) {
                const activeClass = p == currentPage ? 'active' : '';
                const pageLink = document.createElement('a');
                pageLink.href = `?page=${p}`;
                pageLink.className = `page-link ${activeClass}`;
                pageLink.textContent = p;
                if (p != currentPage) {
                    pageLink.onclick = (e) => {
                        e.preventDefault();
                        navigateToPage(p);
                    };
                }
                pagination.appendChild(pageLink);
            }
            
            if (endPageButton < totalPages) {
                if (endPageButton < totalPages - 1) {
                    const ellipsis = document.createElement('span');
                    ellipsis.className = 'page-link disabled';
                    ellipsis.textContent = '...';
                    pagination.appendChild(ellipsis);
                }
                
                const lastPageLink = document.createElement('a');
                lastPageLink.href = `?page=${totalPages}`;
                lastPageLink.className = 'page-link';
                lastPageLink.textContent = totalPages;
                lastPageLink.onclick = (e) => {
                    e.preventDefault();
                    navigateToPage(totalPages);
                };
                pagination.appendChild(lastPageLink);
            }
            
            // Next button
            const nextDisabled = currentPage >= totalPages ? 'disabled' : '';
            const nextPage = Math.min(totalPages, currentPage + 1);
            const nextLink = document.createElement('a');
            nextLink.href = `?page=${nextPage}`;
            nextLink.className = `page-link ${nextDisabled}`;
            nextLink.innerHTML = '<i class="fas fa-chevron-right"></i>';
            if (!nextDisabled) {
                nextLink.onclick = (e) => {
                    e.preventDefault();
                    navigateToPage(nextPage);
                };
            }
            pagination.appendChild(nextLink);
            
            // Page jump form
            const pageJump = document.createElement('div');
            pageJump.className = 'page-jump';
            
            const jumpForm = document.createElement('form');
            jumpForm.id = 'jumpToPageForm';
            jumpForm.onsubmit = (e) => {
                e.preventDefault();
                return jumpToPage();
            };
            
            const pageInput = document.createElement('input');
            pageInput.type = 'number';
            pageInput.id = 'pageInput';
            pageInput.min = '1';
            pageInput.max = totalPages;
            pageInput.placeholder = 'Page';
            
            const goButton = document.createElement('button');
            goButton.type = 'submit';
            goButton.textContent = 'Go';
            
            jumpForm.appendChild(pageInput);
            jumpForm.appendChild(goButton);
            pageJump.appendChild(jumpForm);
            
            pagination.appendChild(pageJump);
        }
        
        function navigateToPage(page) {
            currentPage = page;
            // Update URL without reload
            window.history.pushState({}, '', `?page=${page}`);
            // Update UI
            generateBoxes();
            updatePagination();
            // Fetch new data
            fetchAll();
        }
        
        function fetchAll() {
            fetchLogs();
            fetchStates();
        }
        
        function fetchLogs() {
            const serverUrl = `http://${serverIp}:3753/logs`;
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
            const serverUrl = `http://${serverIp}:3753/status`;
            const headers = {
                'lastLog': lastState
            };

            fetch(serverUrl, {
                method: 'GET',
                headers: headers
            })
            .then(response => response.json())
            .then(data => {
                changeStates(data);
            })
            .catch(error => {
                console.error("Error fetching states:", error);
                showErrorAnnouncement("Failed to fetch states");
            });
        }
        
        function changeStates(states) {
            states.forEach(state => {
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
            const serverUrl = `http://${serverIp}:3753/info`;
            const headers = {
                'index': boxNumber
            };

            fetch(serverUrl, {
                method: 'GET',
                headers: headers
            })
            .then(response => response.json())
            .then(data => {
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
        
        function jumpToPage() {
            const pageInput = document.getElementById('pageInput');
            const page = parseInt(pageInput.value);
            
            if (page >= 1 && page <= totalPages) {
                navigateToPage(page);
            } else {
                showErrorAnnouncement(`Please enter a page number between 1 and ${totalPages}`);
            }
            
            return false; // Prevent form submission
        }
        
        // Handle browser back/forward buttons
        window.onpopstate = function() {
            const pageParam = getUrlParam('page');
            if (pageParam) {
                currentPage = parseInt(pageParam);
                generateBoxes();
                updatePagination();
                fetchAll();
            }
        };
        
        window.onload = function() {
            loadInitialData();
            setInterval(fetchAll, 2000);  // Poll every 2 seconds
        }
    </script>
</body>
</html>