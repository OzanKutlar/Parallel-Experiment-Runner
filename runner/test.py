import socket
import json
import argparse
import threading
import sys
import os

def listen_to_server(sock):
    try:
        while True:
            data = sock.recv(1024).decode('utf-8')
            if not data:
                print("Server closed the connection.")
                break

            try:
                response = json.loads(data)
                if 'command' in response and response['command'] == 'shutdown':
                    print("Received shutdown command. Exiting...")
                    sock.close()
                    os._exit(0)
                print("Response from server:", response)
            except json.JSONDecodeError:
                print("Invalid JSON received.")
    except Exception as e:
        print("Error in listening thread:", e)
        sock.close()
        sys.exit(1)

def send_to_server(sock):
    try:
        while True:
            msg = input("Enter message (or 'quit' to exit): ").strip()
            if msg.lower() == 'quit':
                print("Disconnecting...")
                sock.close()
                break

            request = {'req': msg}
            sock.send(json.dumps(request).encode('utf-8'))
    except Exception as e:
        print("Error in sending thread:", e)
        sock.close()

def test_client(proxy_host='127.0.0.1', proxy_port=65431):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((proxy_host, proxy_port))

        # Receive the client ID from proxy
        data = s.recv(1024).decode('utf-8')
        try:
            response = json.loads(data)
            if 'client_id' in response:
                client_id = response['client_id']
                print(f"Connected to proxy. Your client ID is: {client_id}")
            else:
                print("Failed to receive client ID.")
                return
        except json.JSONDecodeError:
            print("Invalid JSON received from proxy.")
            return

        # Start listening thread
        listen_thread = threading.Thread(target=listen_to_server, args=(s,), daemon=True)
        listen_thread.start()

        # Main thread handles sending
        send_to_server(s)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test client for proxy connection")
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Proxy server host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=65431, help='Proxy server port (default: 65431)')

    args = parser.parse_args()

    test_client(proxy_host=args.host, proxy_port=args.port)
