<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Experiment Dashboard</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            /* Default Dark Mode Variables */
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
            --card-hover-bg: #3a3d3f;
        }

        /* Light Mode Variables (Royal Blue Theme) */
        body.light-mode {
            --bg-primary: #f4f6f8;
            --bg-secondary: #ffffff;
            --bg-tertiary: #e9ecef;
            --text-primary: #2c3e50;
            --text-secondary: #5f6368;
            --accent-orange: #0d6efd; 
            --accent-orange-dark: #0a58ca;
            --success: #198754;
            --warning: #ffc107;
            --error: #dc3545;
            --border: #dee2e6;
            --card-hover-bg: #f1f3f5;
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
            transition: background-color 0.3s ease, color 0.3s ease;
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
            transition: background-color 0.3s ease, border-color 0.3s ease;
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
            transition: background-color 0.3s ease, color 0.3s ease;
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
        
        body.light-mode .btn { color: #ffffff; }

        .btn:hover { background-color: var(--accent-orange-dark); }
        .btn-icon { display: inline-flex; align-items: center; gap: 8px; }

        .btn-theme {
            background-color: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border);
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-theme:hover {
            border-color: var(--accent-orange);
            color: var(--accent-orange);
        }

        .left-panel {
            display: flex;
            flex-direction: column;
            gap: 15px;
            overflow-y: auto;
            padding-right: 5px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
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
            transition: background-color 0.3s ease;
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background-color: var(--accent-orange);
        }

        .stat-value {
            font-size: 32px;
            font-weight: 700;
            color: var(--accent-orange);
            margin-bottom: 5px;
        }

        .stat-label {
            font-size: 13px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* --- Search Bar --- */
        .search-container {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border);
            padding: 10px 15px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .search-input {
            width: 100%;
            background: transparent;
            border: none;
            color: var(--text-primary);
            font-family: inherit;
            font-size: 14px;
            outline: none;
        }
        .search-input::placeholder { color: var(--text-secondary); }

        .progress-card {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 30px;
            transition: background-color 0.3s ease;
        }

        .progress-circle {
            position: relative;
            width: 120px;
            height: 120px;
        }

        .progress-svg { transform: rotate(-90deg); }
        .progress-bg { fill: none; stroke: var(--bg-tertiary); stroke-width: 10; }
        .progress-bar {
            fill: none;
            stroke: var(--accent-orange);
            stroke-width: 10;
            stroke-linecap: round;
            transition: stroke-dashoffset 0.5s ease;
        }

        .progress-text {
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            font-size: 24px;
            font-weight: 700;
            color: var(--accent-orange);
        }

        .progress-details { flex: 1; }
        .progress-details h3 { color: var(--accent-orange); margin-bottom: 10px; font-size: 16px; }

        .progress-item {
            display: flex; justify-content: space-between;
            margin-bottom: 8px; padding: 6px 0;
            border-bottom: 1px solid var(--border);
            font-size: 13px;
        }
        .progress-item:last-child { border-bottom: none; }

        /* ETA Style */
        .eta-badge {
            background-color: var(--bg-tertiary);
            color: var(--text-primary);
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 10px;
            border: 1px solid var(--border);
        }
        .eta-badge i { color: var(--accent-orange); }

        .activity-section {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            min-height: 200px;
            transition: background-color 0.3s ease;
        }

        .activity-header {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 15px; padding-bottom: 10px;
            border-bottom: 2px solid var(--accent-orange);
        }
        .activity-header h3 { color: var(--accent-orange); font-size: 16px; }

        .running-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
            padding: 4px;
        }

        .running-card {
            background-color: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-left: 4px solid var(--accent-orange);
            border-radius: 6px;
            padding: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
            animation: fadeInItem 0.3s ease;
            display: flex; flex-direction: column; gap: 6px;
        }
        .running-card:hover {
            background-color: var(--card-hover-bg);
            transform: translateY(-2px);
            border-color: var(--accent-orange);
        }
        .running-card .card-id { color: var(--accent-orange); font-size: 16px; font-weight: bold; display: flex; justify-content: space-between; }
        .running-card .card-worker { font-size: 12px; color: var(--text-primary); }
        .running-card .card-status { font-size: 10px; text-transform: uppercase; color: var(--warning); letter-spacing: 1px; }

        .activity-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; }

        .activity-item {
            background-color: var(--bg-tertiary);
            border-left: 3px solid var(--accent-orange);
            padding: 10px;
            border-radius: 4px;
            display: flex; justify-content: space-between; align-items: center;
            transition: all 0.2s;
            cursor: pointer;
            font-size: 13px;
        }
        .activity-item:hover { background-color: var(--card-hover-bg); transform: translateX(3px); }
        .activity-item.taken { border-left-color: var(--warning); }
        .activity-item.finished { border-left-color: var(--success); }
        .activity-content { flex: 1; }
        .activity-id { color: var(--accent-orange); font-weight: 600; margin-right: 8px; }

        .right-panel {
            display: flex;
            flex-direction: column;
            gap: 15px;
            overflow: hidden; /* Important for inner scroll */
        }

        /* --- Active Workers Section --- */
        .workers-section {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            height: 35%; /* Takes up top 35% of right panel */
            transition: background-color 0.3s ease;
        }

        .worker-list {
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .worker-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px;
            background-color: var(--bg-tertiary);
            border-radius: 4px;
            font-size: 13px;
        }
        .worker-name { font-weight: 600; color: var(--text-primary); display: flex; align-items: center; gap: 8px; }
        .worker-load { background-color: var(--accent-orange); color: var(--bg-primary); padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold; }
        body.light-mode .worker-load { color: white; }

        .log-section {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            height: 65%; /* Takes remaining space */
            transition: background-color 0.3s ease;
        }

        .log-header {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 10px; padding-bottom: 8px;
            border-bottom: 2px solid var(--accent-orange);
        }
        .log-header h3 { color: var(--accent-orange); font-size: 16px; }

        .log-controls { display: flex; gap: 6px; }
        .btn-small {
            background-color: transparent;
            color: var(--text-secondary);
            border: 1px solid var(--border);
            padding: 2px 6px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
            transition: all 0.2s;
        }
        .btn-small:hover { background-color: var(--accent-orange); color: var(--bg-primary); border-color: var(--accent-orange); }
        body.light-mode .btn-small:hover { color: white; }

        .log-list {
            flex: 1; overflow-y: auto;
            font-family: 'Consolas', monospace; font-size: 12px;
        }

        .log-entry {
            padding: 6px 8px;
            border-bottom: 1px solid var(--bg-tertiary);
            display: flex; gap: 8px;
        }
        .log-timestamp { color: var(--text-secondary); flex-shrink: 0; width: 70px; }
        .log-message { color: var(--text-primary); word-break: break-word; }

        .status-badge {
            display: inline-flex; align-items: center; gap: 5px;
            padding: 4px 10px; border-radius: 12px;
            font-size: 10px; font-weight: 600; text-transform: uppercase;
        }
        .status-badge.running { background-color: rgba(187, 181, 41, 0.2); color: var(--warning); }
        body.light-mode .status-badge.running { background-color: rgba(255, 193, 7, 0.2); color: #bfa006; }
        .status-badge.finished { background-color: rgba(98, 151, 85, 0.2); color: var(--success); }

        /* Modal */
        .modal {
            display: none; position: fixed; z-index: 1000;
            left: 0; top: 0; width: 100%; height: 100%;
            background-color: rgba(0, 0, 0, 0.7);
            animation: fadeIn 0.2s ease;
        }
        .modal.active { display: flex; justify-content: center; align-items: center; }
        .modal-content {
            background-color: var(--bg-secondary);
            border: 2px solid var(--accent-orange);
            border-radius: 8px;
            padding: 30px;
            max-width: 600px; max-height: 80vh;
            overflow-y: auto; animation: slideIn 0.3s ease;
        }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slideIn { from { transform: translateY(-50px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid var(--accent-orange); }
        .modal-header h2 { color: var(--accent-orange); font-size: 20px; }
        .modal-close { background: none; border: none; color: var(--text-secondary); font-size: 24px; cursor: pointer; }
        
        .property-item { display: flex; padding: 10px; border-bottom: 1px solid var(--border); }
        .property-key { color: var(--accent-orange); font-weight: 600; min-width: 150px; }
        .property-value { color: var(--text-primary); word-break: break-word; }
        .modal-footer { margin-top: 20px; padding-top: 15px; border-top: 1px solid var(--border); display: flex; justify-content: flex-end; gap: 10px; }
        .btn-danger { background-color: var(--error); color: white; }
        body.light-mode .btn-danger:hover { background-color: #bb2d3b; }

        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg-tertiary); }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--accent-orange); }

        .empty-state {
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            padding: 30px; color: var(--text-secondary); text-align: center;
        }
        .empty-state i { font-size: 36px; margin-bottom: 10px; opacity: 0.5; }

        @keyframes fadeInItem { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .activity-item, .log-entry { animation: fadeInItem 0.3s ease; }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <div class="header-title">
                <h1>Parallel Runner</h1>
                <div class="status-badge" id="connectionStatus">
                    <i class="fas fa-circle"></i> <span>Connecting...</span>
                </div>
            </div>
            <div class="server-config">
                <button class="btn-theme" onclick="manualToggleTheme()" title="Toggle Theme">
                    <i class="fas fa-moon" id="themeIcon"></i>
                </button>
                <input type="text" id="serverIpInput" placeholder="localhost">
                <button class="btn btn-icon" onclick="updateServerIp()">
                    <i class="fas fa-save"></i>
                </button>
                <button class="btn btn-icon" onclick="fetchAll()">
                    <i class="fas fa-sync"></i>
                </button>
            </div>
        </div>

        <div class="left-panel">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="totalExperiments">0</div>
                    <div class="stat-label">Total</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="runningCount">0</div>
                    <div class="stat-label">Running</div>
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

            <!-- SEARCH BAR -->
            <div class="search-container">
                <i class="fas fa-search" style="color: var(--text-secondary)"></i>
                <input type="text" id="searchInput" class="search-input" placeholder="Search by Experiment ID or Worker Name..." onkeyup="handleSearch()">
            </div>

            <div class="progress-card">
                <div class="progress-circle">
                    <svg class="progress-svg" width="120" height="120">
                        <circle class="progress-bg" cx="60" cy="60" r="50"></circle>
                        <circle class="progress-bar" id="progressBar" cx="60" cy="60" r="50" 
                                stroke-dasharray="314.15" stroke-dashoffset="314.15"></circle>
                    </svg>
                    <div class="progress-text" id="progressPercent">0%</div>
                </div>
                <div class="progress-details">
                    <h3>Progress & ETA</h3>
                    <div class="progress-item">
                        <span>Completed:</span>
                        <span id="progressCompleted">0 / 0</span>
                    </div>
                    <div class="progress-item">
                        <span>In Progress:</span>
                        <span id="progressRunning">0</span>
                    </div>
                    <!-- ETA BADGE -->
                    <div class="eta-badge" title="Estimated time based on current speed">
                        <i class="fas fa-clock"></i>
                        <span id="etaValue">Calculating...</span>
                    </div>
                </div>
            </div>

            <div class="activity-section">
                <div class="activity-header">
                    <h3><i class="fas fa-cog"></i> Currently Running</h3>
                    <span style="color: var(--text-secondary); font-size: 12px;" id="currentlyRunningCount">0 items</span>
                </div>
                <div class="running-grid" id="currentlyRunningList">
                    <div class="empty-state"><i class="fas fa-inbox"></i><p>No experiments running</p></div>
                </div>
            </div>

            <div class="activity-section">
                <div class="activity-header">
                    <h3><i class="fas fa-play-circle"></i> Experiments Taken</h3>
                    <span style="color: var(--text-secondary); font-size: 12px;" id="takenCount">0 items</span>
                </div>
                <div class="activity-list" id="takenList">
                    <div class="empty-state"><i class="fas fa-inbox"></i><p>No experiments taken yet</p></div>
                </div>
            </div>

            <div class="activity-section">
                <div class="activity-header">
                    <h3><i class="fas fa-check-circle"></i> Experiments Finished</h3>
                    <span style="color: var(--text-secondary); font-size: 12px;" id="finishedCount">0 items</span>
                </div>
                <div class="activity-list" id="finishedList">
                    <div class="empty-state"><i class="fas fa-inbox"></i><p>No experiments finished yet</p></div>
                </div>
            </div>
        </div>

        <div class="right-panel">
            <!-- ACTIVE WORKERS PANEL -->
            <div class="workers-section">
                <div class="log-header">
                    <h3><i class="fas fa-server"></i> Active Workers</h3>
                </div>
                <div class="worker-list" id="workerList">
                    <div class="empty-state" style="padding:10px;"><i class="fas fa-microchip" style="font-size:24px;"></i><p style="font-size:12px;">No active workers</p></div>
                </div>
            </div>

            <div class="log-section">
                <div class="log-header">
                    <h3><i class="fas fa-terminal"></i> Activity Log</h3>
                    <div class="log-controls">
                        <button class="btn-small" onclick="clearLogs()"><i class="fas fa-trash"></i></button>
                        <button class="btn-small" onclick="scrollToBottom()"><i class="fas fa-arrow-down"></i></button>
                    </div>
                </div>
                <div class="log-list" id="logList">
                    <div class="empty-state"><i class="fas fa-scroll"></i><p>No logs</p></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal for experiment details -->
    <div id="experimentModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">Experiment Details</h2>
                <button class="modal-close" onclick="closeModal()"><i class="fas fa-times"></i></button>
            </div>
            <div class="modal-body" id="modalBody"></div>
            <div class="modal-footer">
                <button class="btn btn-danger" onclick="resetExperiment()"><i class="fas fa-redo"></i> Reset</button>
                <button class="btn" onclick="closeModal()">Close</button>
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
        let currentExperimentId = null;

        // Caching for flicker prevention
        let runningCache = "";
        let takenCache = "";
        let finishedCache = "";
        
        // Search Filter
        let searchText = "";

        // ETA Variables
        let previousFinishedCount = 0;
        let completionTimestamps = [];

        // Theme Logic
        function initTheme() {
            const shouldBeLight = isScheduledLightMode();
            applyTheme(shouldBeLight);
        }

        function isScheduledLightMode() {
            const now = new Date();
            const mins = now.getHours() * 60 + now.getMinutes();
            return mins >= (8 * 60 + 30) && mins < (17 * 60);
        }

        function applyTheme(isLight) {
            const icon = document.getElementById('themeIcon');
            if (isLight) {
                document.body.classList.add('light-mode');
                icon.className = 'fas fa-sun';
                localStorage.setItem('theme', 'light');
            } else {
                document.body.classList.remove('light-mode');
                icon.className = 'fas fa-moon';
                localStorage.setItem('theme', 'dark');
            }
        }

        function manualToggleTheme() {
            const isLight = document.body.classList.toggle('light-mode');
            document.getElementById('themeIcon').className = isLight ? 'fas fa-sun' : 'fas fa-moon';
            localStorage.setItem('theme', isLight ? 'light' : 'dark');
        }

        function checkAutoTimeSwitch() {
            const now = new Date();
            if (now.getHours() === 8 && now.getMinutes() === 30 && !document.body.classList.contains('light-mode')) applyTheme(true);
            else if (now.getHours() === 17 && now.getMinutes() === 0 && document.body.classList.contains('light-mode')) applyTheme(false);
        }

        document.getElementById('serverIpInput').value = serverIp;

        function updateServerIp() {
            const newIp = document.getElementById('serverIpInput').value.trim();
            if (newIp) {
                serverIp = newIp;
                localStorage.setItem('serverIp', serverIp);
                loadInitialData();
            }
        }

        function loadInitialData() {
            fetch(`http://${serverIp}:3753/getNum`)
                .then(r => r.text())
                .then(data => {
                    totalExperiments = parseInt(data) || 0;
                    document.getElementById('totalExperiments').textContent = totalExperiments;
                    document.getElementById('connectionStatus').innerHTML = '<i class="fas fa-circle" style="color: var(--success);"></i><span>Connected</span>';
                    fetchAll();
                })
                .catch(() => document.getElementById('connectionStatus').innerHTML = '<i class="fas fa-circle" style="color: var(--error);"></i><span>Disconnected</span>');
        }

        function fetchAll() {
            fetch(`http://${serverIp}:3753/logs`, { headers: { 'lastLog': lastLog } })
                .then(r => r.json()).then(d => { d.forEach(l => { addLogEntry(l); lastLog = l.ID; }); })
                .catch(e => console.error(e));

            fetch(`http://${serverIp}:3753/status`, { headers: { 'lastLog': lastState } })
                .then(r => r.json()).then(d => {
                    if (d.length > 0) {
                        allStates = [...allStates, ...d];
                        d.forEach(s => lastState = s.ID);
                        updateDashboard();
                    }
                })
                .catch(e => console.error(e));

            // Fetch server-side calculated stats
            fetch(`http://${serverIp}:3753/timeStats`)
                .then(r => r.json())
                .then(stats => updateTimeStats(stats))
                .catch(e => console.error(e));
        }

        function handleSearch() {
            searchText = document.getElementById('searchInput').value.toLowerCase();
            // Force re-render with current state data
            updateDashboard(true);
        }

        function updateDashboard(forceRender = false) {
            const taken = [];
            const finished = [];
            const running = [];
            const latestStates = {};

            allStates.forEach(state => latestStates[state.index] = state);

            Object.values(latestStates).forEach(state => {
                if (state.state === 'Finished') finished.push(state);
                else if (state.state === 'Running') {
                    running.push(state);
                    taken.push(state);
                }
            });

            // Update Counts (Global, ignored by search for stats)
            document.getElementById('runningCount').textContent = running.length;
            document.getElementById('completedCount').textContent = finished.length;
            document.getElementById('waitingCount').textContent = totalExperiments - finished.length - running.length;


            // Active Workers Panel
            updateActiveWorkers(running);

            // Progress Bar
            const percent = totalExperiments > 0 ? Math.round((finished.length / totalExperiments) * 100) : 0;
            const circumference = 314.15; // 2 * pi * 50
            document.getElementById('progressBar').style.strokeDashoffset = circumference - (percent / 100) * circumference;
            document.getElementById('progressPercent').textContent = percent + '%';
            document.getElementById('progressCompleted').textContent = `${finished.length} / ${totalExperiments}`;
            document.getElementById('progressRunning').textContent = running.length;

            // Filter lists based on search
            const filterFn = (item) => {
                if (!searchText) return true;
                return String(item.index).includes(searchText) || (item.sentTo && item.sentTo.toLowerCase().includes(searchText));
            };

            updateRunningGrid(running.reverse().filter(filterFn), forceRender);
            updateActivityList('takenList', taken.reverse().filter(filterFn), 'taken', 'takenCount', forceRender);
            updateActivityList('finishedList', finished.reverse().filter(filterFn), 'finished', 'finishedCount', forceRender);
        }

        // --- TIME STATS UI LOGIC ---
        function updateTimeStats(stats) {
            const etaEl = document.getElementById('etaValue');
            const etaSeconds = stats.eta_seconds;

            if (etaSeconds === 0 && document.getElementById('progressPercent').textContent === '100%') {
                etaEl.innerText = "Done";
                return;
            }

            if (stats.active_workers === 0) {
                etaEl.innerText = "Paused (No Workers)";
                return;
            }

            if (etaSeconds <= 0) {
                etaEl.innerText = "Calculating...";
                return;
            }
            
            // Format ETA
            if (etaSeconds < 60) etaEl.innerText = `~${Math.round(etaSeconds)}s remaining`;
            else if (etaSeconds < 3600) etaEl.innerText = `~${Math.round(etaSeconds/60)}m remaining`;
            else {
                const h = Math.floor(etaSeconds / 3600);
                const m = Math.round((etaSeconds % 3600) / 60);
                etaEl.innerText = `~${h}h ${m}m remaining`;
            }
        }

        // --- ACTIVE WORKERS LOGIC ---
        function updateActiveWorkers(runningList) {
            const counts = {};
            runningList.forEach(item => {
                const w = item.sentTo || "Unknown";
                counts[w] = (counts[w] || 0) + 1;
            });

            const listEl = document.getElementById('workerList');
            if (Object.keys(counts).length === 0) {
                listEl.innerHTML = `<div class="empty-state" style="padding:10px;"><i class="fas fa-microchip" style="font-size:24px;"></i><p style="font-size:12px;">No active workers</p></div>`;
                return;
            }

            listEl.innerHTML = Object.entries(counts).map(([name, count]) => `
                <div class="worker-item">
                    <div class="worker-name"><i class="fas fa-server"></i> ${name}</div>
                    <div class="worker-load">${count} jobs</div>
                </div>
            `).join('');
        }

        function updateRunningGrid(items, force) {
            const listEl = document.getElementById('currentlyRunningList');
            const dataHash = JSON.stringify(items);
            if (!force && runningCache === dataHash) return;
            runningCache = dataHash;

            document.getElementById('currentlyRunningCount').textContent = items.length + ' items';
            if (items.length === 0) {
                listEl.innerHTML = `<div class="empty-state"><i class="fas fa-inbox"></i><p>No experiments running</p></div>`;
                return;
            }

            listEl.innerHTML = items.map(item => `
                <div class="running-card" onclick="showExperimentDetails(${item.index})">
                    <div class="card-id">#${item.index} <i class="fas fa-cog fa-spin"></i></div>
                    <div class="card-worker"><i class="fas fa-server"></i> <strong>${item.sentTo}</strong></div>
                    <div class="card-status">Running</div>
                </div>
            `).join('');
        }

        function updateActivityList(listId, items, type, countId, force) {
            const listEl = document.getElementById(listId);
            const dataHash = JSON.stringify(items);
            
            if (!force) {
                if (type === 'taken' && takenCache === dataHash) return;
                if (type === 'finished' && finishedCache === dataHash) return;
            }
            if (type === 'taken') takenCache = dataHash; else finishedCache = dataHash;

            document.getElementById(countId).textContent = items.length + ' items';

            if (items.length === 0) {
                listEl.innerHTML = `<div class="empty-state"><i class="fas fa-inbox"></i><p>No experiments ${type}</p></div>`;
                return;
            }

            listEl.innerHTML = items.map(item => `
                <div class="activity-item ${type}" onclick="showExperimentDetails(${item.index})">
                    <div class="activity-content">
                        <span class="activity-id">#${item.index}</span>
                        <span>${type === 'finished' ? 'Finished by' : 'Running on'} <strong>${item.sentTo}</strong></span>
                    </div>
                    <div class="status-badge ${type}">
                        <i class="fas ${type === 'finished' ? 'fa-check' : 'fa-cog fa-spin'}"></i> ${type === 'finished' ? 'Done' : 'Running'}
                    </div>
                </div>
            `).join('');
        }

        function showExperimentDetails(id) {
            currentExperimentId = id;
            fetch(`http://${serverIp}:3753/info`, { headers: { 'index': id } })
            .then(r => r.json())
            .then(data => {
                document.getElementById('modalTitle').textContent = `Experiment #${id} Details`;
                const mb = document.getElementById('modalBody');
                mb.innerHTML = '';
                for (const [key, value] of Object.entries(data)) {
                    mb.innerHTML += `<div class="property-item"><div class="property-key">${key}:</div><div class="property-value">${typeof value === 'object' ? JSON.stringify(value,null,2) : value}</div></div>`;
                }
                document.getElementById('experimentModal').classList.add('active');
            });
        }
        function closeModal() { document.getElementById('experimentModal').classList.remove('active'); }

        function resetExperiment() {
            if (!currentExperimentId || !confirm(`Reset experiment #${currentExperimentId}?`)) return;
            fetch(`http://${serverIp}:3753/reset`, { headers: { 'index': currentExperimentId } })
            .then(() => { closeModal(); setTimeout(fetchAll, 500); });
        }

        function addLogEntry(log) {
            const list = document.getElementById('logList');
            // Safe DOM creation to prevent XSS
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            
            const timeSpan = document.createElement('div');
            timeSpan.className = 'log-timestamp';
            timeSpan.textContent = log.time ? (log.time.includes(' ') ? log.time.split(' ')[1] : log.time) : new Date().toLocaleTimeString();
            
            const msgSpan = document.createElement('div');
            msgSpan.className = 'log-message';
            msgSpan.textContent = log.Text;

            entry.appendChild(timeSpan);
            entry.appendChild(msgSpan);
            
            if(list.querySelector('.empty-state')) list.innerHTML = '';
            list.insertBefore(entry, list.firstChild);
            while (list.children.length > 100) list.removeChild(list.lastChild);
        }

        function clearLogs() { document.getElementById('logList').innerHTML = `<div class="empty-state"><i class="fas fa-scroll"></i><p>No logs</p></div>`; }
        function scrollToBottom() { const l = document.getElementById('logList'); l.scrollTop = l.scrollHeight; }

        window.onload = function() {
            initTheme();
            loadInitialData();
            setInterval(fetchAll, 2000);
            setInterval(checkAutoTimeSwitch, 60000);
        }
    </script>
</body>
</html>