import threading
import time
import queue
import logging
import uuid
from typing import Dict, Any, Optional, Tuple

from socket_wrapper import SocketWrapper, logger as wrapper_logger

# Configure manager server logging
logger = logging.getLogger('manager_server')
logger.setLevel(logging.INFO)
if not logger.handlers: # Avoid adding multiple handlers if re-run in same session
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# wrapper_logger.addHandler(handler) # Optionally share handler
# wrapper_logger.setLevel(logging.INFO)


MAIN_SERVER_HOST = 'localhost'
MAIN_SERVER_PORT = 3753

MANAGER_LISTEN_HOST = '0.0.0.0'
MANAGER_LISTEN_PORT = 3754 # Each manager instance would need a unique port or dynamic assignment
MAX_DOWNSTREAM_CLIENTS = 40 # As per requirement
MESSAGE_QUEUE_MAX_SIZE = 200 # Max messages to buffer from downstream clients

# --- Manager State ---
# Connection to the main upstream server
upstream_wrapper: Optional[SocketWrapper] = None
upstream_connected = threading.Event()

# Server for downstream clients
downstream_listener_socket: Optional[SocketWrapper] = None

# Connected downstream clients: client_address -> SocketWrapper
connected_downstream_clients: Dict[Tuple[str, int], SocketWrapper] = {}
downstream_clients_lock = threading.Lock()

# Message queue for relaying messages from downstream clients to the main server
# Each item could be (message_dict, original_client_address_tuple)
message_relay_queue = queue.Queue(maxsize=MESSAGE_QUEUE_MAX_SIZE)

# Track messages sent upstream to correlate responses back to downstream clients
# message_id (original from client) -> (downstream_client_socket_wrapper, original_message_dict, timestamp, retries)
pending_upstream_responses: Dict[str, Tuple[SocketWrapper, Dict[str, Any], float, int]] = {}
pending_responses_lock = threading.Lock()
UPSTREAM_RESPONSE_TIMEOUT = 10  # seconds
MAX_UPSTREAM_RETRIES = 3

exit_event = threading.Event() # Global shutdown signal for the manager

# --- Callbacks for Upstream (Main Server) Connection ---
def handle_main_server_response(message: Dict[str, Any]) -> None:
    """
    Callback for messages received from the main server.
    This function is executed by the upstream_wrapper's receiver thread.
    It should not return a value, as it's processing a response, not generating a new one for upstream.
    """
    original_client_msg_id = message.get('client_original_id') # This should be the ID from the end-client
    # The message_id in `message` itself is the one used between manager and main_server.
    # If main_server correctly uses the manager's sent message_id for its response,
    # then message.get('message_id') is what we need.
    # Let's assume main_server's response `message_id` is the one we sent it.

    msg_id_for_routing = message.get('message_id') # This should be the ID the manager used to send to main server

    logger.info(f"Manager received from MainServer (for msg_id {msg_id_for_routing}): {message.get('type')} - {message.get('payload')}")

    with pending_responses_lock:
        if msg_id_for_routing in pending_upstream_responses:
            downstream_client_wrapper, _, _, _ = pending_upstream_responses.pop(msg_id_for_routing)

            # Forward the response to the correct downstream client
            # The response from main_server should ideally contain the original client's message_id
            # if it was relayed. If not, we use the msg_id_for_routing (which was the client's original)
            # The `message` dict from main_server is what we forward.
            # Ensure the message_id in the forwarded message is the one the client expects.

            # The `message` dict already contains the correct 'message_id' (which was client's original)
            # because the main_server's wrapper's _process_message uses the incoming message_id for the response.
            sent_to_client = downstream_client_wrapper.send_to(message, message_id=msg_id_for_routing)
            if sent_to_client:
                logger.info(f"Manager relayed response for {msg_id_for_routing} to client {downstream_client_wrapper.address}")
            else:
                logger.error(f"Manager failed to relay response for {msg_id_for_routing} to client {downstream_client_wrapper.address}")
        else:
            logger.warning(f"Manager received response from MainServer for unknown/timed-out message_id: {msg_id_for_routing}. Discarding.")
    return None # This callback processes a response, doesn't generate a new one for upstream.

