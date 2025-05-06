import threading
import logging
import time
from typing import Dict, Any, Optional, Tuple

# Use the updated SocketWrapper from the file (assuming it's saved as socket_wrapper.py)
try:
    from socket_wrapper import SocketWrapper, logger
except ImportError:
    print("Error: Make sure socket_wrapper.py is in the same directory.")
    exit(1)

# --- Configuration ---
HOST = '0.0.0.0'  # Listen on all available interfaces
PORT = 3753       # The single mandatory port
SERVER_ID = "MainServer"

# --- Server State ---
# Thread-safe storage for connected clients and registered sub-servers
clients: Dict[str, Dict[str, Any]] = {} # { client_id: {'wrapper': SocketWrapper, 'address': tuple, 'sub_server_info': dict} }
sub_servers: Dict[str, Dict[str, Any]] = {} # { sub_server_id: {'host': str, 'port': int, 'client_id': str} }
clients_lock = threading.Lock()
sub_servers_lock = threading.Lock()

# --- Message Handlers ---

def handle_register_subserver(message: Dict[str, Any], client_id: str, client_address: Tuple[str, int]) -> Optional[Dict[str, Any]]:
    """Handles requests from clients wanting to register as sub-servers."""
    sub_port = message.get('port')
    sub_id = message.get('id', client_id) # Use provided ID or default to client ID

    if not isinstance(sub_port, int) or not (0 < sub_port < 65536):
        logger.warning(f"Invalid port {sub_port} received from {client_id} @ {client_address}. Ignoring registration.")
        return {'type': 'REGISTER_ACK', 'status': 'ERROR', 'detail': 'Invalid port number'}

    # Use the client's connecting IP as the host for the sub-server
    sub_host = client_address[0]

    with sub_servers_lock:
        if sub_id in sub_servers:
             logger.warning(f"Sub-server ID {sub_id} already registered. Updating info.")
             # Potentially update existing entry or reject, here we update
        sub_servers[sub_id] = {'host': sub_host, 'port': sub_port, 'client_id': client_id}
        logger.info(f"Registered sub-server '{sub_id}' at {sub_host}:{sub_port} (Client: {client_id})")

    # Also store sub-server info with the client connection data
    with clients_lock:
        if client_id in clients:
            clients[client_id]['sub_server_info'] = {'id': sub_id, 'host': sub_host, 'port': sub_port}

    # Send acknowledgment back
    return {'type': 'REGISTER_ACK', 'status': 'OK', 'registered_id': sub_id}

def handle_get_subservers(message: Dict[str, Any], client_id: str, client_address: Tuple[str, int]) -> Optional[Dict[str, Any]]:
    """Handles requests for the list of available sub-servers."""
    logger.info(f"Client {client_id} @ {client_address} requested sub-server list.")
    with sub_servers_lock:
        # Return a copy to avoid issues with concurrent modification
        current_list = list(sub_servers.values())
    return {'type': 'SUBSERVER_LIST', 'servers': current_list}

def handle_echo(message: Dict[str, Any], client_id: str, client_address: Tuple[str, int]) -> Optional[Dict[str, Any]]:
    """Handles simple echo requests."""
    payload = message.get('payload', '')
    logger.info(f"Echo request from {client_id}: {payload}")
    return {'type': 'ECHO_RESPONSE', 'payload': payload}


# --- Default Message Handler ---

def default_message_handler(message: Dict[str, Any], client_id: str, client_address: Tuple[str, int]) -> Optional[Dict[str, Any]]:
    """Handles messages that don't match specific types."""
    message_type = message.get('type', 'UNKNOWN')
    message_id = message.get('message_id', 'N/A')
    logger.warning(f"Received unhandled message type '{message_type}' (ID: {message_id}) from {client_id} @ {client_address}")
    return {'type': 'ERROR', 'code': 'UNKNOWN_TYPE', 'detail': f"Message type '{message_type}' not handled by server."}


# --- Client Connection Handler ---

