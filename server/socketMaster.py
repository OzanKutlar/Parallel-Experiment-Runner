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
        self.managers = {}  # {manager_address: {"name": name, "clients": [client_names], "socket": socket}}
        self.lock = threading.Lock()
        self.message_map = {}
        
        # Set up default message handlers
        self.defineMessage("client_connected", self.handle_client_connected)
        self.defineMessage("client_disconnected", self.handle_client_disconnected)

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
                        self.message_map[message['type']](message, address)
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

    def sendMessage(self, manager_address, message):
        """Send a message to a specific manager."""
        with self.lock:
            if manager_address in self.managers:
                manager_socket = self.managers[manager_address]["socket"]
                try:
                    manager_socket.send(json.dumps(message).encode('utf-8'))
                    print(f"Sent message to manager {self.managers[manager_address]['name']}: {message}")
                    return True
                except Exception as e:
                    print(f"Error sending message to manager {self.managers[manager_address]['name']}: {e}")
                    return False
            else:
                print(f"Manager {manager_address} not found.")
                return False

    def handle_client_connected(self, message, manager_address):
        """Handle notification of client connection from manager."""
        client_name = message.get('client_name')
        if client_name:
            with self.lock:
                if manager_address in self.managers:
                    self.managers[manager_address]["clients"].append(client_name)
                    print(f"Client {client_name} connected to manager {self.managers[manager_address]['name']}")
                    self.print_system_status()

    def handle_client_disconnected(self, message, manager_address):
        """Handle notification of client disconnection from manager."""
        client_name = message.get('client_name')
        if client_name:
            with self.lock:
                if manager_address in self.managers and client_name in self.managers[manager_address]["clients"]:
                    self.managers[manager_address]["clients"].remove(client_name)
                    print(f"Client {client_name} disconnected from manager {self.managers[manager_address]['name']}")
                    self.print_system_status()

    def close_manager(self, manager_address):
        """Send a message to a manager to close and shut down."""
        if self.get_manager_client_count(manager_address) > 0:
            # Tell manager to close all its clients first
            message = {
                'type': 'close_manager',
                'action': 'close_all_clients'
            }
            return self.sendMessage(manager_address, message)
        else:
            # Tell manager to shut down immediately
            message = {
                'type': 'close_manager',
                'action': 'shutdown'
            }
            return self.sendMessage(manager_address, message)

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
    
    # Getter methods
    def get_manager_count(self):
        """Get the number of connected managers."""
        with self.lock:
            return len(self.managers)
    
    def get_manager_names(self):
        """Get a list of names of all connected managers."""
        with self.lock:
            return [info["name"] for info in self.managers.values()]
    
    def get_manager_by_name(self, name):
        """Find a manager by its name and return its address."""
        with self.lock:
            for addr, info in self.managers.items():
                if info["name"] == name:
                    return addr
            return None
    
    def get_manager_client_count(self, manager_address):
        """Get the number of clients connected to a specific manager."""
        with self.lock:
            if manager_address in self.managers:
                return len(self.managers[manager_address]["clients"])
            return 0
    
    def get_total_client_count(self):
        """Get the total number of clients connected to all managers."""
        with self.lock:
            return sum(len(info["clients"]) for info in self.managers.values())
            
    def get_manager_clients(self, manager_address):
        """Get a list of clients connected to a specific manager."""
        with self.lock:
            if manager_address in self.managers:
                return self.managers[manager_address]["clients"].copy()
            return []

class CustomRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server, master_server):
        self.master_server = master_server
        super().__init__(request, client_address, server)

    def do_GET(self):
        """Handle GET requests to the server."""
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/getManagers':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            managers = [{"manager_id": address, "name": info["name"]} for address, info in self.master_server.managers.items()]
            self.wfile.write(json.dumps(managers).encode('utf-8'))
        elif parsed_path.path == '/getManagerCount':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"count": self.master_server.get_manager_count()}).encode('utf-8'))
        elif parsed_path.path == '/getTotalClientCount':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"count": self.master_server.get_total_client_count()}).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Invalid request. Use /getManagers to get manager list.")
        return

# Custom HTTP server that knows about the MasterServer
class MasterHTTPServer(HTTPServer):
    def __init__(self, server_address, master_server):
        self.master_server = master_server
        super().__init__(server_address, lambda request, client_address, server: 
                         CustomRequestHandler(request, client_address, server, master_server))

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Master Server for Distributed Computing')
    parser.add_argument('--host', default='0.0.0.0', help='Master server hostname')
    parser.add_argument('--port', type=int, default=5000, help='Master server port')
    parser.add_argument('--web-port', type=int, default=8080, help='Web interface port')
    
    args = parser.parse_args()
    
    master = MasterServer(host=args.host, port=args.port)
    
    # Start HTTP server in a separate thread
    http_server = MasterHTTPServer((args.host, args.web_port), master)
    http_thread = threading.Thread(target=http_server.serve_forever)
    http_thread.daemon = True
    http_thread.start()
    print(f"HTTP server started on {args.host}:{args.web_port}")
    
    try:
        master.start()
    except KeyboardInterrupt:
        print("Master server shutting down")
        http_server.shutdown()