# --- Callbacks for Downstream (Client) Connections ---
def handle_downstream_client_message(message: Dict[str, Any], client_wrapper: SocketWrapper) -> None:
    """
    Callback for messages received from a downstream client.
    This function is executed by the client_wrapper's receiver thread.
    It should not return a value to be auto-sent by the wrapper, as the response comes from upstream.
    """
    message_id = message.get('message_id')
    client_address = client_wrapper.address
    logger.info(f"Manager received from client {client_address} (msg_id: {message_id}): {message.get('type')} - {message.get('payload')}")

    if not message_id:
        logger.warning(f"Manager received message without ID from {client_address}. Discarding.")
        return None # No response

    # Add to relay queue. The message itself contains the client's original message_id.
    try:
        # We need to associate this message with the client_wrapper for the response later.
        # The message_relay_thread will handle this.
        # The item in queue should be (message_dict_from_client, client_socket_wrapper_instance)
        message_package = (message, client_wrapper)
        message_relay_queue.put(message_package, timeout=1.0) # Non-blocking put with timeout
        logger.debug(f"Message {message_id} from {client_address} added to relay queue.")
    except queue.Full:
        logger.warning(f"Relay queue full. Message {message_id} from {client_address} dropped.")
        # Optionally, send an error back to the client
        error_response = {
            "type": "manager_error",
            "payload": "Manager queue full, please try again later.",
            "status": "queue_full",
            "message_id": message_id # Use client's message_id for the error response
        }
        client_wrapper.send_to(error_response, message_id=message_id)

    return None # No direct response from this handler; actual response comes via main server.


# --- Threads ---
def connect_to_main_server_thread():
    """Manages connection to the main server."""
    global upstream_wrapper
    logger.info("Manager attempting to connect to Main Server...")

    # Create a unique name for this manager's upstream wrapper for logging
    manager_id = f"Manager@{MANAGER_LISTEN_HOST}:{MANAGER_LISTEN_PORT}"
    upstream_wrapper = SocketWrapper(name=f"{manager_id}-Upstream")
    upstream_wrapper.register_callback(handle_main_server_response) # For responses from main server

    while not exit_event.is_set():
        if not upstream_wrapper.is_connected():
            logger.info(f"Manager connecting to Main Server at {MAIN_SERVER_HOST}:{MAIN_SERVER_PORT}")
            if upstream_wrapper.connect(MAIN_SERVER_HOST, MAIN_SERVER_PORT, max_attempts=1, retry_delay=0): # Try once
                logger.info("Manager connected to Main Server.")
                upstream_connected.set()
            else:
                logger.warning("Manager failed to connect to Main Server. Retrying in 10s...")
                upstream_connected.clear()
                # The wrapper's connect has its own retry, but we add a delay here before re-calling connect
                # if it fails all its internal attempts.
                # For this setup, connect has infinite retries if max_attempts is -1.
                # Let's use max_attempts=1 in connect and handle longer retry period here.
                if exit_event.wait(10): # Wait for 10s or until exit_event is set
                    break
        else:
            # Connection is active, just wait or do periodic checks
             if exit_event.wait(5): # Wait for 5s or until exit_event is set
                break

    upstream_connected.clear()
    if upstream_wrapper:
        upstream_wrapper.close()
    logger.info("Manager's connection thread to Main Server terminated.")