def handle_client_connection(client_wrapper: SocketWrapper, client_address: Tuple[str, int]):
    """
    Manages communication with a single connected client in a separate thread.
    """
    client_id = f"{client_address[0]}:{client_address[1]}" # Simple ID based on address
    logger.info(f"Handling connection from {client_id}")

    # Store client info
    with clients_lock:
        clients[client_id] = {'wrapper': client_wrapper, 'address': client_address, 'sub_server_info': None}

    # --- Register Message Callbacks for this Client ---
    # We use lambdas to pass the client_id and address to the handlers
    client_wrapper.register_callback(
        lambda msg: handle_register_subserver(msg, client_id, client_address),
        message_type='REGISTER_SUBSERVER'
    )
    client_wrapper.register_callback(
        lambda msg: handle_get_subservers(msg, client_id, client_address),
        message_type='GET_SUBSERVERS'
    )
    client_wrapper.register_callback(
        lambda msg: handle_echo(msg, client_id, client_address),
        message_type='ECHO_REQUEST'
    )
    # Register the default handler
    client_wrapper.register_callback(
         lambda msg: default_message_handler(msg, client_id, client_address)
         # No message_type specified, so it becomes the default
    )

    # --- Start Receiving Messages ---
    # The SocketWrapper needs its receiver loop started for this accepted connection
    client_wrapper.start_receiver()

    # --- Keep Thread Alive / Monitor Connection ---
    # The receiver thread runs in the background. This thread can monitor
    # the connection status or just wait.
    while client_wrapper.is_connected():
        try:
            # You could add periodic checks or commands here if needed
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received in client handler thread.")
            break # Allow graceful shutdown

    # --- Cleanup on Disconnect ---
    logger.info(f"Client {client_id} disconnected.")
    with clients_lock:
        if client_id in clients:
            # Check if this client was registered as a sub-server
            sub_server_info = clients[client_id].get('sub_server_info')
            if sub_server_info:
                sub_id_to_remove = sub_server_info.get('id')
                with sub_servers_lock:
                    if sub_id_to_remove and sub_id_to_remove in sub_servers:
                        logger.info(f"Removing registered sub-server '{sub_id_to_remove}' due to client disconnect.")
                        del sub_servers[sub_id_to_remove]
            # Remove client from active clients list
            del clients[client_id]

    # Ensure the wrapper is closed (might already be closed by receiver loop exit)
    client_wrapper.close()


# --- Main Server Loop ---

def run_server():
    """Starts the main server listening loop."""
    listener_socket = SocketWrapper()

    if not listener_socket.bind(HOST, PORT):
        logger.error(f"Failed to bind to {HOST}:{PORT}. Exiting.")
        return

    listener_socket.listen()
    logger.info(f"{SERVER_ID} listening on {HOST}:{PORT}")

    try:
        while True:
            # Accept new connections
            client_wrapper, client_address = listener_socket.accept()

            if client_wrapper and client_address:
                # Start a new thread to handle this client
                # Pass the wrapper and address to the handler function
                thread = threading.Thread(target=handle_client_connection, args=(client_wrapper, client_address), daemon=True)
                thread.start()
            else:
                # Accept failed, possibly due to socket closing
                logger.warning("Socket accept returned None, might be shutting down.")
                # Add a small delay to prevent tight loop on errors
                time.sleep(0.1)
                # Consider breaking the loop if the listener socket is no longer valid
                # if not listener_socket.is_listening(): # (Need to add an is_listening method to wrapper if needed)
                #    break

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Shutting down server...")
    except Exception as e:
        logger.exception(f"An unexpected error occurred in the main server loop: {e}")
    finally:
        logger.info("Closing listener socket.")
        listener_socket.close()
        # Optionally, close all active client connections
        with clients_lock:
            logger.info("Closing all active client connections...")
            for client_id, client_data in list(clients.items()): # Iterate over a copy
                 client_data['wrapper'].close()
        logger.info("Server shutdown complete.")


if __name__ == "__main__":
    run_server()
