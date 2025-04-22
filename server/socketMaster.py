import socket
import threading
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

class MasterServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.server_socket = None
        self.managers = {}  # {manager_address: {"name": name, "clients": [client_names]}}
        self.lock = threading.Lock()
        self.message_map = {}

    def start(self):
        """Start the master server and listen for manager connections."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"Master server started on {self.host}:{self.port}")
            while True:
                client_socket, address = self.server_socket.accept()
                manager_thread = threading.Thread(target=self.handle_manager,
                                                 args=(client_socket, address))
                manager_thread.daemon = True
                manager_thread.start()
        except Exception as e:
            print(f"Error in master server: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()

    def handle_manager(self, manager_socket, address):
        """Handle communication with a manager server."""
        try:
            # Receive manager registration
            data = manager_socket.recv(1024).decode('utf-8')
            manager_info = json.loads(data)
            manager_name = manager_info.get('name', f"unknown-{address[0]}:{address[1]}")
            with self.lock:
                self.managers[address] = {"name": manager_name, "clients": [], "socket": manager_socket}
                print(f"New manager connected: {manager_name} ({address[0]}:{address[1]})")
                self.print_system_status()
            # Continue listening for updates from this manager
            while True:
                data = manager_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                try:
                    message = json.loads(data)
                    if message['type'] in self.message_map:
                        self.message_map[message['type']](message)
                    else:
                        print(f"Received unknown message type: {message['type']}")
                except json.JSONDecodeError:
                    print(f"Received invalid JSON from manager {manager_name}")
        except Exception as e:
            print(f"Error handling manager {address}: {e}")
        finally:
            with self.lock:
                if address in self.managers:
                    print(f"Manager {self.managers[address]['name']} disconnected")
                    self.managers.pop(address)
                    self.print_system_status()
            manager_socket.close()

    def defineMessage(self, request, func):
        """Define a message handler for a specific type of request."""
        self.message_map[request] = func

    def sendMessage(self, manager_id, message):
        """Send a message to a specific manager."""
        manager_socket = self.managers.get(manager_id)
        if manager_socket:
            manager_socket.sendall(json.dumps(message).encode('utf-8'))
            print(f"Sent message to manager {manager_id}: {message}")
        else:
            print(f"Manager {manager_id} not found.")

    def print_system_status(self):
        """Print the current system status showing all managers and their clients."""
        print("\n=== SYSTEM STATUS ===")
        if not self.managers:
            print("No managers connected")
        else:
            for addr, info in self.managers.items():
                print(f"Manager: {info['name']} ({addr[0]}:{addr[1]})")
                if info['clients']:
                    print(f"  Connected clients: {', '.join(info['clients'])}")
                else:
                    print("  No clients connected")
        print("=====================\n")
    

class CustomRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, master_server):
        self.master_server = master_server
        BaseHTTPRequestHandler.__init__(self)

    def do_GET(self):
        """Handle GET requests to the server."""
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/getManagers':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            managers = [{"manager_id": address, "name": info["name"]} for address, info in self.master_server.managers.items()]
            self.wfile.write(json.dumps(managers).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Invalid request. Use /getManagers to get manager list.")
        return
