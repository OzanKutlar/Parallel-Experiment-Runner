import threading
import time
import uuid
import logging
from typing import Dict, Any, Optional, Tuple

from socket_wrapper import SocketWrapper, logger as wrapper_logger

# Configure client logging
logger = logging.getLogger('client')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# wrapper_logger.addHandler(handler)
# wrapper_logger.setLevel(logging.INFO)


MANAGER_SERVER_HOST = 'localhost'
# Default manager port, can be changed via command line argument
MANAGER_SERVER_PORT = 3754

client_socket_wrapper: Optional[SocketWrapper] = None
exit_event = threading.Event()

# For tracking messages sent and awaiting responses
# message_id -> (original_message_dict, timestamp, retries)
pending_server_responses: Dict[str, Tuple[Dict[str, Any], float, int]] = {}
pending_responses_lock = threading.Lock()
RESPONSE_TIMEOUT = 10  # seconds to wait for a response
MAX_SEND_RETRIES = 3   # max retries for a single message

def handle_server_response(message: Dict[str, Any]) -> None:
    """
    Callback for messages received from the manager server.
    This function is executed by the client_socket_wrapper's receiver thread.
    """
    message_id = message.get('message_id')
    logger.info(f"Client received (msg_id: {message_id}): {message.get('type')} - {message.get('payload', message.get('error'))}")

    if message_id:
        with pending_responses_lock:
            if message_id in pending_server_responses:
                pending_server_responses.pop(message_id)
                logger.debug(f"Response for message {message_id} received and processed.")
            else:
                logger.debug(f"Received response for {message_id}, but it was not in pending list (possibly already processed or unexpected).")
    else:
        logger.warning("Client received a message from server without a message_id.")

    # This callback processes a response, doesn't generate a new one for the server.
    return None


def send_message_with_retry(message_payload: Dict[str, Any], message_type: str = "data_request") -> Optional[str]:
    """
    Sends a message and stores it for potential retry if no response is received.
    Returns the message_id if successfully initiated, None otherwise.
    """
    if not client_socket_wrapper or not client_socket_wrapper.is_connected():
        logger.error("Cannot send message: Client not connected to manager server.")
        return None

    msg_id = str(uuid.uuid4())
    message_to_send = {
        "type": message_type,
        "payload": message_payload,
        # message_id will be added by send_to or we can add it here
    }

    with pending_responses_lock:
        pending_server_responses[msg_id] = (message_to_send, time.time(), 0)

    logger.info(f"Client sending (msg_id: {msg_id}): {message_type} - {message_payload}")
    actual_sent_id = client_socket_wrapper.send_to(message_to_send, message_id=msg_id)

    if not actual_sent_id: # Send failed immediately
        logger.error(f"Initial send attempt failed for message {msg_id}.")
        with pending_responses_lock:
            pending_server_responses.pop(msg_id, None) # Remove if send failed
        return None

    if actual_sent_id != msg_id: # Should not happen if we provide msg_id
        logger.warning(f"Sent ID {actual_sent_id} differs from generated ID {msg_id}")
        # Adjust tracking if necessary, though wrapper should use provided ID
        with pending_responses_lock:
            if msg_id in pending_server_responses:
                data = pending_server_responses.pop(msg_id)
                pending_server_responses[actual_sent_id] = data


    return actual_sent_id # or msg_id, should be the same

def retry_timed_out_messages_thread():
    """
    Periodically checks for messages that haven't received a response and retries them.
    """
    logger.info("Client retry thread started.")
    while not exit_event.is_set():
        time.sleep(RESPONSE_TIMEOUT / 2) # Check periodically

        if not client_socket_wrapper or not client_socket_wrapper.is_connected():
            continue

        messages_to_retry_now = []
        with pending_responses_lock:
            current_time = time.time()
            for msg_id, (original_msg, ts, retries) in list(pending_server_responses.items()):
                if current_time - ts > RESPONSE_TIMEOUT:
                    if retries < MAX_SEND_RETRIES:
                        logger.warning(f"Client: Message {msg_id} timed out. Retrying (attempt {retries + 1}).")
                        messages_to_retry_now.append((msg_id, original_msg, retries + 1))
                    else:
                        logger.error(f"Client: Message {msg_id} exceeded max retries. Giving up.")
                        pending_server_responses.pop(msg_id, None) # Remove from pending

        for msg_id, original_msg, new_retry_count in messages_to_retry_now:
            logger.info(f"Client resending (msg_id: {msg_id}, attempt {new_retry_count}): {original_msg.get('type')} - {original_msg.get('payload')}")
            sent_id = client_socket_wrapper.send_to(original_msg, message_id=msg_id)
            with pending_responses_lock:
                if msg_id in pending_server_responses: # Check if still there (not responded in meantime)
                    if sent_id: # Resend successful
                        # Update timestamp and retry count
                        pending_server_responses[msg_id] = (original_msg, time.time(), new_retry_count)
                    else: # Resend failed
                        logger.error(f"Client: Failed to resend message {msg_id} on attempt {new_retry_count}.")
                        # It will be picked up again if connection recovers, or eventually max out retries.
                        # If connection is lost, is_connected() will become false.

    logger.info("Client retry thread terminated.")


