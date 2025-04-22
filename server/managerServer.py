import socket
import threading
import json
import time
import platform

class ManagerServer:
    def __init__(self, master_host='localhost', master_port=5000, 
                 host='0.0.0.0', port=5001):
        self.master_host = master_host
        self.master_port = master_port
        self.host = host
        self.port = port
        self.server_socket = None
        self.master_socket = None
        self.manager_name = platform.node()  # Get computer name
        self.clients = {}  # {client_address: client_name}
        self.client_sockets = {}  # {client_name: client_socket}
        self.lock = threading.Lock()
        
    def connect_to_master(self):
        """Connect to the master server and register as a manager."""
        try:
            self.master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.master_socket.connect((self.master_host, self.master_port))
            
            # Register with master
            registration = {
                'type': 'registration',
                'name': self.manager_name
            }
            self.master_socket.send(json.dumps(registration).encode('utf-8'))
            print(f"Connected to master server at {self.master_host}:{self.master_port}")
            
            # Start a thread to handle communication with master
            master_thread = threading.Thread(target=self.handle_master_communication)
            master_thread.daemon = True
            master_thread.start()
            
            return True
        except Exception as e:
            print(f"Failed to connect to master server: {e}")
            return False
            
    def handle_master_communication(self):
        """Handle communication with the master server."""
        try:
            while True:
                data = self.master_socket.recv(1024).decode('utf-8')
                if not data:
                    print("Connection to master server lost")
                    break
                
                # Parse and handle commands from master
                try:
                    message = json.loads(data)
                    print(f"Received from master: {message}")
                    
                    # Handle the close_client command
                    if message.get('type') == 'close_client':
                        client_name = message.get('client_name')
                        if client_name:
                            self.close_client(client_name)
                    
                    # Handle the close_manager command
                    elif message.get('type') == 'close_manager':
                        action = message.get('action')
                        if action == 'close_all_clients':
                            self.close_all_clients()
                        elif action == 'shutdown':
                            print("Received shutdown command from master")
                            # Send acknowledgement before shutting down
                            ack = {
                                'type': 'shutdown_ack',
                                'status': 'shutting_down'
                            }
                            self.master_socket.send(json.dumps(ack).encode('utf-8'))
                            # Gracefully shut down the server
                            threading.Thread(target=self.shutdown).start()
                
                except json.JSONDecodeError:
                    print(f"Received invalid JSON from master")
                
        except Exception as e:
            print(f"Error in master communication: {e}")
        finally:
            self.master_socket.close()
    
    def close_client(self, client_name):
        """Close the connection to a specific client."""
        with self.lock:
            if client_name in self.client_sockets:
                try:
                    # Send close command to client
                    close_message = {
                        'type': 'close_command',
                        'reason': 'Closed by master server'
                    }
                    self.client_sockets[client_name].send(json.dumps(close_message).encode('utf-8'))
                    print(f"Sent close command to client {client_name}")
                    
                    # We don't close the socket here - the client should disconnect gracefully
                    # The socket will be removed when the client disconnects in handle_client
                    
                    return True
                except Exception as e:
                    print(f"Error closing client {client_name}: {e}")
                    # If we can't send the message, force close the socket
                    try:
                        self.client_sockets[client_name].close()
                    except:
                        pass
                    # Remove from our tracking
                    self.client_sockets.pop(client_name, None)
                    # Find and remove from clients dict
                    for addr, name in list(self.clients.items()):
                        if name == client_name:
                            self.clients.pop(addr)
                            break
                    
                    # Notify master about client disconnection
                    self.notify_client_connection(client_name, connected=False)
            else:
                print(f"Client {client_name} not found")
                return False
    
    def close_all_clients(self):
        """Close all client connections."""
        with self.lock:
            client_names = list(self.client_sockets.keys())
        
        for client_name in client_names:
            self.close_client(client_name)
    
    def shutdown(self):
        """Shut down the manager server."""
        # First close all clients
        self.close_all_clients()
        time.sleep(1)  # Give clients time to disconnect
        
        # Then close the server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("Manager server shutting down")
        import os, signal
        os._exit(0)  # Force exit the process
    
    def notify_client_connection(self, client_name, connected=True):
        """Notify the master server about a client connection/disconnection."""
        if self.master_socket:
            message = {
                'type': 'client_connected' if connected else 'client_disconnected',
                'client_name': client_name
            }
            try:
                self.master_socket.send(json.dumps(message).encode('utf-8'))
            except Exception as e:
                print(f"Failed to notify master about client: {e}")
    
    def start(self):
        """Start the manager server and listen for client connections."""
        # First connect to the master server
        if not self.connect_to_master():
            print("Cannot start without connection to master server")
            return
        
        # Start listening for client connections
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            print(f"Manager server '{self.manager_name}' started on {self.host}:{self.port}")
            
            while True:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, 
                                               args=(client_socket, address))
                client_thread.daemon = True
                client_thread.start()
                
        except Exception as e:
            print(f"Error in manager server: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    def handle_client(self, client_socket, address):
        """Handle communication with a client."""
        client_name = None
        try:
            # Receive client registration
            data = client_socket.recv(1024).decode('utf-8')
            client_info = json.loads(data)
            client_name = client_info.get('name', f"unknown-{address[0]}:{address[1]}")
            
            with self.lock:
                self.clients[address] = client_name
                self.client_sockets[client_name] = client_socket
                print(f"New client connected: {client_name} ({address[0]}:{address[1]})")
            
            # Notify master about new client
            self.notify_client_connection(client_name, connected=True)
            
            # Echo back acknowledgment to client
            response = {
                'type': 'registration_ack',
                'manager_name': self.manager_name,
                'status': 'connected'
            }
            client_socket.send(json.dumps(response).encode('utf-8'))
            
            # Continue listening for client requests
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                    
                try:
                    message = json.loads(data)
                    # Handle client messages/tasks here
                    print(f"Received from client {client_name}: {message}")
                    
                    # Echo back a response
                    response = {
                        'type': 'echo',
                        'original_message': message,
                        'timestamp': time.time()
                    }
                    client_socket.send(json.dumps(response).encode('utf-8'))
                    
                except json.JSONDecodeError:
                    print(f"Received invalid JSON from client {client_name}")
        
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            with self.lock:
                if address in self.clients:
                    client_name = self.clients[address]
                    print(f"Client {client_name} disconnected")
                    self.clients.pop(address)
                    if client_name in self.client_sockets:
                        self.client_sockets.pop(client_name)
                    
            # Notify master about client disconnection
            if client_name:
                self.notify_client_connection(client_name, connected=False)
                
            client_socket.close()
    
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Manager Server for Distributed Computing')
    parser.add_argument('--master-host', default='localhost', 
                        help='Master server hostname')
    parser.add_argument('--master-port', type=int, default=5000, 
                        help='Master server port')
    parser.add_argument('--host', default='0.0.0.0', 
                        help='Manager server hostname')
    parser.add_argument('--port', type=int, default=5001, 
                        help='Manager server port')
    
    args = parser.parse_args()
    
    manager = ManagerServer(
        master_host=args.master_host,
        master_port=args.master_port,
        host=args.host,
        port=args.port
    )
    
    try:
        manager.start()
    except KeyboardInterrupt:
        print("Manager server shutting down")