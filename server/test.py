import time
import logging
import random
from typing import Dict, Any, Optional, List

# Use the updated SocketWrapper from the file (assuming it's saved as socket_wrapper.py)
try:
    from socket_wrapper import SocketWrapper, logger
except ImportError:
    print("Error: Make sure socket_wrapper.py is in the same directory.")
    exit(1)

# --- Configuration ---
MAIN_SERVER_HOST = '127.0.0.1' # Address of the main server
MAIN_SERVER_PORT = 3753        # Port of the main server
CLIENT_ID = f"Client_{random.randint(1000, 9999)}"

# --- State ---
available_sub_servers: List[Dict[str, Any]] = []
sub_server_connection: Optional[SocketWrapper] = None

# --- Message Handlers ---

def handle_main_server_list(message: Dict[str, Any]) -> None:
    """Handles the SUBSERVER_LIST response from the main server."""
    global available_sub_servers
    if message.get('type') == 'SUBSERVER_LIST':
        servers = message.get('servers', [])
        logger.info(f"Received sub-server list: {servers}")
        available_sub_servers = servers
    else:
        logger.warning(f"Received unexpected message from main server: {message}")

def handle_sub_server_response(message: Dict[str, Any]) -> None:
    """Handles responses received FROM the connected sub-server."""
    msg_type = message.get('type')
    response_to = message.get('response_to')
    logger.info(f"Received from Sub-Server (Type: {msg_type}, ResponseTo: {response_to}): {message}")
    # Process specific responses like ECHO_RESPONSE, etc.


# --- Main Client Logic ---

def main():
    global available_sub_servers, sub_server_connection

    # --- 1. Connect to Main Server to Get List ---
    logger.info(f"[{CLIENT_ID}] Connecting to Main Server ({MAIN_SERVER_HOST}:{MAIN_SERVER_PORT}) to get sub-server list...")
    main_conn = SocketWrapper()
    main_conn.register_callback(handle_main_server_list) # Only need to handle the list response

    if not main_conn.connect(MAIN_SERVER_HOST, MAIN_SERVER_PORT, max_attempts=3, retry_delay=2):
        logger.error(f"[{CLIENT_ID}] Could not connect to Main Server. Exiting.")
        return

    # Send request for sub-server list
    list_request = {'type': 'GET_SUBSERVERS'}
    list_request_id = main_conn.send_to(list_request)

    if not list_request_id:
        logger.error(f"[{CLIENT_ID}] Failed to send request to Main Server.")
        main_conn.close()
        return

    # Wait a short time for the response (receiver runs in background)
    # A more robust approach would use events or check a flag set by the callback
    time.sleep(2) # Simple wait

    main_conn.close() # Disconnect from main server
    logger.info(f"[{CLIENT_ID}] Disconnected from Main Server.")

    # --- 2. Choose and Connect to a Sub-Server ---
    if not available_sub_servers:
        logger.warning(f"[{CLIENT_ID}] No sub-servers available. Exiting.")
        return

    # Choose a sub-server (e.g., the first one)
    target_sub_server = available_sub_servers[0]
    target_host = target_sub_server.get('host')
    target_port = target_sub_server.get('port')
    target_id = target_sub_server.get('client_id', 'Unknown SubServer') # Or use a dedicated sub-server ID if available

    if not target_host or not target_port:
        logger.error(f"[{CLIENT_ID}] Invalid sub-server info received: {target_sub_server}. Exiting.")
        return

    logger.info(f"[{CLIENT_ID}] Connecting to Sub-Server '{target_id}' at {target_host}:{target_port}...")
    sub_server_connection = SocketWrapper()
    sub_server_connection.register_callback(handle_sub_server_response) # Handle responses from sub-server

    if not sub_server_connection.connect(target_host, target_port, max_attempts=3, retry_delay=3):
        logger.error(f"[{CLIENT_ID}] Failed to connect to Sub-Server '{target_id}'. Exiting.")
        return

    logger.info(f"[{CLIENT_ID}] Successfully connected to Sub-Server '{target_id}'.")

    # --- 3. Interact with Sub-Server ---
    try:
        for i in range(5):
            if not sub_server_connection.is_connected():
                logger.warning(f"[{CLIENT_ID}] Lost connection to sub-server.")
                break

            message_payload = {'type': 'ECHO_REQUEST', 'payload': f'Hello from {CLIENT_ID} - message {i+1}'}
            logger.info(f"[{CLIENT_ID}] Sending: {message_payload}")
            sent_id = sub_server_connection.send_to(message_payload)
            if sent_id:
                logger.info(f"[{CLIENT_ID}] Message sent (ID: {sent_id})")
            else:
                logger.error(f"[{CLIENT_ID}] Failed to send message.")
                break # Stop trying if send fails
            time.sleep(random.uniform(1, 3)) # Wait a bit between messages

    except KeyboardInterrupt:
        logger.info(f"[{CLIENT_ID}] KeyboardInterrupt received.")
    finally:
        if sub_server_connection and sub_server_connection.is_connected():
            logger.info(f"[{CLIENT_ID}] Closing connection to sub-server.")
            sub_server_connection.close()
        logger.info(f"[{CLIENT_ID}] Client shutdown complete.")


if __name__ == "__main__":
    main()
