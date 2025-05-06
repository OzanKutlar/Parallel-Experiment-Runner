import threading
import logging
import time
import random
from typing import Dict, Any, Optional, Tuple

# Use the updated SocketWrapper from the file (assuming it's saved as socket_wrapper.py)
try:
    from socket_wrapper import SocketWrapper, logger
except ImportError:
    print("Error: Make sure socket_wrapper.py is in the same directory.")
    exit(1)

# --- Configuration ---
MAIN_SERVER_HOST = '127.0.0.1' # Address of the main server
MAIN_SERVER_PORT = 3753        # Port of the main server
SUB_SERVER_HOST = '0.0.0.0'    # Host for this sub-server to listen on
SUB_SERVER_ID = f"SubServer_{random.randint(1000, 9999)}" # Unique-ish ID

# --- State ---
main_server_connection: Optional[SocketWrapper] = None
sub_server_listener: Optional[SocketWrapper] = None
my_listening_port: Optional[int] = None
connected_sub_clients: Dict[str, SocketWrapper] = {} # { sub_client_id: wrapper }
sub_clients_lock = threading.Lock()

# --- Message Handlers for Main Server Communication ---

def handle_main_server_response(message: Dict[str, Any]) -> None:
    """Handles responses received FROM the main server."""
    msg_type = message.get('type')
    response_to = message.get('response_to')
    logger.info(f"Received from Main Server (Type: {msg_type}, ResponseTo: {response_to}): {message}")

    if msg_type == 'REGISTER_ACK':
        status = message.get('status')
        if status == 'OK':
            registered_id = message.get('registered_id')
            logger.info(f"Successfully registered with Main Server as '{registered_id}' on port {my_listening_port}")
        else:
            detail = message.get('detail')
            logger.error(f"Failed to register with Main Server: {detail}")
            # Consider shutdown or retry logic here
    # Add handlers for other message types from the main server if needed

# --- Message Handlers for Sub-Client Communication ---

def handle_sub_client_echo(message: Dict[str, Any], sub_client_id: str) -> Optional[Dict[str, Any]]:
    """Handles echo requests FROM clients connected TO this sub-server."""
    payload = message.get('payload', '')
    logger.info(f"Echo request from sub-client {sub_client_id}: {payload}")
    return {'type': 'ECHO_RESPONSE', 'payload': f"{SUB_SERVER_ID} echoes: {payload}"}

def default_sub_client_handler(message: Dict[str, Any], sub_client_id: str) -> Optional[Dict[str, Any]]:
    """Default handler for messages from sub-clients."""
    message_type = message.get('type', 'UNKNOWN')
    message_id = message.get('message_id', 'N/A')
    logger.warning(f"Received unhandled message type '{message_type}' (ID: {message_id}) from sub-client {sub_client_id}")
    return {'type': 'ERROR', 'code': 'UNKNOWN_TYPE', 'detail': f"Message type '{message_type}' not handled by {SUB_SERVER_ID}."}


# --- Sub-Client Connection Handler ---

def handle_sub_client_connection(sub_client_wrapper: SocketWrapper, sub_client_address: Tuple[str, int]):
    """Manages communication with a single client connected TO this sub-server."""
    sub_client_id = f"{sub_client_address[0]}:{sub_client_address[1]}"
    logger.info(f"Sub-server accepted connection from {sub_client_id}")

    with sub_clients_lock:
        connected_sub_clients[sub_client_id] = sub_client_wrapper

    # Register message handlers for this specific sub-client
    sub_client_wrapper.register_callback(
        lambda msg: handle_sub_client_echo(msg, sub_client_id),
        message_type='ECHO_REQUEST'
    )
    sub_client_wrapper.register_callback(
        lambda msg: default_sub_client_handler(msg, sub_client_id)
        # Default handler
    )

    # Start the receiver loop for this sub-client
    sub_client_wrapper.start_receiver()

    # Monitor connection
    while sub_client_wrapper.is_connected():
        time.sleep(1)

    # Cleanup on disconnect
    logger.info(f"Sub-client {sub_client_id} disconnected.")
    with sub_clients_lock:
        if sub_client_id in connected_sub_clients:
            del connected_sub_clients[sub_client_id]
    sub_client_wrapper.close()


