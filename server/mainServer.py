import threading
import time
import logging
from typing import Dict, Any, Optional
from socket_wrapper import SocketWrapper, logger as wrapper_logger

# Configure main server logging
logger = logging.getLogger('main_server')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Use the same logger for the wrapper for consistency if desired, or keep separate
# wrapper_logger.addHandler(handler)
# wrapper_logger.setLevel(logging.INFO)


SERVER_HOST = '0.0.0.0'
SERVER_PORT = 3753
MAX_MANAGERS = 10  # Example limit

# Store connected manager clients (SocketWrapper instances)
# Key: manager_address (ip, port), Value: SocketWrapper instance
connected_managers: Dict[tuple, SocketWrapper] = {}
managers_lock = threading.Lock()

def handle_manager_message(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Callback function to process messages received from a manager.
    This function is executed by the SocketWrapper's receiver thread for a specific manager.
    It should return a dictionary if a response needs to be sent back, or None otherwise.
    """
    message_id = message.get('message_id', 'N/A')
    client_original_id = message.get('client_original_id', 'N/A') # ID from the end-client
    logger.info(f"MainServer received from manager (msg_id: {message_id}, client_orig_id: {client_original_id}): {message.get('type', 'Unknown type')} - {message.get('payload')}")

    # Example processing: Echo back or perform some action
    response_payload = f"MainServer processed your data: {message.get('payload')}"

    # The response will be sent by the SocketWrapper using the original message_id
    # It's important that the response also includes client_original_id if the manager needs it
    # for routing back to the specific end-client.
    response = {
        "type": "main_server_response",
        "payload": response_payload,
        "status": "success",
        "client_original_id": client_original_id # Forward back the original client ID
    }
    # The message_id of the incoming message will be automatically used for the response by the wrapper.
    return response

def manager_connection_thread(manager_wrapper: SocketWrapper, manager_address: tuple):
    """
    Dedicated thread to handle a single manager connection.
    The SocketWrapper's internal _receiver_loop will handle message processing.
    This thread primarily exists to monitor the connection status and clean up.
    """
    logger.info(f"Thread started for manager {manager_address}")
    manager_wrapper.register_callback(handle_manager_message) # All messages from this manager go here

    # The _receiver_loop is started by SocketWrapper on accept or connect.
    # We just need to keep this thread alive as long as the wrapper is connected,
    # or perform periodic checks/actions if needed.
    while manager_wrapper.is_connected() and not exit_event.is_set():
        time.sleep(1) # Keep alive, check connection status

    logger.info(f"Manager {manager_address} disconnected or server shutting down.")
    with managers_lock:
        if manager_address in connected_managers:
            del connected_managers[manager_address]
            logger.info(f"Removed manager {manager_address} from active list. Total managers: {len(connected_managers)}")
    manager_wrapper.close()


exit_event = threading.Event()

def start_main_server():
    """
    Starts the main server to listen for manager connections.
    """
    server_socket = SocketWrapper(name="MainServerListener")
    if not server_socket.bind(SERVER_HOST, SERVER_PORT):
        logger.error(f"Failed to bind main server to {SERVER_HOST}:{SERVER_PORT}. Exiting.")
        return

    server_socket.listen(MAX_MANAGERS)
    logger.info(f"Main Server listening on {SERVER_HOST}:{SERVER_PORT}")

    threads = []

    try:
        while not exit_event.is_set():
            logger.info(f"Main Server waiting for a manager connection... Active managers: {len(connected_managers)}")
            # Set a timeout for accept to allow periodic check of exit_event
            server_socket.socket.settimeout(1.0)
            try:
                manager_wrapper, manager_address = server_socket.accept()
            except socket.timeout:
                continue # Timeout allows checking exit_event
            except Exception as e:
                if exit_event.is_set(): break
                logger.error(f"Error during accept: {e}")
                continue


            if manager_wrapper and manager_address:
                logger.info(f"Manager connected from {manager_address}")
                with managers_lock:
                    if len(connected_managers) >= MAX_MANAGERS:
                        logger.warning(f"Max manager limit ({MAX_MANAGERS}) reached. Rejecting {manager_address}")
                        manager_wrapper.send_to({"type": "error", "payload": "Server busy, max managers reached."})
                        manager_wrapper.close()
                        continue
                    connected_managers[manager_address] = manager_wrapper

                # The SocketWrapper for the accepted connection (manager_wrapper)
                # will start its own receiver loop. We just need to manage it.
                # No need to pass manager_wrapper to the thread, it's already started.
                # The thread is for managing its lifecycle or custom logic if any.
                # For now, the wrapper handles its own receiving thread.
                # We can simplify by not needing a dedicated thread per manager here if wrapper handles all.
                # However, if we want to monitor or manage it actively, a thread is useful.

                # The manager_wrapper's receiver loop is already started by its __init__ when a socket is passed.
                # We just need to register the callback.
                manager_wrapper.register_callback(handle_manager_message)

                # Optional: A thread to monitor this specific manager if needed beyond wrapper's scope
                # thread = threading.Thread(target=manager_connection_thread, args=(manager_wrapper, manager_address), daemon=True)
                # thread.start()
                # threads.append(thread)

            elif exit_event.is_set():
                logger.info("Main server shutting down, accept loop terminating.")
                break

    except KeyboardInterrupt:
        logger.info("Main Server shutting down (KeyboardInterrupt)...")
    except Exception as e:
        logger.error(f"Main Server encountered an error: {e}", exc_info=True)
    finally:
        logger.info("Main Server initiating cleanup...")
        exit_event.set() # Signal all components to shut down

        with managers_lock:
            for address, wrapper in list(connected_managers.items()): # Iterate over a copy
                logger.info(f"Closing connection to manager {address}")
                wrapper.close()
            connected_managers.clear()

        server_socket.close() # Close the listening socket

        # for t in threads: # If using dedicated threads per manager
        #     t.join(timeout=2)
        logger.info("Main Server has shut down.")

if __name__ == "__main__":
    start_main_server()
