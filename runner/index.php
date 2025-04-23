<?php
// Configuration
$master_host = 'evolab';
$master_port = 8080; // Web interface port for master server

// Helper functions
function callMasterAPI($endpoint) {
    global $master_host, $master_port;
    $url = "http://evolab:8080{$endpoint}";
    $response = @file_get_contents($url);
    if ($response === false) {
        return null;
    }
    
    return json_decode($response, true);
}

function sendCommand($endpoint, $data = []) {
    global $master_host, $master_port;
    $url = "http://{$master_host}:{$master_port}{$endpoint}";
    
    $options = [
        'http' => [
            'header'  => "Content-type: application/json\r\n",
            'method'  => 'POST',
            'content' => json_encode($data)
        ]
    ];
    
    $context  = stream_context_create($options);
    $response = @file_get_contents($url, false, $context);
    
    if ($response === false) {
        return null;
    }
    
    return json_decode($response, true);
}

// Handle actions
$message = '';
$messageType = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (isset($_POST['action'])) {
        switch ($_POST['action']) {
            case 'shutdownManager':
                if (isset($_POST['managerId'])) {
                    $managerId = json_decode($_POST['managerId'], true);
                    $result = sendCommand('/closeManager', ['manager_id' => $managerId]);
                    if ($result && isset($result['success']) && $result['success']) {
                        $message = "Manager shutdown command sent successfully.";
                        $messageType = "success";
                    } else {
                        $message = "Failed to send manager shutdown command.";
                        $messageType = "danger";
                    }
                }
                break;
                
            case 'shutdownClient':
                if (isset($_POST['managerId']) && isset($_POST['clientName'])) {
                    $managerId = json_decode($_POST['managerId'], true);
                    $clientName = $_POST['clientName'];
                    $result = sendCommand('/closeClient', [
                        'manager_id' => $managerId,
                        'client_name' => $clientName
                    ]);
                    if ($result && isset($result['success']) && $result['success']) {
                        $message = "Client shutdown command sent successfully.";
                        $messageType = "success";
                    } else {
                        $message = "Failed to send client shutdown command.";
                        $messageType = "danger";
                    }
                }
                break;
        }
    }
}

// Fetch data
$managers = callMasterAPI('/getManagers') ?: [];
$managerDetails = [];

foreach ($managers as $manager) {
    if (isset($manager['manager_id'])) {
        $managerInfo = callMasterAPI('/getManagerDetails?id=' . urlencode(json_encode($manager['manager_id'])));
        if ($managerInfo) {
            $managerDetails[$manager['name']] = $managerInfo;
        }
    }
}