def start_client():
    global client_socket_wrapper, MANAGER_SERVER_PORT

    import sys
    if len(sys.argv) > 1:
        try:
            MANAGER_SERVER_PORT = int(sys.argv[1])
            logger.info(f"Client will connect to manager on port: {MANAGER_SERVER_PORT}")
        except ValueError:
            logger.error(f"Invalid port number provided: {sys.argv[1]}. Using default {MANAGER_SERVER_PORT}.")

    client_socket_wrapper = SocketWrapper(name=f"ClientToMgr@{MANAGER_SERVER_HOST}:{MANAGER_SERVER_PORT}")
    client_socket_wrapper.register_callback(handle_server_response)

    # Start the retry thread
    retry_thread = threading.Thread(target=retry_timed_out_messages_thread, daemon=True)
    retry_thread.start()

    # Attempt to connect (SocketWrapper handles retries for connection establishment)
    # The connect method is blocking until successful or max attempts reached.
    if not client_socket_wrapper.connect(MANAGER_SERVER_HOST, MANAGER_SERVER_PORT, max_attempts=-1, retry_delay=5):
        logger.error("Client failed to connect to manager server after multiple attempts. Exiting.")
        exit_event.set() # Signal retry thread to stop
        retry_thread.join(timeout=2)
        return

    logger.info(f"Client connected to manager server at {MANAGER_SERVER_HOST}:{MANAGER_SERVER_PORT}")

    try:
        # Example: Send a few messages
        for i in range(5):
            if exit_event.is_set(): break
            payload_data = f"Hello from client, message {i+1}"
            send_message_with_retry({"data": payload_data, "count": i+1})
            time.sleep(2) # Stagger messages

        # Keep client running to receive responses or send more messages
        logger.info("Client finished sending initial messages. Will wait for responses or Ctrl+C to exit.")
        while not exit_event.is_set():
            if not client_socket_wrapper.is_connected():
                logger.warning("Client disconnected from manager. Attempting to reconnect...")
                # The wrapper's connect method can be called again if we want to manage reconnection here
                # Or rely on its internal retry if that's how it's designed for persistent connections.
                # For now, the initial connect has infinite retries. If it drops, we might need to re-initiate.
                # The current wrapper's connect is for initial connection. If it drops after connecting,
                # the _receiver_loop sets self.connected=False.
                # We'd need a loop here to re-call client_socket_wrapper.connect()
                logger.info("Client will attempt to reconnect via SocketWrapper's internal mechanism if configured, or exit.")
                # For this example, if connection drops, we'll just exit the send loop.
                # A more robust client would have a reconnection loop here.
                # The provided wrapper's connect() method does retry, so if it fails initially, it keeps trying.
                # If it disconnects *after* being connected, the current client script doesn't automatically re-run connect().
                # This could be an enhancement.
                # For now, if it disconnects, the retry thread stops sending and this loop might break or do nothing.
                if not client_socket_wrapper.connect(MANAGER_SERVER_HOST, MANAGER_SERVER_PORT, max_attempts=3, retry_delay=5): # Try a few more times
                     logger.error("Client could not re-establish connection. Exiting loop.")
                     break
                else:
                    logger.info("Client reconnected to manager.")


            time.sleep(1) # Main loop idle

    except KeyboardInterrupt:
        logger.info("Client shutting down (KeyboardInterrupt)...")
    finally:
        logger.info("Client initiating cleanup...")
        exit_event.set() # Signal retry thread to stop

        if client_socket_wrapper:
            client_socket_wrapper.close()

        retry_thread.join(timeout=3) # Wait for retry thread to finish
        logger.info("Client has shut down.")

if __name__ == "__main__":
    start_client()
