import socket
import json
import argparse

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

        while True:
            msg = input("Enter message (or 'quit' to exit): ").strip()
            if msg.lower() == 'quit':
                print("Disconnecting...")
                break

            request = {
                'req': msg  # Don't include client_id – the proxy will do it
            }

            s.send(json.dumps(request).encode('utf-8'))

            data = s.recv(1024).decode('utf-8')
            try:
                response = json.loads(data)
                print("Response from server:", response)
            except json.JSONDecodeError:
                print("Invalid response received.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test client for proxy connection")
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Proxy server host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=65431, help='Proxy server port (default: 65431)')

    args = parser.parse_args()

    test_client(proxy_host=args.host, proxy_port=args.port)