$totalClients = callMasterAPI('/getTotalClientCount');
$totalClients = $totalClients ? $totalClients['count'] : 0;
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Distributed System Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            padding-top: 20px;
            background-color: #f5f5f5;
        }
        .card {
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: all 0.3s;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.1);
        }
        .card-selected {
            border: 3px solid #0d6efd;
        }
        .client-item, .manager-item {
            cursor: pointer;
            padding: 10px 15px;
            border-radius: 4px;
            transition: background-color 0.2s;
        }
        .client-item:hover, .manager-item:hover {
            background-color: rgba(13, 110, 253, 0.1);
        }
        .client-selected, .manager-selected {
            background-color: rgba(13, 110, 253, 0.2);
            font-weight: bold;
        }
        .dashboard-header {
            background-color: #343a40;
            color: white;
            padding: 15px 0;
            margin-bottom: 30px;
            border-radius: 5px;
        }
        .status-dot {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-active {
            background-color: #28a745;
        }
        .status-warning {
            background-color: #ffc107;
        }
        .status-danger {
            background-color: #dc3545;
        }
        #refreshButton {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
        }
        .action-buttons {
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="row dashboard-header text-center">
            <div class="col">
                <h1>Distributed System Dashboard</h1>
                <p class="lead">Monitor and control your distributed computing network</p>
            </div>
        </div>
        
        <?php if (!empty($message)): ?>
        <div class="alert alert-<?php echo $messageType; ?> alert-dismissible fade show" role="alert">
            <?php echo $message; ?>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
        <?php endif; ?>
        
        <!-- Status Overview -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5 class="card-title mb-0">System Status</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-6">
                                <h6>Managers</h6>
                                <h2><?php echo count($managers); ?></h2>
                            </div>
                            <div class="col-6">
                                <h6>Clients</h6>
                                <h2><?php echo $totalClients; ?></h2>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-success text-white">
                        <h5 class="card-title mb-0">Actions</h5>
                    </div>
                    <div class="card-body action-buttons">
                        <button id="shutdownManagerBtn" class="btn btn-warning me-2" disabled>
                            Shutdown Selected Manager
                        </button>
                        <button id="shutdownClientBtn" class="btn btn-danger" disabled>
                            Shutdown Selected Client
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Main Content -->
        <div class="row">
            <!-- Managers List -->
            <div class="col-md-5">
                <div class="card">
                    <div class="card-header bg-dark text-white">
                        <h5 class="card-title mb-0">Managers</h5>
                    </div>
                    <div class="card-body p-0">
                        <ul class="list-group list-group-flush" id="managersList">
                            <?php if (empty($managers)): ?>
                                <li class="list-group-item text-center text-muted">No managers connected</li>
                            <?php else: ?>
                                <?php foreach ($managers as $manager): ?>
                                    <li class="list-group-item manager-item" 
                                        data-manager-id='<?php echo htmlspecialchars(json_encode($manager['manager_id'])); ?>'
                                        data-manager-name="<?php echo htmlspecialchars($manager['name']); ?>">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <div>
                                                <span class="status-dot status-active"></span>
                                                <strong><?php echo htmlspecialchars($manager['name']); ?></strong>
                                            </div>
                                            <span class="badge bg-primary rounded-pill">
                                                <?php 
                                                    $clientCount = isset($managerDetails[$manager['name']]['clients']) ? 
                                                        count($managerDetails[$manager['name']]['clients']) : 0;
                                                    echo $clientCount . ' client' . ($clientCount !== 1 ? 's' : '');
                                                ?>
                                            </span>
                                        </div>
                                    </li>
                                <?php endforeach; ?>
                            <?php endif; ?>
                        </ul>
                    </div>
                </div>
            </div>
            
            <!-- Clients List -->
            <div class="col-md-7">
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <h5 class="card-title mb-0">Connected Clients</h5>
                    </div>
                    <div class="card-body p-0">
                        <div id="clientsPlaceholder" class="text-center p-4 text-muted">
                            Select a manager to view its clients
                        </div>
                        <div id="clientsContainer" class="d-none">
                            <div class="p-3 bg-light border-bottom">
                                <h6 class="mb-0">Clients for: <span id="selectedManagerName"></span></h6>
                            </div>
                            <ul class="list-group list-group-flush" id="clientsList">
                                <!-- Client items will be loaded here -->
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <button id="refreshButton" class="btn btn-primary rounded-circle p-3">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-arrow-clockwise" viewBox="0 0 16 16">
            <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z"/>
            <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z"/>
        </svg>
    </button>
    
    <!-- Form for submitting actions -->
    <form id="actionForm" method="post" style="display: none;">
        <input type="hidden" name="action" id="actionType">
        <input type="hidden" name="managerId" id="actionManagerId">
        <input type="hidden" name="clientName" id="actionClientName">
    </form>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            let selectedManager = null;
            let selectedClient = null;
            const managersList = document.getElementById('managersList');
            const clientsList = document.getElementById('clientsList');
            const clientsContainer = document.getElementById('clientsContainer');
            const clientsPlaceholder = document.getElementById('clientsPlaceholder');
            const selectedManagerName = document.getElementById('selectedManagerName');
            const shutdownManagerBtn = document.getElementById('shutdownManagerBtn');
            const shutdownClientBtn = document.getElementById('shutdownClientBtn');
            const refreshButton = document.getElementById('refreshButton');
            const actionForm = document.getElementById('actionForm');
            const actionType = document.getElementById('actionType');
            const actionManagerId = document.getElementById('actionManagerId');
            const actionClientName = document.getElementById('actionClientName');
            
            // Handle manager selection
            if (managersList) {
                managersList.addEventListener('click', function(e) {
                    const managerItem = e.target.closest('.manager-item');
                    if (!managerItem) return;
                    
                    // Clear previous selection
                    document.querySelectorAll('.manager-selected').forEach(item => {
                        item.classList.remove('manager-selected');
                    });
                    
                    // Set new selection
                    managerItem.classList.add('manager-selected');
                    selectedManager = {
                        id: JSON.parse(managerItem.dataset.managerId),
                        name: managerItem.dataset.managerName
                    };
                    
                    // Update clients list
                    loadClientsForManager(selectedManager.name);
                    
                    // Enable manager shutdown button
                    shutdownManagerBtn.disabled = false;
                    
                    // Clear client selection
                    selectedClient = null;
                    shutdownClientBtn.disabled = true;
                });
            }
            
            // Handle client selection
            function setupClientListeners() {
                document.querySelectorAll('.client-item').forEach(item => {
                    item.addEventListener('click', function() {
                        // Clear previous selection
                        document.querySelectorAll('.client-selected').forEach(i => {
                            i.classList.remove('client-selected');
                        });
                        
                        // Set new selection
                        this.classList.add('client-selected');
                        selectedClient = this.dataset.clientName;
                        
                        // Enable client shutdown button
                        shutdownClientBtn.disabled = false;
                    });
                });
            }
            
            // Load clients for selected manager
            function loadClientsForManager(managerName) {
                // Show clients container
                clientsContainer.classList.remove('d-none');
                clientsPlaceholder.classList.add('d-none');
                selectedManagerName.textContent = managerName;
                
                // Clear existing clients
                clientsList.innerHTML = '';
                
                // Load clients data
                const clients = <?php echo json_encode($managerDetails); ?>[managerName]?.clients || [];
                
                if (clients.length === 0) {
                    clientsList.innerHTML = '<li class="list-group-item text-center text-muted">No clients connected to this manager</li>';
                } else {
                    clients.forEach(client => {
                        const li = document.createElement('li');
                        li.className = 'list-group-item client-item';
                        li.dataset.clientName = client;
                        
                        li.innerHTML = `
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <span class="status-dot status-active"></span>
                                    ${client}
                                </div>
                                <span class="badge bg-info rounded-pill">Connected</span>
                            </div>
                        `;
                        
                        clientsList.appendChild(li);
                    });
                    
                    // Setup event listeners for clients
                    setupClientListeners();
                }
            }
            
            // Handle shutdown manager button
            shutdownManagerBtn.addEventListener('click', function() {
                if (!selectedManager) return;
                
                if (confirm(`Are you sure you want to shutdown manager "${selectedManager.name}"?\nThis will also disconnect all clients connected to this manager.`)) {
                    actionType.value = 'shutdownManager';
                    actionManagerId.value = JSON.stringify(selectedManager.id);
                    actionForm.submit();
                }
            });
            
            // Handle shutdown client button
            shutdownClientBtn.addEventListener('click', function() {
                if (!selectedManager || !selectedClient) return;
                
                if (confirm(`Are you sure you want to shutdown client "${selectedClient}"?`)) {
                    actionType.value = 'shutdownClient';
                    actionManagerId.value = JSON.stringify(selectedManager.id);
                    actionClientName.value = selectedClient;
                    actionForm.submit();
                }
            });
            
            // Handle refresh button
            refreshButton.addEventListener('click', function() {
                location.reload();
            });
            
            // Auto-refresh every 15 seconds
            setInterval(() => {
                location.reload();
            }, 15000);
        });
    </script>
</body>
</html>