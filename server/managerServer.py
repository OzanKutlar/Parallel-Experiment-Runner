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
clients = {}  # client_id -> client_socket
request_queue = queue.Queue()
response_event = threading.Event()

lock = threading.Lock()

HEARTBEAT_INTERVAL = 10
PENDING_MESSAGES = {}  # client_id -> (message, timestamp)
RETRY_INTERVAL = 1     # seconds

def sendUpstream(obj, upstream_socket):
    upstream_socket.send((json.dumps(obj) + "\n").encode('utf-8'))

def retry_unacknowledged_messages(upstream_socket):
    while True:
        time.sleep(1)
        current_time = time.time()
        with lock:
            for client_id, (message, timestamp) in list(PENDING_MESSAGES.items()):
                if current_time - timestamp >= RETRY_INTERVAL:
                    try:
                        print(f"[Retry] Resending message from client {client_id}")
                        sendUpstream(message, upstream_socket)
                        PENDING_MESSAGES[client_id] = (message, current_time)
                    except Exception as e:
                        print(f"Failed to resend message for client {client_id}: {e}")


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
            data = upstream.recv(1024)
            if not data:
                print("Upstream connection closed.")
                break

            response = json.loads(data.decode('utf-8'))

            if response.get("type") == "heartbeat":
                continue

            client_id = response.get('client_id')
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
    upstream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    upstream.connect((UPSTREAM_HOST, UPSTREAM_PORT))
    
    data = upstream.recv(1024).decode('utf-8')
    try:
        response = json.loads(data)
        if 'manager_id' in response:
            manager_id = response['manager_id']
            print(f"Registered with server. Manager ID: {manager_id}")
        else:
            print("Error: Server did not send manager ID.")
            return
    except json.JSONDecodeError:
        print("Error: Invalid response from server during registration.")
        return

    print(f"Connected to upstream server at {UPSTREAM_HOST}:{UPSTREAM_PORT}")

    threading.Thread(target=listen_upstream, args=(upstream,), daemon=True).start()
    threading.Thread(target=heartbeat_thread, args=(upstream,), daemon=True).start()
    threading.Thread(target=retry_unacknowledged_messages, args=(upstream,), daemon=True).start()

    while True:
        message = request_queue.get()
        message['manager_id'] = manager_id
        try:
            sendUpstream(message, upstream)
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
