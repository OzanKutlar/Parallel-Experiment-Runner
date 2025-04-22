import socket
import json
import threading
import time
import platform
import argparse

class Client:
    def __init__(self, manager_host='localhost', manager_port=5001):
        self.manager_host = manager_host
        self.manager_port = manager_port
        self.socket = None
        self.client_name = platform.node()  # Get computer name
        self.running = False
        self.manager_name = None
        
    def connect(self):
        """Connect to the manager server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.manager_host, self.manager_port))
            
            # Register with manager
            registration = {
                'type': 'registration',
                'name': self.client_name
            }
            self.socket.send(json.dumps(registration).encode('utf-8'))
            
            # Receive acknowledgment
            data = self.socket.recv(1024).decode('utf-8')
            response = json.loads(data)
            
            if response.get('type') == 'registration_ack' and response.get('status') == 'connected':
                self.manager_name = response.get('manager_name', 'Unknown Manager')
                print(f"Connected to manager '{self.manager_name}' at {self.manager_host}:{self.manager_port}")
                self.running = True
                return True
            else:
                print("Failed to register with manager server")
                self.socket.close()
                return False
                
        except Exception as e:
            print(f"Connection error: {e}")
            if self.socket:
                self.socket.close()
            return False
    
    def receive_messages(self):
        """Listen for messages from the manager server."""
        try:
            while self.running:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    print("Connection to manager server lost")
                    self.running = False
                    break
                
                try:
                    message = json.loads(data)
                    print(f"Received from manager: {message}")
                except json.JSONDecodeError:
                    print(f"Received invalid JSON from manager")
                    
        except Exception as e:
            print(f"Error receiving messages: {e}")
            self.running = False
        finally:
            self.socket.close()
    
    def send_message(self, message_type, content=None):
        """Send a message to the manager server."""
        if not self.running or not self.socket:
            print("Not connected to manager")
            return False
            
        message = {
            'type': message_type,
            'timestamp': time.time(),
            'client_name': self.client_name
        }
        
        if content:
            message['content'] = content
            
        try:
            self.socket.send(json.dumps(message).encode('utf-8'))
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            self.running = False
            return False
    
    def start(self):
        """Start the client and begin communication with the manager."""
        if not self.connect():
            print("Failed to connect to manager server")
            return
            
        # Start a thread to receive messages
        receiver_thread = threading.Thread(target=self.receive_messages)
        receiver_thread.daemon = True
        receiver_thread.start()
        
        try:
            # Simple command loop
            self.send_heartbeat()
            while self.running:
                print("\nOptions:")
                print("1. Send heartbeat")
                print("2. Request task")
                print("3. Send test message")
                print("4. Quit")
                
                choice = input("Enter your choice (1-4): ")
                
                if choice == '1':
                    self.send_heartbeat()
                elif choice == '2':
                    self.request_task()
                elif choice == '3':
                    message = input("Enter message: ")
                    self.send_message('test', message)
                elif choice == '4':
                    break
                else:
                    print("Invalid choice")
                    
        except KeyboardInterrupt:
            print("\nClient shutting down...")
        finally:
            self.running = False
            if self.socket:
                self.socket.close()
    
    def send_heartbeat(self):
        """Send a heartbeat to the manager server."""
        self.send_message('heartbeat', {'status': 'active'})
    
    def request_task(self):
        """Request a task from the manager server."""
        self.send_message('task_request', {'resources': {'cpu': 4, 'memory': 8}})
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Client for Distributed Computing')
    parser.add_argument('--manager-host', default='localhost', 
                        help='Manager server hostname')
    parser.add_argument('--manager-port', type=int, default=5001, 
                        help='Manager server port')
    
    args = parser.parse_args()
    
    client = Client(
        manager_host=args.manager_host,
        manager_port=args.manager_port
    )
    
    client.start()