# --- Sub-Server Listening Loop ---

def run_sub_server_listener(listener: SocketWrapper):
    """Listens for and accepts connections from other clients."""
    global my_listening_port
    try:
        # Get the dynamically assigned port
        my_listening_port = listener.socket.getsockname()[1]
        logger.info(f"{SUB_SERVER_ID} starting to listen on {SUB_SERVER_HOST}:{my_listening_port}")
        listener.listen()

        # --- Register with Main Server AFTER we know the port ---
        if main_server_connection and main_server_connection.is_connected():
            register_msg = {
                'type': 'REGISTER_SUBSERVER',
                'id': SUB_SERVER_ID,
                'port': my_listening_port
            }
            logger.info(f"Sending registration to Main Server: {register_msg}")
            main_server_connection.send_to(register_msg)
        else:
             logger.error("Cannot register with Main Server: Connection not established.")
             # Handle this case - maybe retry connection or shut down?


        # --- Accept Loop ---
        while True:
            sub_client_wrapper, sub_client_address = listener.accept()
            if sub_client_wrapper and sub_client_address:
                thread = threading.Thread(
                    target=handle_sub_client_connection,
                    args=(sub_client_wrapper, sub_client_address),
                    daemon=True
                )
                thread.start()
            else:
                logger.warning("Sub-server listener accept failed, might be shutting down.")
                break # Exit loop if accept fails

    except Exception as e:
        logger.exception(f"Error in sub-server listening loop: {e}")
    finally:
        logger.info("Sub-server listener shutting down.")
        listener.close()


# --- Main Execution ---

def main():
    global main_server_connection, sub_server_listener

    # --- 1. Connect to Main Server ---
    logger.info(f"Attempting to connect to Main Server at {MAIN_SERVER_HOST}:{MAIN_SERVER_PORT}")
    main_server_connection = SocketWrapper()
    # Register the callback *before* connecting
    main_server_connection.register_callback(handle_main_server_response) # Default handler for main server msgs

    # Connect with infinite retries, increasing delay
    if not main_server_connection.connect(MAIN_SERVER_HOST, MAIN_SERVER_PORT, max_attempts=-1, retry_delay=5):
        logger.error("Failed to connect to Main Server after multiple attempts. Exiting.")
        return # Cannot proceed without main server connection

    logger.info("Successfully connected to Main Server.")
    # The receiver thread for the main server connection is now running.

    # --- 2. Start Sub-Server Listener ---
    sub_server_listener = SocketWrapper()
    # Bind to port 0 to let the OS choose an available ephemeral port
    if not sub_server_listener.bind(SUB_SERVER_HOST, 0):
        logger.error("Failed to bind sub-server listener socket. Exiting.")
        main_server_connection.close()
        return

    # Start the listener loop in a separate thread
    listener_thread = threading.Thread(target=run_sub_server_listener, args=(sub_server_listener,), daemon=True)
    listener_thread.start()

    # --- 3. Keep Main Thread Alive ---
    # Keep the main thread alive to allow background threads to run
    # and handle KeyboardInterrupt for graceful shutdown.
    try:
        while True:
            # Check if main server connection is still alive
            if not main_server_connection.is_connected():
                logger.error("Connection to Main Server lost. Attempting to reconnect...")
                # Implement reconnection logic here if desired, or shut down.
                # For simplicity, we'll just log and break for now.
                break

            # Add other main loop tasks if needed
            time.sleep(2)

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Shutting down...")
    finally:
        logger.info("Closing connections...")
        if main_server_connection:
            main_server_connection.close()
        if sub_server_listener:
            sub_server_listener.close() # This should signal the listener thread to stop accept()

        # Close connections to sub-clients
        with sub_clients_lock:
             for wrapper in connected_sub_clients.values():
                 wrapper.close()

        logger.info("Sub-Server / Client shutdown complete.")


if __name__ == "__main__":
    main()
