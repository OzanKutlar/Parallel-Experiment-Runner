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
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }

        /* --- Clickable Stat Cards --- */
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
            transition: background-color 0.3s ease, transform 0.2s ease;
            cursor: pointer;
        }

        .stat-card:hover {
            background-color: var(--card-hover-bg);
            transform: translateY(-2px);
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
            transition: background-color 0.3s ease, transform 0.2s ease;
            cursor: pointer;
        }

        .progress-card:hover {
            background-color: var(--card-hover-bg);
            transform: translateY(-2px);
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
            max-height: 300px;
            overflow-y: auto;
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

        /* --- Tabs Logic --- */
        .modal-tabs {
            display: flex; gap: 10px; margin-bottom: 20px;
            border-bottom: 2px solid var(--bg-tertiary); padding-bottom: 10px;
        }
        .modal-tab {
            background: none; border: none; color: var(--text-secondary);
            font-size: 16px; cursor: pointer; padding: 5px 10px;
            border-bottom: 2px solid transparent; transition: all 0.2s;
            font-family: inherit;
        }
        .modal-tab.active { color: var(--accent-orange); border-bottom-color: var(--accent-orange); }
        .modal-tab:hover:not(.active) { color: var(--text-primary); }
        .tab-content { display: none; flex-direction: column; gap: 10px; max-height: 50vh; overflow-y: auto; }
        .tab-content.active { display: flex; }
        .modal.large .modal-content { max-width: 800px; width: 90%; }
        
        .waiting-card { display: flex; justify-content: space-between; align-items: center; padding: 12px; background-color: var(--bg-tertiary); border: 1px solid var(--border); border-left: 4px solid var(--text-secondary); border-radius: 6px; }
        .waiting-card .card-id { font-size: 16px; font-weight: bold; color: var(--text-primary); }
        .waiting-card .card-status { font-size: 10px; text-transform: uppercase; color: var(--text-secondary); letter-spacing: 1px; }

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

        .worker-group-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 10px;
            background-color: var(--bg-tertiary);
            border-left: 3px solid var(--accent-orange);
            border-radius: 4px;
            font-size: 13px;
            font-weight: bold;
            color: var(--accent-orange);
            cursor: pointer;
            user-select: none;
            margin-top: 4px;
        }
        
        .worker-group-header:hover { background-color: var(--card-hover-bg); }
        
        .worker-group-content {
            display: flex;
            flex-direction: column;
            gap: 4px;
            padding-left: 10px;
            margin-bottom: 6px;
        }
        .worker-group-content.collapsed { display: none; }

        .worker-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 10px;
            background-color: var(--bg-tertiary);
            border-radius: 4px;
            font-size: 12px;
        }
        
        /* Ungrouped items without indent */
        .worker-list > .worker-item { padding: 8px; margin-bottom: 4px; font-size: 13px; }

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
        
        .property-item { display: flex; padding: 10px; border-bottom: 1px solid var(--border); justify-content: space-between; }
        .property-key { color: var(--text-secondary); font-weight: 600; min-width: 150px; }
        .property-value { color: var(--text-primary); word-break: break-word; font-weight: bold; text-align: right; }
        
        /* Stats detail grid */
        .stats-detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }
        .stats-detail-card { background-color: var(--bg-tertiary); padding: 15px; border-radius: 8px; border-left: 4px solid var(--accent-orange); }
        .stats-detail-card .val { font-size: 24px; color: var(--accent-orange); font-weight: bold; margin-bottom: 5px; }
        .stats-detail-card .lbl { font-size: 11px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px; }

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

        @media (max-width: 900px) {
            .dashboard {
                grid-template-columns: 1fr; /* Stacks panels vertically */
                overflow-y: auto;
            }
            .left-panel, .right-panel {
                overflow: visible;
                height: auto;
            }
            .workers-section, .log-section {
                height: 400px;
            }
        }
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
                <div class="stat-card" style="cursor: default; transform: none;">
                    <div class="stat-value" id="totalExperiments">0</div>
                    <div class="stat-label">Total</div>
                </div>
                <div class="stat-card" onclick="openExperimentsModal('running')">
                    <div class="stat-value" id="runningCount">0</div>
                    <div class="stat-label">Running</div>
                </div>
                <div class="stat-card" onclick="openExperimentsModal('finished')">
                    <div class="stat-value" id="completedCount">0</div>
                    <div class="stat-label">Completed</div>
                </div>
                <div class="stat-card" onclick="openExperimentsModal('waiting')">
                    <div class="stat-value" id="waitingCount">0</div>
                    <div class="stat-label">Waiting</div>
                </div>
            </div>

            <div class="progress-card" id="progressCardEl" style="margin-top: auto; margin-bottom: 10px;" onclick="openDetailedStatsModal()">
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

            <!-- Inline Experiment Sections -->
            <div class="activity-section">
                <div class="activity-header">
                    <h3><i class="fas fa-cog"></i> Currently Running</h3>
                    <span style="color: var(--text-secondary); font-size: 12px;" id="inlineRunningCount">0 items</span>
                </div>
                <div class="running-grid" id="inlineRunningList">
                    <div class="empty-state"><i class="fas fa-inbox"></i><p>No experiments running</p></div>
                </div>
            </div>

            <div class="activity-section">
                <div class="activity-header">
                    <h3><i class="fas fa-play-circle"></i> Experiments Running / Taken</h3>
                    <span style="color: var(--text-secondary); font-size: 12px;" id="inlineTakenCount">0 items</span>
                </div>
                <div class="activity-list" id="inlineTakenList">
                    <div class="empty-state"><i class="fas fa-inbox"></i><p>No experiments taken yet</p></div>
                </div>
            </div>

            <div class="activity-section">
                <div class="activity-header">
                    <h3><i class="fas fa-check-circle"></i> Experiments Finished</h3>
                    <button class="btn-small" onclick="openExperimentsModal('finished')" style="font-size:11px;"><i class="fas fa-expand"></i> View all</button>
                </div>
                <div class="activity-list" id="inlineFinishedList">
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
                <button class="modal-close" onclick="closeModal('experimentModal')"><i class="fas fa-times"></i></button>
            </div>
            <div class="modal-body" id="modalBody"></div>
            <div class="modal-footer">
                <button class="btn btn-danger" id="resetBtn" onclick="resetExperiment()"><i class="fas fa-redo"></i> Reset</button>
                <button class="btn" onclick="closeModal('experimentModal')">Close</button>
            </div>
        </div>
    </div>

    <!-- Modal for all experiments lists -->
    <div id="experimentsListModal" class="modal large">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Experiments</h2>
                <button class="modal-close" onclick="closeModal('experimentsListModal')"><i class="fas fa-times"></i></button>
            </div>
            
            <div class="search-container" style="margin-bottom: 20px;">
                <i class="fas fa-search" style="color: var(--text-secondary)"></i>
                <input type="text" id="searchInput" class="search-input" placeholder="Search by Experiment ID or Worker Name..." onkeyup="handleSearch()">
            </div>
            
            <div class="modal-tabs">
                <button class="modal-tab active" onclick="switchExperimentsTab('running')" id="tab-btn-running">Running (<span id="currentlyRunningCount">0</span>)</button>
                <button class="modal-tab" onclick="switchExperimentsTab('finished')" id="tab-btn-finished">Finished (<span id="finishedCount">0</span>)</button>
                <button class="modal-tab" onclick="switchExperimentsTab('waiting')" id="tab-btn-waiting">Waiting (<span id="waitingCountInner">0</span>)</button>
            </div>
            
            <div class="tab-content active" id="tab-running">
                <div class="running-grid" id="currentlyRunningList"></div>
            </div>
            
            <div class="tab-content" id="tab-finished">
                <div class="activity-list" id="finishedList"></div>
            </div>
            
            <div class="tab-content" id="tab-waiting">
                <div class="activity-list" id="waitingList"></div>
            </div>
            
            <div class="modal-footer">
                <button class="btn" onclick="closeModal('experimentsListModal')">Close</button>
            </div>
        </div>
    </div>

    <!-- Detailed Stats Modal -->
    <div id="detailedStatsModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2><i class="fas fa-chart-bar"></i> Time Prediction & System Stats</h2>
                <button class="modal-close" onclick="closeModal('detailedStatsModal')"><i class="fas fa-times"></i></button>
            </div>
            
            <div class="stats-detail-grid">
                <div class="stats-detail-card">
                    <div class="val" id="ds-total-workers">0</div>
                    <div class="lbl">Active Workers</div>
                </div>
                <div class="stats-detail-card">
                    <div class="val" id="ds-avg-exp-time">0s</div>
                    <div class="lbl">Avg Time / Experiment</div>
                </div>
                <div class="stats-detail-card">
                    <div class="val" id="ds-total-time">0s</div>
                    <div class="lbl">Total System Time</div>
                </div>
                <div class="stats-detail-card">
                    <div class="val" id="ds-throughput">0s</div>
                    <div class="lbl">System Throughput / Exp</div>
                </div>
            </div>

            <div class="modal-body">
                <div class="property-item"><div class="property-key">Total Experiments:</div><div class="property-value" id="ds-total-exp">0</div></div>
                <div class="property-item"><div class="property-key">Finished Experiments:</div><div class="property-value" id="ds-finished-exp">0</div></div>
                <div class="property-item"><div class="property-key">Remaining Experiments:</div><div class="property-value" id="ds-remaining-exp">0</div></div>
                <div class="property-item"><div class="property-key">Data Samples (Sliding Window):</div><div class="property-value" id="ds-window-tasks">0</div></div>
                <div class="property-item"><div class="property-key">Estimated Time Remaining:</div><div class="property-value" id="ds-eta" style="color:var(--accent-orange)">0s</div></div>
            </div>

            <div class="modal-footer">
                <button class="btn" onclick="closeModal('detailedStatsModal')">Close</button>
            </div>
        </div>
    </div>

    <script>
        let serverIp = localStorage.getItem('serverIp') || 'localhost';
        let lastLog = -1;
        let lastState = -1;
        let latestStates = {}; 
        let totalExperiments = 0;
        let isConnected = false;
        let currentExperimentId = null;

        // Caching for flicker prevention
        let runningCache = "";
        let takenCache = "";
        let finishedCache = "";
        let inlineRunningCache = "";
        let inlineTakenCache = "";
        let inlineFinishedCache = "";
        
        // Search Filter
        let searchText = "";
        let searchTimeout;

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
            const logsPromise = fetch(`http://${serverIp}:3753/logs`, { headers: { 'lastLog': lastLog } })
                .then(r => r.json()).then(d => { d.forEach(l => { addLogEntry(l); lastLog = l.ID; }); });

            const statusPromise = fetch(`http://${serverIp}:3753/status`, { headers: { 'lastLog': lastState } })
                .then(r => r.json()).then(d => {
                    if (d.length > 0) {
                        d.forEach(s => {
                            lastState = s.ID;
                            latestStates[s.index] = s;
                        });
                        updateDashboard();
                    }
                });

            const statsPromise = fetch(`http://${serverIp}:3753/timeStats`)
                .then(r => r.json())
                .then(stats => updateTimeStats(stats));

            Promise.all([logsPromise, statusPromise, statsPromise])
                .catch(e => console.error(e))
                .finally(() => {
                    // Queue the next fetch ONLY after this one finishes or fails
                    setTimeout(fetchAll, 2000);
                });
        }

        function handleSearch() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchText = document.getElementById('searchInput').value.toLowerCase();
                updateDashboard(true);
            }, 300);
        }

        function updateDashboard(forceRender = false) {
            const taken = [];
            const finished = [];
            const running = [];

            Object.values(latestStates).forEach(state => {
                if (state.state === 'Finished') finished.push(state);
                else if (state.state === 'Running') {
                    running.push(state);
                    taken.push(state);
                }
            });

            // Update Counts (Global, ignored by search for stats)
            const waitingCount = totalExperiments - finished.length - running.length;
            document.getElementById('runningCount').textContent = running.length;
            document.getElementById('completedCount').textContent = finished.length;
            document.getElementById('waitingCount').textContent = waitingCount > 0 ? waitingCount : 0;
            
            document.getElementById('currentlyRunningCount').textContent = running.length;
            document.getElementById('finishedCount').textContent = finished.length;
            document.getElementById('waitingCountInner').textContent = waitingCount > 0 ? waitingCount : 0;

            // Active Workers Panel
            updateActiveWorkers(running);

            // Progress Bar
            const rawPercent = totalExperiments > 0 ? (finished.length / totalExperiments) * 100 : 0;
            const percent = Math.round(rawPercent);
            const circumference = 314.15; // 2 * pi * 50
            if (document.getElementById('progressBar')) {
                document.getElementById('progressBar').style.strokeDashoffset = circumference - (rawPercent / 100) * circumference;
                document.getElementById('progressPercent').textContent = percent + '%';
                document.getElementById('progressCompleted').textContent = `${finished.length} / ${totalExperiments}`;
                document.getElementById('progressRunning').textContent = running.length;
            }

            // Filter lists based on search
            const filterFn = (item) => {
                if (!searchText) return true;
                return String(item.index).includes(searchText) || (item.sentTo && item.sentTo.toLowerCase().includes(searchText));
            };

            updateRunningGrid(running.reverse().filter(filterFn), forceRender);
            updateActivityList('finishedList', finished.slice().reverse().filter(filterFn), 'finished', 'finishedCount', forceRender);
            
            // Only compute the expensive waiting list when the modal is actually open
            const listModalOpen = document.getElementById('experimentsListModal').classList.contains('active');
            if (listModalOpen) {
                updateWaitingList(waitingCount > 0 ? waitingCount : 0, running, finished, filterFn, forceRender);
            }

            // Also update inline sections
            updateInlineSections(running, taken, finished, filterFn, forceRender);
        }

        function updateInlineSections(running, taken, finished, filterFn, forceRender) {
            // Currently Running (grid cards) — with hash cache
            const inlineRunEl = document.getElementById('inlineRunningList');
            const inlineRunCount = document.getElementById('inlineRunningCount');
            if (inlineRunEl) {
                const filtered = running.slice().filter(filterFn);
                const hash = filtered.map(i => i.index).join(',');
                if (forceRender || hash !== inlineRunningCache) {
                    inlineRunningCache = hash;
                    inlineRunCount.textContent = filtered.length + ' items';
                    if (filtered.length === 0) {
                        inlineRunEl.innerHTML = `<div class="empty-state"><i class="fas fa-inbox"></i><p>No experiments running</p></div>`;
                    } else {
                        inlineRunEl.innerHTML = filtered.map(item => `
                            <div class="running-card" onclick="showExperimentDetails(${item.index})">
                                <div class="card-id">#${item.index} <i class="fas fa-cog fa-spin"></i></div>
                                <div class="card-worker"><i class="fas fa-server"></i> <strong>${item.sentTo}</strong></div>
                                <div class="card-status">Running</div>
                            </div>
                        `).join('');
                    }
                }
            }

            // Taken list — with hash cache
            const inlineTakenEl = document.getElementById('inlineTakenList');
            const inlineTakenCount = document.getElementById('inlineTakenCount');
            if (inlineTakenEl) {
                const filtered = taken.slice().reverse().filter(filterFn);
                const hash = filtered.map(i => i.index).join(',');
                if (forceRender || hash !== inlineTakenCache) {
                    inlineTakenCache = hash;
                    inlineTakenCount.textContent = filtered.length + ' items';
                    if (filtered.length === 0) {
                        inlineTakenEl.innerHTML = `<div class="empty-state"><i class="fas fa-inbox"></i><p>No experiments taken yet</p></div>`;
                    } else {
                        inlineTakenEl.innerHTML = filtered.map(item => `
                            <div class="activity-item taken" onclick="showExperimentDetails(${item.index})">
                                <div class="activity-content">
                                    <span class="activity-id">#${item.index}</span>
                                    <span>Running on <strong>${item.sentTo}</strong></span>
                                </div>
                                <div class="status-badge running"><i class="fas fa-cog fa-spin"></i> Running</div>
                            </div>
                        `).join('');
                    }
                }
            }

            // Finished list (inline, capped at 50) — with hash cache
            const inlineFinEl = document.getElementById('inlineFinishedList');
            if (inlineFinEl) {
                const filtered = finished.slice().reverse().filter(filterFn);
                const hash = finished.length + ':' + filtered.slice(0, 50).map(i => i.index).join(',');
                if (forceRender || hash !== inlineFinishedCache) {
                    inlineFinishedCache = hash;
                    if (filtered.length === 0) {
                        inlineFinEl.innerHTML = `<div class="empty-state"><i class="fas fa-inbox"></i><p>No experiments finished yet</p></div>`;
                    } else {
                        const display = filtered.slice(0, 50);
                        const moreText = filtered.length > 50 ? `<div style="text-align:center;padding:10px;color:var(--text-secondary);font-size:12px;">+ ${filtered.length - 50} more — <a href="#" onclick="openExperimentsModal('finished'); return false;" style="color:var(--accent-orange);">View all</a></div>` : '';
                        inlineFinEl.innerHTML = display.map(item => `
                            <div class="activity-item finished" onclick="showExperimentDetails(${item.index})">
                                <div class="activity-content">
                                    <span class="activity-id">#${item.index}</span>
                                    <span>Finished by <strong>${item.sentTo}</strong></span>
                                </div>
                                <div class="status-badge finished"><i class="fas fa-check"></i> Done</div>
                            </div>
                        `).join('') + moreText;
                    }
                }
            }
        }

        function switchExperimentsTab(tabName) {
            document.querySelectorAll('.modal-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById('tab-btn-' + tabName).classList.add('active');
            document.getElementById('tab-' + tabName).classList.add('active');
        }

        function openExperimentsModal(tabName) {
            switchExperimentsTab(tabName);
            document.getElementById('experimentsListModal').classList.add('active');
        }

        let globalTimeStatsCache = null;

        // --- TIME STATS UI LOGIC ---
        function updateTimeStats(stats) {
            globalTimeStatsCache = stats;
            const etaEl = document.getElementById('etaValue');
            const etaSeconds = stats.eta_seconds;

            if (etaSeconds === 0 && document.getElementById('progressPercent') && document.getElementById('progressPercent').textContent === '100%') {
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
            
            etaEl.innerText = formatDuration(etaSeconds) + ' remaining';
        }

        function formatDuration(seconds) {
            if (!seconds || seconds <= 0) return '0s';
            if (seconds < 60) return `${Math.round(seconds)}s`;
            if (seconds < 3600) return `${Math.round(seconds/60)}m ${Math.round(seconds%60)}s`;
            const h = Math.floor(seconds / 3600);
            const m = Math.round((seconds % 3600) / 60);
            return `${h}h ${m}m`;
        }

        function openDetailedStatsModal() {
            // Calculate active workers from runninglist
            const running = [];
            const finished = [];
            
            Object.values(latestStates).forEach(state => {
                if (state.state === 'Finished') finished.push(state);
                else if (state.state === 'Running') running.push(state);
            });

            const uniqueWorkers = new Set();
            running.forEach(item => uniqueWorkers.add(item.sentTo || "Unknown"));
            
            document.getElementById('ds-total-workers').textContent = uniqueWorkers.size;
            document.getElementById('ds-total-exp').textContent = totalExperiments;
            document.getElementById('ds-finished-exp').textContent = finished.length;
            document.getElementById('ds-remaining-exp').textContent = totalExperiments - finished.length;

            if (globalTimeStatsCache) {
                document.getElementById('ds-window-tasks').textContent = globalTimeStatsCache.window_tasks || 0;
                document.getElementById('ds-eta').textContent = formatDuration(globalTimeStatsCache.eta_seconds);
                
                // Reverse engineer avg time and total time
                // eta = remaining * throughput => throughput = eta / remaining
                const remaining = totalExperiments - finished.length;
                let throughput = 0;
                if (remaining > 0 && globalTimeStatsCache.eta_seconds > 0) {
                    throughput = globalTimeStatsCache.eta_seconds / remaining;
                }
                
                document.getElementById('ds-throughput').textContent = formatDuration(throughput);
                
                // throughput = avg_duration_per_task / active_workers => avg_duration = throughput * active_workers
                const avgDuration = throughput * (globalTimeStatsCache.active_workers || 1);
                document.getElementById('ds-avg-exp-time').textContent = formatDuration(avgDuration);
                
                // total time = finished * avgDuration
                document.getElementById('ds-total-time').textContent = formatDuration(finished.length * avgDuration);
            }

            document.getElementById('detailedStatsModal').classList.add('active');
        }

        // --- ACTIVE WORKERS LOGIC ---
        // Track which worker groups the user has collapsed
        const collapsedGroups = new Set();

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

            // Group workers
            const groups = {};
            const ungrouped = {};

            Object.entries(counts).forEach(([name, count]) => {
                // Flexible prefix matching: capture the lab group from names like
                // LAB1_PC01, LAB_1_PC01, LAB2PC03, ROOM_A_01, etc.
                // Strategy: split by underscore. If there are ≥2 parts AND the first
                // part (or first 2 parts) look like a "group prefix", group by it.
                const parts = name.split('_');
                let groupKey = null;
                if (parts.length >= 2) {
                    // Check if first part is purely letters, or letters+digits (like "LAB1")
                    // and second part (if it's a single digit) also belongs to the group
                    const part0 = parts[0]; // e.g. "LAB" or "LAB1"
                    const part1 = parts[1]; // e.g. "1" or "PC01"
                    
                    // If first part is letters only and second part is purely a number => group = "LAB_1"
                    if (/^[A-Za-z]+$/.test(part0) && /^\d+$/.test(part1)) {
                        groupKey = `${part0}_${part1}`; // e.g. LAB_1
                    } 
                    // If first part has letters+digits (like "LAB1") => group = "LAB1"
                    else if (/^[A-Za-z]+\d+$/.test(part0) && parts.length >= 2) {
                        groupKey = part0; // e.g. LAB1
                    }
                    // If first part is letters only and second is also letters+digits (like "ROOM_A") => group = "ROOM_A"
                    else if (/^[A-Za-z]+$/.test(part0) && /^[A-Za-z]/.test(part1) && parts.length >= 3) {
                        groupKey = `${part0}_${part1}`;
                    }
                }
                if (groupKey) {
                    if (!groups[groupKey]) groups[groupKey] = {};
                    groups[groupKey][name] = count;
                } else {
                    ungrouped[name] = count;
                }
            });

            let html = '';

            // Snapshot collapsed state from existing DOM before wiping it
            listEl.querySelectorAll('.worker-group-header').forEach(header => {
                const content = header.nextElementSibling;
                const label = header.getAttribute('data-group');
                if (label && content && content.classList.contains('collapsed')) {
                    collapsedGroups.add(label);
                } else if (label) {
                    collapsedGroups.delete(label);
                }
            });

            // Render groups
            Object.keys(groups).sort().forEach(groupPrefix => {
                let groupJobs = 0;
                let groupWorkers = groups[groupPrefix];
                const workerRows = Object.keys(groupWorkers).sort().map(w => {
                    groupJobs += groupWorkers[w];
                    return `
                        <div class="worker-item">
                            <div class="worker-name"><i class="fas fa-desktop"></i> ${w}</div>
                            <div class="worker-load">${groupWorkers[w]} jobs</div>
                        </div>
                    `;
                }).join('');

                html += `
                    <div class="worker-group-header" data-group="${groupPrefix}" onclick="toggleWorkerGroup(this)">
                        <span><i class="fas fa-network-wired"></i> ${groupPrefix} (${Object.keys(groupWorkers).length} PCs)</span>
                        <div style="display:flex; align-items:center; gap:8px;">
                           <span class="worker-load">${groupJobs} jobs</span>
                           <i class="fas fa-chevron-down" style="font-size:10px;"></i>
                        </div>
                    </div>
                    <div class="worker-group-content">
                        ${workerRows}
                    </div>
                `;
            });

            // Render ungrouped
            if (Object.keys(ungrouped).length > 0) {
                if (Object.keys(groups).length > 0) {
                    html += `<div style="font-size: 11px; color: var(--text-secondary); margin: 8px 0 4px 4px; text-transform: uppercase;">Other Workers</div>`;
                }
                html += Object.keys(ungrouped).sort().map(w => `
                    <div class="worker-item">
                        <div class="worker-name"><i class="fas fa-server"></i> ${w}</div>
                        <div class="worker-load">${ungrouped[w]} jobs</div>
                    </div>
                `).join('');
            }

            listEl.innerHTML = html;

            // Re-apply collapsed state
            listEl.querySelectorAll('.worker-group-header').forEach(header => {
                const label = header.getAttribute('data-group');
                if (label && collapsedGroups.has(label)) {
                    header.nextElementSibling.classList.add('collapsed');
                    const chevron = header.querySelector('.fa-chevron-down');
                    if (chevron) { chevron.classList.remove('fa-chevron-down'); chevron.classList.add('fa-chevron-right'); }
                }
            });
        }

        function toggleWorkerGroup(header) {
            const label = header.getAttribute('data-group');
            const content = header.nextElementSibling;
            const chevron = header.querySelector('i.fa-chevron-down, i.fa-chevron-right');
            const isNowCollapsed = content.classList.toggle('collapsed');
            if (chevron) {
                chevron.classList.toggle('fa-chevron-down', !isNowCollapsed);
                chevron.classList.toggle('fa-chevron-right', isNowCollapsed);
            }
            if (label) {
                if (isNowCollapsed) collapsedGroups.add(label);
                else collapsedGroups.delete(label);
            }
        }

        // Only update the modal lists when the modal is actually visible
        function updateRunningGrid(items, force) {
            const listEl = document.getElementById('currentlyRunningList');
            if (!listEl) return;
            // Skip re-render if modal is closed and data hasn't changed
            const isOpen = document.getElementById('experimentsListModal').classList.contains('active');
            if (!isOpen && !force) return;
            const dataHash = JSON.stringify(items.map(i => i.index));
            if (!force && runningCache === dataHash) return;
            runningCache = dataHash;

            document.getElementById('currentlyRunningCount').textContent = items.length;
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
            if (!listEl) return;
            // Skip if modal is closed and nothing forced
            const isOpen = document.getElementById('experimentsListModal').classList.contains('active');
            if (!isOpen && !force) return;
            const dataHash = JSON.stringify(items.map(i => i.index));
            
            if (!force) {
                if (type === 'finished' && finishedCache === dataHash) return;
            }
            if (type === 'finished') finishedCache = dataHash;

            document.getElementById('finishedCount').textContent = items.length;

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

        function updateWaitingList(waitingCount, runningList, finishedList, filterFn, force) {
            const listEl = document.getElementById('waitingList');
            document.getElementById('waitingCountInner').textContent = waitingCount;
            
            if (waitingCount === 0) {
                listEl.innerHTML = `<div class="empty-state"><i class="fas fa-inbox"></i><p>No experiments waiting</p></div>`;
                return;
            }

            // Waiting items are IDs that are neither finished nor running.
            // Since we just have totalExperiments, we can generate them.
            // This could be large, so we cap it to 100 for display to avoid lag.
            
            const activeIds = new Set();
            runningList.forEach(item => activeIds.add(item.index));
            finishedList.forEach(item => activeIds.add(item.index));
            
            let waitingItems = [];
            for (let i = 1; i <= totalExperiments; i++) {
                if (!activeIds.has(i)) {
                    waitingItems.push({ index: i, sentTo: 'Waiting' });
                }
            }
            
            waitingItems = waitingItems.filter(filterFn);
            
            if (waitingItems.length === 0) {
                listEl.innerHTML = `<div class="empty-state"><i class="fas fa-search"></i><p>No waiting experiments match search</p></div>`;
                return;
            }
            
            // Limit render to 100 max
            const displayItems = waitingItems.slice(0, 100);
            const moreText = waitingItems.length > 100 ? `<div style="text-align:center; padding: 10px; color: var(--text-secondary); font-size: 12px;">+ ${waitingItems.length - 100} more waiting...</div>` : '';

            listEl.innerHTML = displayItems.map(item => `
                <div class="waiting-card">
                    <div class="card-id">#${item.index}</div>
                    <div class="card-status">Waiting</div>
                </div>
            `).join('') + moreText;
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
        function closeModal(id) { document.getElementById(id || 'experimentModal').classList.remove('active'); }

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
            list.appendChild(entry);
            while (list.children.length > 100) list.removeChild(list.firstChild);
        }

        function clearLogs() { document.getElementById('logList').innerHTML = `<div class="empty-state"><i class="fas fa-scroll"></i><p>No logs</p></div>`; }
        function scrollToBottom() { const l = document.getElementById('logList'); l.scrollTop = l.scrollHeight; }

        window.onload = function() {
            initTheme();
            loadInitialData();
            // Switched to recursive setTimeout in fetchAll
            // setInterval(fetchAll, 2000); 
            setInterval(checkAutoTimeSwitch, 60000);

            // Escape key to close modals
            document.addEventListener('keydown', function(event) {
                if (event.key === "Escape") {
                    document.querySelectorAll('.modal.active').forEach(modal => {
                        modal.classList.remove('active');
                    });
                }
            });
        }
    </script>
</body>
</html>