def message_relay_thread():
    """
    Thread to take messages from the local queue and send them to the main server.
    """
    logger.info("Message relay thread started.")
    while not exit_event.is_set():
        if not upstream_connected.is_set():
            # logger.debug("Relay: Upstream not connected, waiting...")
            time.sleep(0.5) # Wait for upstream connection
            continue

        try:
            message_from_client, client_socket_wrapper = message_relay_queue.get(timeout=1.0)

            client_original_message_id = message_from_client.get('message_id')
            if not client_original_message_id:
                logger.error(f"Relay: Message from client {client_socket_wrapper.address} has no message_id. Discarding.")
                message_relay_queue.task_done()
                continue

            # The message_from_client already has 'message_id' from the client.
            # We will use THIS ID when sending to the main server.
            # The main server's response should also use this ID.
            # SocketWrapper's send_to will use this if provided.

            # Store for response correlation and retry
            with pending_responses_lock:
                # Check if already trying to send this (e.g. from a previous failed attempt)
                if client_original_message_id in pending_upstream_responses:
                    _, _, _, retries = pending_upstream_responses[client_original_message_id]
                    if retries >= MAX_UPSTREAM_RETRIES:
                        logger.error(f"Relay: Message {client_original_message_id} from {client_socket_wrapper.address} exceeded max retries to main server. Dropping.")
                        pending_upstream_responses.pop(client_original_message_id, None) # Remove if present
                        # Optionally notify client
                        error_payload = {"type": "error", "status": "upstream_timeout", "message": "Failed to get response from main server."}
                        client_socket_wrapper.send_to(error_payload, message_id=client_original_message_id)
                        message_relay_queue.task_done()
                        continue
                    # It's already being tracked, likely by the retry_pending_messages_thread.
                    # Or, this is a quick re-queue. For now, let's assume retry thread handles it.
                    # If we want to send immediately, we update the tracking.

                pending_upstream_responses[client_original_message_id] = \
                    (client_socket_wrapper, message_from_client, time.time(), 0) # (wrapper, original_msg, timestamp, retries)

            logger.info(f"Relay: Sending message {client_original_message_id} from client {client_socket_wrapper.address} to Main Server.")

            # We need to ensure the 'client_original_id' is part of the message if the main server needs it.
            # The message_from_client might already be structured correctly.
            # For this example, let's assume message_from_client is what we send.
            # The `message_id` parameter to `send_to` ensures that ID is used.
            sent_id = upstream_wrapper.send_to(message_from_client, message_id=client_original_message_id)

            if not sent_id:
                logger.error(f"Relay: Failed to send message {client_original_message_id} to Main Server. Will be retried.")
                # The retry_pending_messages_thread will handle this.
                # No need to re-queue here, as it's already in pending_upstream_responses.
            else:
                logger.debug(f"Relay: Message {sent_id} successfully sent to Main Server.")
                # If send was successful, the pending_upstream_responses entry is now waiting for a response.

            message_relay_queue.task_done()

        except queue.Empty:
            continue # No messages in queue, loop again
        except Exception as e:
            logger.error(f"Exception in message_relay_thread: {e}", exc_info=True)
            time.sleep(1) # Avoid rapid spin on error

    logger.info("Message relay thread terminated.")


