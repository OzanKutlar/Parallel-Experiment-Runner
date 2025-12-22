<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Experiment Dashboard</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --bg-primary: #2b2b2b;
            --bg-secondary: #3c3f41;
            --bg-tertiary: #313335;
            --text-primary: #a9b7c6;
            --text-secondary: #808080;
            --accent-orange: #cc7832;
            --accent-orange-dark: #a85f28;
            --success: #629755;
            --warning: #bbb529;
            --error: #bc3f3c;
            --border: #555555;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Consolas', 'Monaco', monospace;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            overflow: hidden;
        }

        .dashboard {
            display: grid;
            grid-template-columns: 2fr 1fr;
            grid-template-rows: auto 1fr;
            gap: 15px;
            padding: 20px;
            height: 100vh;
        }

        .header {
            grid-column: 1 / -1;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: var(--bg-secondary);
            padding: 15px 25px;
            border-radius: 8px;
            border: 1px solid var(--border);
        }

        .header-title {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .header-title h1 {
            color: var(--accent-orange);
            font-size: 24px;
            font-weight: 600;
        }

        .server-config {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .server-config input {
            background-color: var(--bg-tertiary);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 8px 12px;
            border-radius: 4px;
            font-family: inherit;
            width: 150px;
        }

        .btn {
            background-color: var(--accent-orange);
            color: var(--bg-primary);
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
            transition: background-color 0.3s;
            font-family: inherit;
        }

        .btn:hover {
            background-color: var(--accent-orange-dark);
        }

        .btn-icon {
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .left-panel {
            display: flex;
            flex-direction: column;
            gap: 15px;
            overflow-y: auto;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }

        .stat-card {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background-color: var(--accent-orange);
        }

        .stat-value {
            font-size: 36px;
            font-weight: 700;
            color: var(--accent-orange);
            margin-bottom: 5px;
        }

        .stat-label {
            font-size: 14px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .progress-card {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 25px;
            display: flex;
            align-items: center;
            gap: 30px;
        }

        .progress-circle {
            position: relative;
            width: 150px;
            height: 150px;
        }

        .progress-svg {
            transform: rotate(-90deg);
        }

        .progress-bg {
            fill: none;
            stroke: var(--bg-tertiary);
            stroke-width: 10;
        }

        .progress-bar {
            fill: none;
            stroke: var(--accent-orange);
            stroke-width: 10;
            stroke-linecap: round;
            transition: stroke-dashoffset 0.5s ease;
        }

        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 28px;
            font-weight: 700;
            color: var(--accent-orange);
        }

        .progress-details {
            flex: 1;
        }

        .progress-details h3 {
            color: var(--accent-orange);
            margin-bottom: 15px;
            font-size: 18px;
        }

        .progress-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
        }

        .progress-item:last-child {
            border-bottom: none;
        }

        .activity-section {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            min-height: 300px;
        }

        .activity-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--accent-orange);
        }

        .activity-header h3 {
            color: var(--accent-orange);
            font-size: 16px;
        }

        .activity-list {
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .activity-item {
            background-color: var(--bg-tertiary);
            border-left: 3px solid var(--accent-orange);
            padding: 12px;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background-color 0.2s;
        }

        .activity-item:hover {
            background-color: #3a3d3f;
        }

        .activity-item.taken {
            border-left-color: var(--warning);
        }

        .activity-item.finished {
            border-left-color: var(--success);
        }

        .activity-content {
            flex: 1;
        }

        .activity-id {
            color: var(--accent-orange);
            font-weight: 600;
            margin-right: 8px;
        }

        .activity-time {
            font-size: 11px;
            color: var(--text-secondary);
            margin-top: 4px;
        }

        .right-panel {
            display: flex;
            flex-direction: column;
            gap: 15px;
            overflow-y: auto;
        }

        .log-section {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            height: 100%;
        }

        .log-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--accent-orange);
        }

        .log-header h3 {
            color: var(--accent-orange);
            font-size: 16px;
        }

        .log-controls {
            display: flex;
            gap: 8px;
        }

        .btn-small {
            background-color: transparent;
            color: var(--text-secondary);
            border: 1px solid var(--border);
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
        }

        .btn-small:hover {
            background-color: var(--accent-orange);
            color: var(--bg-primary);
            border-color: var(--accent-orange);
        }

        .log-list {
            flex: 1;
            overflow-y: auto;
            font-family: 'Consolas', monospace;
            font-size: 13px;
        }

        .log-entry {
            padding: 8px 10px;
            border-bottom: 1px solid var(--bg-tertiary);
            display: flex;
            gap: 10px;
            transition: background-color 0.2s;
        }

        .log-entry:hover {
            background-color: var(--bg-tertiary);
        }

        .log-timestamp {
            color: var(--text-secondary);
            flex-shrink: 0;
            width: 80px;
        }

        .log-message {
            color: var(--text-primary);
            word-break: break-word;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-badge.running {
            background-color: rgba(187, 181, 41, 0.2);
            color: var(--warning);
        }

        .status-badge.finished {
            background-color: rgba(98, 151, 85, 0.2);
            color: var(--success);
        }

        .status-badge.waiting {
            background-color: rgba(128, 128, 128, 0.2);
            color: var(--text-secondary);
        }

        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-tertiary);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent-orange);
        }

        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px;
            color: var(--text-secondary);
            text-align: center;
        }

        .empty-state i {
            font-size: 48px;
            margin-bottom: 15px;
            opacity: 0.5;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .activity-item, .log-entry {
            animation: fadeIn 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <div class="header-title">
                <i class="fas fa-flask" style="color: var(--accent-orange); font-size: 28px;"></i>
                <h1>Experiment Monitor</h1>
                <div class="status-badge" id="connectionStatus">
                    <i class="fas fa-circle"></i>
                    <span>Connecting...</span>
                </div>
            </div>
            <div class="server-config">
                <label style="color: var(--text-secondary);">Server IP:</label>
                <input type="text" id="serverIpInput" placeholder="localhost">
                <button class="btn btn-icon" onclick="updateServerIp()">
                    <i class="fas fa-save"></i> Update
                </button>
                <button class="btn btn-icon" onclick="fetchAll()">
                    <i class="fas fa-sync"></i> Refresh
                </button>
            </div>
        </div>

        <div class="left-panel">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="totalExperiments">0</div>
                    <div class="stat-label">Total Experiments</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="runningCount">0</div>
                    <div class="stat-label">Currently Running</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="completedCount">0</div>
                    <div class="stat-label">Completed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="waitingCount">0</div>
                    <div class="stat-label">Waiting</div>
                </div>
            </div>

            <div class="progress-card">
                <div class="progress-circle">
                    <svg class="progress-svg" width="150" height="150">
                        <circle class="progress-bg" cx="75" cy="75" r="65"></circle>
                        <circle class="progress-bar" id="progressBar" cx="75" cy="75" r="65" 
                                stroke-dasharray="408.41" stroke-dashoffset="408.41"></circle>
                    </svg>
                    <div class="progress-text" id="progressPercent">0%</div>
                </div>
                <div class="progress-details">
                    <h3>Completion Progress</h3>
                    <div class="progress-item">
                        <span>Completed:</span>
                        <span id="progressCompleted">0 / 0</span>
                    </div>
                    <div class="progress-item">
                        <span>In Progress:</span>
                        <span id="progressRunning">0</span>
                    </div>
                    <div class="progress-item">
                        <span>Remaining:</span>
                        <span id="progressRemaining">0</span>
                    </div>
                </div>
            </div>

            <div class="activity-section">
                <div class="activity-header">
                    <h3><i class="fas fa-play-circle"></i> Experiments Taken</h3>
                    <span style="color: var(--text-secondary); font-size: 12px;" id="takenCount">0 items</span>
                </div>
                <div class="activity-list" id="takenList">
                    <div class="empty-state">
                        <i class="fas fa-inbox"></i>
                        <p>No experiments taken yet</p>
                    </div>
                </div>
            </div>

            <div class="activity-section">
                <div class="activity-header">
                    <h3><i class="fas fa-check-circle"></i> Experiments Finished</h3>
                    <span style="color: var(--text-secondary); font-size: 12px;" id="finishedCount">0 items</span>
                </div>
                <div class="activity-list" id="finishedList">
                    <div class="empty-state">
                        <i class="fas fa-inbox"></i>
                        <p>No experiments finished yet</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="right-panel">
            <div class="log-section">
                <div class="log-header">
                    <h3><i class="fas fa-terminal"></i> Activity Log</h3>
                    <div class="log-controls">
                        <button class="btn-small" onclick="clearLogs()">
                            <i class="fas fa-trash"></i> Clear
                        </button>
                        <button class="btn-small" onclick="scrollToTop()">
                            <i class="fas fa-arrow-up"></i> Top
                        </button>
                        <button class="btn-small" onclick="scrollToBottom()">
                            <i class="fas fa-arrow-down"></i> Bottom
                        </button>
                    </div>
                </div>
                <div class="log-list" id="logList">
                    <div class="empty-state">
                        <i class="fas fa-scroll"></i>
                        <p>No log entries yet</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let serverIp = localStorage.getItem('serverIp') || 'localhost';
        let lastLog = -1;
        let lastState = -1;
        let allStates = [];
        let totalExperiments = 0;
        let isConnected = false;

        document.getElementById('serverIpInput').value = serverIp;

        function updateServerIp() {
            const newIp = document.getElementById('serverIpInput').value.trim();
            if (newIp) {
                serverIp = newIp;
                localStorage.setItem('serverIp', serverIp);
                showNotification('Server IP updated to ' + serverIp);
                loadInitialData();
            }
        }

        function showNotification(message) {
            // Simple notification in log
            addLogEntry({ Text: message, time: new Date().toLocaleTimeString() });
        }

        function updateConnectionStatus(connected) {
            isConnected = connected;
            const statusEl = document.getElementById('connectionStatus');
            if (connected) {
                statusEl.innerHTML = '<i class="fas fa-circle" style="color: var(--success);"></i><span>Connected</span>';
            } else {
                statusEl.innerHTML = '<i class="fas fa-circle" style="color: var(--error);"></i><span>Disconnected</span>';
            }
        }

        function loadInitialData() {
            fetch(`http://${serverIp}:3753/getNum`)
                .then(response => response.text())
                .then(data => {
                    totalExperiments = parseInt(data) || 0;
                    document.getElementById('totalExperiments').textContent = totalExperiments;
                    updateConnectionStatus(true);
                    fetchAll();
                })
                .catch(error => {
                    console.error("Error:", error);
                    updateConnectionStatus(false);
                });
        }

        function fetchAll() {
            fetchLogs();
            fetchStates();
        }

        function fetchLogs() {
            fetch(`http://${serverIp}:3753/logs`, {
                headers: { 'lastLog': lastLog }
            })
            .then(response => response.json())
            .then(data => {
                data.forEach(log => {
                    addLogEntry(log);
                    lastLog = log.ID;
                });
            })
            .catch(error => console.error("Error fetching logs:", error));
        }

        function fetchStates() {
            fetch(`http://${serverIp}:3753/status`, {
                headers: { 'lastLog': lastState }
            })
            .then(response => response.json())
            .then(data => {
                allStates = [...allStates, ...data];
                data.forEach(state => {
                    lastState = state.ID;
                });
                updateDashboard();
            })
            .catch(error => console.error("Error fetching states:", error));
        }

        function updateDashboard() {
            const taken = [];
            const finished = [];
            const running = [];
            const waiting = [];

            // Process all states
            const latestStates = {};
            allStates.forEach(state => {
                latestStates[state.index] = state;
            });

            Object.values(latestStates).forEach(state => {
                if (state.state === 'Finished') {
                    finished.push(state);
                } else if (state.state === 'Running') {
                    running.push(state);
                    taken.push(state);
                } else if (state.state === 'Reset') {
                    waiting.push(state);
                }
            });

            // Update counts
            document.getElementById('runningCount').textContent = running.length;
            document.getElementById('completedCount').textContent = finished.length;
            document.getElementById('waitingCount').textContent = totalExperiments - finished.length - running.length;

            // Update progress
            const percent = totalExperiments > 0 ? Math.round((finished.length / totalExperiments) * 100) : 0;
            const circumference = 408.41;
            const offset = circumference - (percent / 100) * circumference;
            document.getElementById('progressBar').style.strokeDashoffset = offset;
            document.getElementById('progressPercent').textContent = percent + '%';
            document.getElementById('progressCompleted').textContent = `${finished.length} / ${totalExperiments}`;
            document.getElementById('progressRunning').textContent = running.length;
            document.getElementById('progressRemaining').textContent = totalExperiments - finished.length - running.length;

            // Update taken list
            updateActivityList('takenList', taken.reverse(), 'taken', 'takenCount');
            
            // Update finished list
            updateActivityList('finishedList', finished.reverse(), 'finished', 'finishedCount');
        }

        function updateActivityList(listId, items, type, countId) {
            const listEl = document.getElementById(listId);
            const countEl = document.getElementById(countId);
            
            countEl.textContent = items.length + ' items';

            if (items.length === 0) {
                listEl.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-inbox"></i>
                        <p>No experiments ${type === 'taken' ? 'taken' : 'finished'} yet</p>
                    </div>
                `;
                return;
            }

            listEl.innerHTML = items.map(item => `
                <div class="activity-item ${type}">
                    <div class="activity-content">
                        <span class="activity-id">#${item.index}</span>
                        <span>${type === 'taken' ? 'Running on' : 'Finished by'} <strong>${item.sentTo}</strong></span>
                    </div>
                    <div class="status-badge ${type === 'taken' ? 'running' : 'finished'}">
                        <i class="fas ${type === 'taken' ? 'fa-cog fa-spin' : 'fa-check'}"></i>
                        ${type === 'taken' ? 'Running' : 'Done'}
                    </div>
                </div>
            `).join('');
        }

        function addLogEntry(log) {
            const logList = document.getElementById('logList');
            
            // Remove empty state if present
            const emptyState = logList.querySelector('.empty-state');
            if (emptyState) {
                emptyState.remove();
            }

            const entry = document.createElement('div');
            entry.className = 'log-entry';
            
            const time = log.time ? log.time.split(' ')[1] : new Date().toLocaleTimeString();
            
            entry.innerHTML = `
                <div class="log-timestamp">${time}</div>
                <div class="log-message">${log.Text}</div>
            `;

            logList.insertBefore(entry, logList.firstChild);

            // Keep only last 100 entries
            while (logList.children.length > 100) {
                logList.removeChild(logList.lastChild);
            }
        }

        function clearLogs() {
            const logList = document.getElementById('logList');
            logList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-scroll"></i>
                    <p>No log entries yet</p>
                </div>
            `;
        }

        function scrollToTop() {
            document.getElementById('logList').scrollTop = 0;
        }

        function scrollToBottom() {
            const logList = document.getElementById('logList');
            logList.scrollTop = logList.scrollHeight;
        }

        window.onload = function() {
            loadInitialData();
            setInterval(fetchAll, 2000);
        }
    </script>
</body>
</html>