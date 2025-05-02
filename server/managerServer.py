import socket
import json
import threading
import queue
import os
import argparse
import time

HOST = '0.0.0.0'      # Where this proxy server will listen
PORT = 65431            # Port for the local clients to connect

UPSTREAM_HOST = '127.0.0.1'  # Upstream server IP
UPSTREAM_PORT = 65432        # Upstream server port

client_id_counter = 1
message_id_counter = 1  # New counter for message IDs
clients = {}  # client_id -> client_socket
request_queue = queue.Queue()
waiting_queue = queue.Queue()  # Queue for messages waiting for responses
response_event = threading.Event()

lock = threading.Lock()

HEARTBEAT_INTERVAL = 10
PENDING_MESSAGES = {}  # client_id -> (message, timestamp)
RETRY_INTERVAL = 20     # seconds
MESSAGE_TIMEOUT = 5     # seconds for waiting queue timeout


def sendUpstream(obj, upstream_socket):
    sendUpstreamDirect(obj, upstream_socket)


def sendUpstreamDirect(obj, upstream_socket):
    upstream_socket.send((json.dumps(obj) + "\n").encode('utf-8'))


def check_waiting_messages():
    """Check for timed out messages in the waiting queue and requeue them"""
    while True:
        time.sleep(1)
        current_time = time.time()
        
        # Check if any messages in the waiting queue have timed out
        waiting_items = []
        while not waiting_queue.empty():
            waiting_items.append(waiting_queue.get())
        
        for message, timestamp in waiting_items:
            if current_time - timestamp >= MESSAGE_TIMEOUT:
                # This message has timed out, put it back in the request queue
                print(f"[Timeout] Re-queuing message with ID {message.get('message_id')} from client {message.get('client_id')}")
                request_queue.put(message)
                response_event.set()  # Notify the upstream sender
            else:
                # Message hasn't timed out yet, put it back in the waiting queue
                waiting_queue.put((message, timestamp))




def heartbeat_thread(upstream_socket):
    while True:
        time.sleep(HEARTBEAT_INTERVAL)
        
        # Send heartbeat to upstream
        try:
            heartbeat_msg = {"type": "heartbeat", "manager_id": manager_id}
            sendUpstream(heartbeat_msg, upstream_socket)
        except Exception as e:
            print(f"[Heartbeat] Failed to send to upstream: {e}")
        
        # Send heartbeat to all clients
        with lock:
            for client_id, conn in list(clients.items()):
                try:
                    heartbeat = json.dumps({"type": "heartbeat"}).encode('utf-8')
                    conn.send(heartbeat)
                except Exception as e:
                    print(f"[Heartbeat] Failed to send to client {client_id}: {e}")
                    conn.close()
                    clients.pop(client_id, None)


def handle_client_connection(conn, addr, client_id):
    print(f"Client {client_id} connected from {addr}")
    clients[client_id] = conn

    # Send the client ID
    conn.send(json.dumps({'client_id': client_id}).encode('utf-8'))

    try:
        while True:
            buffer = ""
            while True:
                chunk = conn.recv(1024).decode('utf-8')
                if not chunk:
                    data = buffer
                    break
                buffer += chunk
                if '\n' in buffer:
                    data, buffer = buffer.split('\n', 1)
                    break

            message = json.loads(data)
            
            if message.get("type") == "heartbeat":
                continue  # Just ignore and wait for the next real message
            
            if(message.get("req") == "file"):
                print(f"Recieved file from client {client_id}")
            
            message['client_id'] = client_id  # Ensure client_id is present

            # Add the message to the queue
            request_queue.put(message)
            response_event.set()  # Notify the upstream sender

    except Exception as e:
        print(f"Client {client_id} error: {e}")
    finally:
        print(f"Client {client_id} disconnected")
        with lock:
            clients.pop(client_id, None)
        conn.close()


def listen_for_clients():
    global client_id_counter
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"Proxy server listening on {HOST}:{PORT}")

    while True:
        conn, addr = server_socket.accept()
        with lock:
            client_id = client_id_counter
            client_id_counter += 1
        threading.Thread(target=handle_client_connection, args=(conn, addr, client_id), daemon=True).start()