def retry_pending_messages_thread():
    """
    Periodically checks for messages sent to the main server that haven't received a response
    and retries them if necessary.
    """
    logger.info("Retry pending messages thread started.")
    while not exit_event.is_set():
        time.sleep(UPSTREAM_RESPONSE_TIMEOUT / 2) # Check periodically

        if not upstream_connected.is_set():
            continue

        messages_to_retry = []
        with pending_responses_lock:
            current_time = time.time()
            for msg_id, (client_wrapper, original_msg, ts, retries) in list(pending_upstream_responses.items()):
                if current_time - ts > UPSTREAM_RESPONSE_TIMEOUT:
                    if retries < MAX_UPSTREAM_RETRIES:
                        logger.warning(f"Retry: Message {msg_id} to Main Server timed out. Attempting retry {retries + 1}.")
                        messages_to_retry.append((msg_id, client_wrapper, original_msg, retries + 1))
                    else:
                        logger.error(f"Retry: Message {msg_id} to Main Server exceeded max retries. Dropping.")
                        # Notify original client
                        error_payload = {"type": "error", "status": "upstream_max_retries", "message": "Failed to get response from main server after multiple retries."}
                        client_wrapper.send_to(error_payload, message_id=msg_id)
                        pending_upstream_responses.pop(msg_id, None) # Remove from pending

        for msg_id, client_wrapper, original_msg, new_retry_count in messages_to_retry:
            sent_id = upstream_wrapper.send_to(original_msg, message_id=msg_id)
            if sent_id:
                logger.info(f"Retry: Successfully resent message {msg_id} to Main Server (attempt {new_retry_count}).")
                with pending_responses_lock:
                    if msg_id in pending_upstream_responses: # Update timestamp and retry count
                         _, _, _, _old_retries = pending_upstream_responses[msg_id]
                         pending_upstream_responses[msg_id] = (client_wrapper, original_msg, time.time(), new_retry_count)
            else:
                logger.error(f"Retry: Failed to resend message {msg_id} to Main Server (attempt {new_retry_count}). Will try again if connection recovers.")
                # Keep it in pending_upstream_responses, connection might be down.
                # The main connect_to_main_server_thread will handle reconnecting.
    logger.info("Retry pending messages thread terminated.")


def downstream_client_connection_thread(client_wrapper: SocketWrapper, client_address: tuple):
    """
    Dedicated thread to manage a single downstream client connection.
    The SocketWrapper's internal _receiver_loop will handle message receiving.
    This thread is mostly for lifetime management of the client connection.
    """
    logger.info(f"Manager: Thread started for downstream client {client_address}")

    # Register a specific handler for this client_wrapper instance
    # Need to pass client_wrapper to the handler, so use a lambda or functools.partial
    # The SocketWrapper's callback signature is `callback(message: Dict) -> Optional[Dict]`
    # We need to give it `client_wrapper` context.
    # One way: the wrapper itself could pass itself to the callback if designed that way.
    # Simpler: The main accept loop registers it.
    # Here, the `client_wrapper` is already set up with its receiver loop.
    # The callback `handle_downstream_client_message` needs to know which wrapper it's for.
    # The current SocketWrapper doesn't pass itself to the callback.
    # So, the `handle_downstream_client_message` needs to be adapted or registration needs to be clever.

    # Let's assume the `accept_downstream_clients` loop sets the callback correctly.
    # This thread's main job is to monitor the client_wrapper's connected status.
    while client_wrapper.is_connected() and not exit_event.is_set():
        time.sleep(1)

    logger.info(f"Manager: Downstream client {client_address} disconnected or manager shutting down.")
    with downstream_clients_lock:
        if client_address in connected_downstream_clients:
            del connected_downstream_clients[client_address]
            logger.info(f"Manager: Removed client {client_address}. Active clients: {len(connected_downstream_clients)}")
    client_wrapper.close()


def accept_downstream_clients():
    """
    Listens for and accepts connections from downstream clients.
    """
    global downstream_listener_socket
    downstream_listener_socket = SocketWrapper(name=f"Manager@{MANAGER_LISTEN_HOST}:{MANAGER_LISTEN_PORT}-Listener")
    if not downstream_listener_socket.bind(MANAGER_LISTEN_HOST, MANAGER_LISTEN_PORT):
        logger.error(f"Manager: Failed to bind downstream listener to {MANAGER_LISTEN_HOST}:{MANAGER_LISTEN_PORT}. Exiting accept thread.")
        return

    downstream_listener_socket.listen(MAX_DOWNSTREAM_CLIENTS)
    logger.info(f"Manager: Listening for downstream clients on {MANAGER_LISTEN_HOST}:{MANAGER_LISTEN_PORT}")

    # threads = [] # To keep track of client handler threads

    while not exit_event.is_set():
        downstream_listener_socket.socket.settimeout(1.0) # Timeout to check exit_event
        try:
            client_wrapper, client_address = downstream_listener_socket.accept()
        except socket.timeout:
            continue
        except Exception as e:
            if exit_event.is_set(): break
            logger.error(f"Manager: Error accepting downstream client: {e}")
            continue


        if client_wrapper and client_address:
            logger.info(f"Manager: Downstream client connected from {client_address}")
            with downstream_clients_lock:
                if len(connected_downstream_clients) >= MAX_DOWNSTREAM_CLIENTS:
                    logger.warning(f"Manager: Max downstream clients ({MAX_DOWNSTREAM_CLIENTS}) reached. Rejecting {client_address}")
                    client_wrapper.send_to({"type": "error", "payload": "Manager busy, max clients reached."})
                    client_wrapper.close()
                    continue
                connected_downstream_clients[client_address] = client_wrapper

            # Register the callback for this specific client_wrapper.
            # The callback needs access to the client_wrapper instance to know who sent the message.
            # We can use a lambda to capture the client_wrapper instance.
            client_wrapper.register_callback(
                lambda msg, cw=client_wrapper: handle_downstream_client_message(msg, cw)
            )
            # The client_wrapper's receiver loop is started by its __init__ (when socket is passed)
            # or by its connect method. For accepted sockets, it's in __init__.

            # Optional: Start a dedicated thread for managing this client if more complex logic is needed
            # than what the wrapper provides. For now, the wrapper's receiver thread is sufficient.
            # thread = threading.Thread(target=downstream_client_connection_thread, args=(client_wrapper, client_address), daemon=True)
            # thread.start()
            # threads.append(thread)
        elif exit_event.is_set():
            logger.info("Manager shutting down, downstream accept loop terminating.")
            break

    logger.info("Manager: Downstream client acceptance thread terminated.")
    # for t in threads:
    #     t.join(timeout=1)


def start_manager_server():
    logger.info(f"Starting Manager Server (listening on {MANAGER_LISTEN_HOST}:{MANAGER_LISTEN_PORT})...")

    # Thread to connect to the main server
    upstream_conn_thread = threading.Thread(target=connect_to_main_server_thread, daemon=True)
    upstream_conn_thread.start()

    # Thread to relay messages from queue to main server
    relay_thread = threading.Thread(target=message_relay_thread, daemon=True)
    relay_thread.start()

    # Thread to retry sending messages that timed out waiting for main server response
    retry_thread = threading.Thread(target=retry_pending_messages_thread, daemon=True)
    retry_thread.start()

    # Thread to accept downstream client connections (this will be the main execution of this function for a while)
    accept_clients_thread = threading.Thread(target=accept_downstream_clients, daemon=True)
    accept_clients_thread.start()

    try:
        while not exit_event.is_set():
            # Keep main thread alive, or do other manager-level tasks
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Manager Server shutting down (KeyboardInterrupt)...")
    finally:
        logger.info("Manager Server initiating cleanup...")
        exit_event.set() # Signal all threads to terminate

        if upstream_wrapper:
            upstream_wrapper.close()
        upstream_conn_thread.join(timeout=2)

        # Signal relay and retry threads by clearing queue or other means if needed,
        # but exit_event should be primary.
        message_relay_queue.put(None) # Sentinel to potentially unblock relay_thread if stuck on queue.get()
        relay_thread.join(timeout=2)
        retry_thread.join(timeout=2)


        if downstream_listener_socket:
            downstream_listener_socket.close()

        with downstream_clients_lock:
            for address, wrapper in list(connected_downstream_clients.items()):
                logger.info(f"Manager: Closing connection to downstream client {address}")
                wrapper.close()
            connected_downstream_clients.clear()

        accept_clients_thread.join(timeout=2)

        logger.info("Manager Server has shut down.")


if __name__ == "__main__":
    # Check if a specific port is provided as argument, otherwise use default
    import sys
    if len(sys.argv) > 1:
        try:
            MANAGER_LISTEN_PORT = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid port number provided: {sys.argv[1]}. Using default {MANAGER_LISTEN_PORT}.")

    start_manager_server()