def listen_upstream(upstream):
    while True:
        try:
            buffer = ""
            while True:
                chunk = upstream.recv(1024).decode('utf-8')
                if not chunk:
                    data = buffer
                    break
                buffer += chunk
                if '\n' in buffer:
                    data, buffer = buffer.split('\n', 1)
                    break
                    
            if not data:
                print("Upstream connection closed.")
                break

            response = json.loads(data)

            if response.get("type") == "heartbeat":
                continue

            client_id = response.get('client_id')
            response_id = response.get('response_id')
            
            # Check if this is a response to a message in the waiting queue
            if response_id is not None:
                # Get all items from waiting queue to check
                waiting_items = []
                while not waiting_queue.empty():
                    waiting_items.append(waiting_queue.get())
                
                found_match = False
                for message, timestamp in waiting_items:
                    if message.get('message_id') == response_id:
                        # Found the corresponding message, don't put it back
                        print(f"Received response for message_id {response_id}")
                        found_match = True
                    else:
                        # Put back messages that aren't matched
                        waiting_queue.put((message, timestamp))
                
                if found_match:
                    print(f"Removed message {response_id} from waiting queue")
                else:
                    print(f"Response ID {response_id} did not match any waiting messages")
            
            if client_id is not None:
                with lock:
                    PENDING_MESSAGES.pop(client_id, None)

            if 'client_id' not in response:
                if('command' in response):
                    command = response['command']
                    print(f"Redirecting command {command} to all clients")
                    if command == 'shutdown':
                        print("Received shutdown command. Notifying all clients.")
                        with lock:
                            for client_conn in clients.values():
                                try:
                                    client_conn.send(json.dumps({'command': 'shutdown'}).encode('utf-8'))
                                except Exception as e:
                                    print(f"Error sending shutdown to client: {e}")
                            
                            os._exit(0)
                    elif command == 'report':
                        print("Received report command. Sending status to upstream.")
                        with lock:
                            report = {
                                'manager_id': response.get('manager_id'),  # use the one sent
                                'client_count': len(clients)
                            }
                        sendUpstream(report, upstream)
                        
                    else:
                        with lock:
                            for client_conn in clients.values():
                                try:
                                    client_conn.send(json.dumps(response).encode('utf-8'))
                                except Exception as e:
                                    print(f"Error sending shutdown to client: {e}")
                            
            else:
                # Forward regular response to the client
                client_id = response.get('client_id')
                with lock:
                    client_conn = clients.get(client_id)
                    if client_conn:
                        client_conn.send(json.dumps(response).encode('utf-8'))

        except json.JSONDecodeError:
            print("Error: Invalid JSON from upstream")
        except Exception as e:
            print(f"Error in upstream listener: {e}")
            break


def send_to_upstream():
    global manager_id
    global message_id_counter
    upstream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    upstream.connect((UPSTREAM_HOST, UPSTREAM_PORT))
    
    data = upstream.recv(1024).decode('utf-8')
    try:
        response = json.loads(data)
        if 'manager_id' in response:
            manager_id = response['manager_id']
            print(f"Registered with server. Manager ID: {manager_id}")

            # Now send the PC name (Windows)
            pc_name = os.getenv("COMPUTERNAME")
            if not pc_name:
                print("Error: Could not get computer name.")
                return

            pc_info = {
                'manager_id': manager_id,
                'pc_name': pc_name
            }
            upstream.sendall(json.dumps(pc_info).encode('utf-8'))
            print(f"Sent PC name: {pc_name} to server.")
        else:
            print("Error: Server did not send manager ID.")
            return
    except json.JSONDecodeError:
        print("Error: Invalid response from server during registration.")
        return

    print(f"Connected to upstream server at {UPSTREAM_HOST}:{UPSTREAM_PORT}")

    threading.Thread(target=listen_upstream, args=(upstream,), daemon=True).start()
    threading.Thread(target=heartbeat_thread, args=(upstream,), daemon=True).start()
    threading.Thread(target=check_waiting_messages, args=(), daemon=True).start()

    while True:
        message = request_queue.get()
        message['manager_id'] = manager_id
        
        # Add a unique message ID if this is a new message (not a retry)
        if 'message_id' not in message:
            with lock:
                message['message_id'] = message_id_counter
                message_id_counter += 1
        
        try:
            print(f"Sending message with ID {message['message_id']} from client {message['client_id']}")
            sendUpstream(message, upstream)
            
            # Add to waiting queue with current timestamp
            waiting_queue.put((message, time.time()))
            
            with lock:
                PENDING_MESSAGES[message['client_id']] = (message, time.time())
        except Exception as e:
            print(f"Error sending to upstream: {e}")
        request_queue.task_done()


def force_shutdown():
    print("Forcefully shutting down the proxy server.")
    with lock:
        for client_conn in clients.values():
            try:
                client_conn.send(json.dumps({'command': 'shutdown'}).encode('utf-8'))
                client_conn.close()
            except Exception as e:
                print(f"Error force-sending shutdown: {e}")
        clients.clear()
    
    os._exit(0)  # Immediately terminates the process

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Manager Server for Distributed Computing')
    parser.add_argument('--master-host', default='localhost', 
                        help='Master server hostname')
    parser.add_argument('--master-port', type=int, default=65432, 
                        help='Master server port')
    parser.add_argument('--host', default='0.0.0.0', 
                        help='Manager server hostname')
    parser.add_argument('--port', type=int, default=65431, 
                        help='Manager server port')
    

    args = parser.parse_args()

    HOST = args.host
    PORT = args.port
    
    UPSTREAM_HOST = args.master_host
    UPSTREAM_PORT = args.master_port

    # Start the thread that listens for local clients
    threading.Thread(target=listen_for_clients, daemon=True).start()

    # Start the handler to forward messages to upstream
    send_to_upstream()