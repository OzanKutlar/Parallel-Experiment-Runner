import socket
import json
import uuid
import threading
import time
import logging
from typing import Dict, Any, Callable, Optional, Tuple, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('socket_wrapper')

class SocketWrapper:
    """
    A wrapper for socket communications using JSON, with message caching and retry mechanism.
    """

    def __init__(self, sock: Optional[socket.socket] = None, name: str = "Wrapper"):
        """Initialize the socket wrapper with an optional existing socket."""
        self.socket = sock if sock else socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if not sock: # Only set options if we created the socket
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.name = name # For logging purposes
        self.logger = logging.getLogger(f'socket_wrapper.{self.name}')

        # Use larger buffer size to handle messages of any size
        self.buffer_size = 4096 # This is for socket.recv chunk, not total message size

        # Message handling
        self.message_cache: Dict[str, Dict[str, Any]] = {} # Stores received messages to detect duplicates
        self.response_cache: Dict[str, Dict[str, Any]] = {} # Stores responses to re-send for duplicate messages
        self.message_callbacks: Dict[str, Callable] = {} # For type-specific message handlers
        self.default_callback: Optional[Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]] = None # Default handler

        # Ensure thread safety for cache operations
        self.cache_lock = threading.Lock()

        # For connection management
        self.connected = False
        if sock: # If socket is passed, assume it's connected (server accepted connection)
            self.connected = True

        self.shutdown_flag = threading.Event() # Use Event for clearer shutdown signaling
        self.receiver_thread = None
        self.address = None # Store address for server-side accepted sockets

        if self.connected and sock: # If it's an accepted socket, start receiver loop
            self.address = sock.getpeername()
            self._start_receiver_loop()


    def _start_receiver_loop(self):
        """Starts the receiver loop in a new thread."""
        if self.receiver_thread is None or not self.receiver_thread.is_alive():
            self.shutdown_flag.clear()
            self.receiver_thread = threading.Thread(target=self._receiver_loop, daemon=True)
            self.receiver_thread.start()
            self.logger.info(f"Receiver loop started for {self.address or 'client connection'}")

    def connect(self, host: str, port: int, max_attempts: int = -1, retry_delay: int = 5) -> bool:
        """
        Connect to a server with automatic retry.

        Args:
            host: Server hostname or IP address
            port: Server port
            max_attempts: Maximum connection attempts (-1 for infinite)
            retry_delay: Seconds to wait between attempts

        Returns:
            True if connection successful, False otherwise
        """
        attempts = 0
        self.address = (host, port) # Store target address

        while not self.shutdown_flag.is_set() and (max_attempts == -1 or attempts < max_attempts):
            attempts += 1
            try:
                self.logger.info(f"Connecting to {host}:{port}, attempt {attempts}")
                # Recreate socket for each attempt to ensure clean state
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.socket.connect((host, port))
                self.connected = True

                self._start_receiver_loop() # Start receiver loop upon successful connection

                self.logger.info(f"Successfully connected to {host}:{port}")
                return True

            except ConnectionRefusedError:
                self.logger.warning(f"Connection refused at {host}:{port}")
            except socket.timeout:
                self.logger.warning(f"Connection timed out at {host}:{port}")
            except Exception as e:
                self.logger.error(f"Connection error to {host}:{port}: {str(e)}")

            if self.shutdown_flag.is_set():
                self.logger.info("Shutdown initiated, abandoning connection attempts.")
                break

            if max_attempts == -1 or attempts < max_attempts:
                self.logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

        self.logger.error(f"Failed to connect to {host}:{port} after {attempts} attempts")
        return False

    def bind(self, host: str, port: int) -> bool:
        """
        Bind the socket to a specific address and port.
        """
        try:
            self.socket.bind((host, port))
            self.address = (host, port)
            self.logger.info(f"Socket bound to {host}:{port}")
            return True
        except Exception as e:
            self.logger.error(f"Binding error at {host}:{port}: {str(e)}")
            return False

    def listen(self, backlog: int = 5) -> None:
        """
        Start listening for incoming connections.
        """
        self.socket.listen(backlog)
        self.logger.info(f"Listening on {self.address} with backlog {backlog}")

    def accept(self) -> Tuple[Optional['SocketWrapper'], Optional[Tuple[str, int]]]:
        """
        Accept a new connection.

        Returns:
            A tuple of (SocketWrapper, client_address) or (None, None) if error or shutdown
        """
        try:
            if self.shutdown_flag.is_set():
                self.logger.info("Accept called during shutdown, returning None.")
                return None, None
            client_socket, client_address = self.socket.accept()
            self.logger.info(f"Accepted connection from {client_address}")
            # Pass a unique name for the logger of the new wrapper
            wrapper_name = f"{self.name}-Client[{client_address[0]}:{client_address[1]}]"
            new_wrapper = SocketWrapper(client_socket, name=wrapper_name)
            return new_wrapper, client_address
        except socket.timeout: # If socket is non-blocking
            return None, None
        except OSError as e: # Handle cases like socket closed during accept
             if not self.shutdown_flag.is_set(): # Avoid logging error if it's a planned shutdown
                self.logger.error(f"Accept error: {str(e)}")
             return None, None
        except Exception as e:
            if not self.shutdown_flag.is_set():
                self.logger.error(f"Unexpected accept error: {str(e)}")
            return None, None

    def send_to(self, obj: Dict[str, Any], message_id: Optional[str] = None) -> Optional[str]:
        """
        Send a JSON object to the connected socket.

        Args:
            obj: The Python dictionary to send as JSON
            message_id: Optional message ID (will be generated if not provided)

        Returns:
            The message ID used, or None if send failed
        """
        if self.shutdown_flag.is_set() or not self.connected:
            self.logger.error(f"Cannot send: Not connected or shutting down. Target: {self.address}")
            return None

        current_message_id = message_id if message_id else str(uuid.uuid4())

        # Ensure 'message_id' is in the top-level object
        message_to_send = obj.copy() # Avoid modifying the original object
        message_to_send['message_id'] = current_message_id

        try:
            message_json = json.dumps(message_to_send)
            message_bytes = message_json.encode('utf-8')
            message_length = len(message_bytes)
            length_prefix = message_length.to_bytes(4, byteorder='big')

            self.socket.sendall(length_prefix + message_bytes)
            # self.logger.debug(f"Sent message {current_message_id} to {self.address}: {message_to_send}")
            return current_message_id

        except (ConnectionResetError, BrokenPipeError) as e:
            self.logger.error(f"Send error (connection issue) to {self.address} for msg {current_message_id}: {str(e)}")
            self.connected = False # Mark as disconnected
            self._handle_disconnect()
            return None
        except Exception as e:
            self.logger.error(f"Send error to {self.address} for msg {current_message_id}: {str(e)}")
            # For other errors, it's not always a disconnect, but could be.
            # Consider if self.connected should be set to False here too.
            return None

    def register_callback(self, callback: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]], message_type: Optional[str] = None) -> None:
        """
        Register a callback function for a specific message type or as default.
        The callback should take the received message dict and return a response dict or None.
        """
        if message_type:
            self.message_callbacks[message_type] = callback
            self.logger.info(f"Registered callback for message type '{message_type}'")
        else:
            self.default_callback = callback
            self.logger.info("Registered default callback")

    def _receiver_loop(self) -> None:
        """Background thread that receives and processes incoming messages."""
        self.logger.info(f"Receiver loop starting for {self.address or 'connection'}")
        while not self.shutdown_flag.is_set() and self.connected:
            try:
                length_bytes = self._recv_all(4)
                if not length_bytes:
                    if not self.shutdown_flag.is_set(): # Log only if not intentional shutdown
                        self.logger.info(f"Connection closed by remote host {self.address} (length_bytes empty)")
                    break

                message_length = int.from_bytes(length_bytes, byteorder='big')
                if message_length == 0: # Could be a keep-alive or an error
                    self.logger.debug(f"Received 0-length message from {self.address}")
                    continue


                message_bytes = self._recv_all(message_length)
                if not message_bytes:
                    if not self.shutdown_flag.is_set():
                        self.logger.info(f"Connection closed by remote host {self.address} (message_bytes empty)")
                    break

                message_json = message_bytes.decode('utf-8')
                message_obj = json.loads(message_json)
                # self.logger.debug(f"Received message from {self.address}: {message_obj}")

                self._process_message(message_obj)

            except (ConnectionResetError, ConnectionAbortedError) as e:
                if not self.shutdown_flag.is_set():
                    self.logger.warning(f"Connection issue with {self.address}: {str(e)}")
                break
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to decode JSON message from {self.address}: {str(e)}. Message bytes: {message_bytes[:100]}") # Log part of message
                continue # Try to recover and read next message
            except socket.timeout: # If socket has a timeout
                if not self.shutdown_flag.is_set():
                     self.logger.debug(f"Socket timeout in receiver loop for {self.address}. Continuing.")
                continue
            except OSError as e: # Catching socket errors more broadly (e.g. socket closed)
                if not self.shutdown_flag.is_set():
                    self.logger.error(f"Socket OS error in receiver loop for {self.address}: {e}")
                break
            except Exception as e:
                if not self.shutdown_flag.is_set(): # Avoid error logging during controlled shutdown
                    self.logger.error(f"Unexpected receiver error for {self.address}: {str(e)}", exc_info=True)
                break # Exit loop on unexpected errors

        self.connected = False
        self._handle_disconnect()
        self.logger.info(f"Receiver loop terminated for {self.address or 'connection'}")

    def _recv_all(self, n: int) -> bytes:
        """
        Receive exactly n bytes from the socket.
        Returns empty bytes if connection is closed or error occurs.
        """
        data = b''
        while len(data) < n:
            if self.shutdown_flag.is_set(): return b'' # Stop if shutting down
            try:
                # self.socket.settimeout(1.0) # Short timeout to allow checking shutdown_flag
                packet = self.socket.recv(n - len(data))
            except socket.timeout:
                continue # Loop again to check shutdown_flag
            except OSError: # Socket closed or other error
                return b''
            if not packet:
                return b''  # Connection closed
            data += packet
        return data

    def _process_message(self, message: Dict[str, Any]) -> None:
        """
        Process a received message based on its message_id and type.
        Calls the appropriate handler and sends back the response if one is returned by the handler.
        """
        message_id = message.get('message_id')
        if not message_id:
            self.logger.warning(f"Received message from {self.address} without message_id: {message}")
            # Optionally, call default handler even without message_id if desired
            if self.default_callback:
                try:
                    self.default_callback(message) # No response expected or can be sent without message_id
                except Exception as e:
                    self.logger.error(f"Error in default_callback for message without ID from {self.address}: {e}")
            return

        with self.cache_lock:
            if message_id in self.message_cache and self.message_cache[message_id] == message:
                # This is a resent message for which we might have already responded.
                if message_id in self.response_cache:
                    cached_response = self.response_cache[message_id]
                    self.logger.info(f"Re-sending cached response for duplicate message {message_id} from {self.address}")
                    self.send_to(cached_response, message_id) # Use original message_id for the response
                    return
                else:
                    # We saw this message, but don't have a response cached (maybe handler didn't provide one, or it's still processing)
                    self.logger.info(f"Received duplicate message {message_id} from {self.address}, but no response cached. Reprocessing.")
            else:
                # New message or different content for same ID (should not happen with UUIDs)
                self.message_cache[message_id] = message


        message_type = message.get('type')
        handler = self.message_callbacks.get(message_type, self.default_callback)

        if handler:
            try:
                response_obj = handler(message) # Handler should return a dict or None

                if response_obj and isinstance(response_obj, dict):
                    # Ensure the response also has the original message_id for correlation
                    response_obj['message_id'] = message_id

                    with self.cache_lock:
                        self.response_cache[message_id] = response_obj # Cache the response

                    self.logger.info(f"Sending response for message {message_id} from {self.address}")
                    self.send_to(response_obj, message_id) # Send response, using original msg_id
                # If handler returns None, no direct response is sent by this wrapper for this message
            except Exception as e:
                self.logger.error(f"Error in message handler for type '{message_type}', msg_id {message_id} from {self.address}: {str(e)}", exc_info=True)
                # Optionally send an error response back
                error_response = {
                    'type': 'error_response',
                    'message_id': message_id,
                    'error': str(e),
                    'status': 'handler_exception'
                }
                with self.cache_lock: # Cache the error response too
                    self.response_cache[message_id] = error_response
                self.send_to(error_response, message_id)
        else:
            self.logger.warning(f"No handler found for message type '{message_type}' or default from {self.address}, msg_id {message_id}. Message: {message}")


    def _handle_disconnect(self):
        """Called when a disconnect is detected."""
        self.connected = False
        # Potentially add custom logic here, e.g., notifying other parts of the application.
        self.logger.info(f"Disconnected from {self.address or 'peer'}.")
        # If this wrapper was for a client trying to connect, the connect() loop will handle retries.
        # If this was a server-accepted connection, the server's main loop might remove this client.


    def close(self) -> None:
        """Close the socket connection and clean up."""
        self.logger.info(f"Closing socket for {self.address or self.name}")
        self.shutdown_flag.set() # Signal all loops to stop

        if hasattr(self, 'socket'):
            try:
                # Shutdown socket to unblock recv/accept before closing
                self.socket.shutdown(socket.SHUT_RDWR)
            except (OSError, socket.error) as e:
                # Ignore errors if socket is already closed or not connected
                pass # self.logger.debug(f"Error during socket shutdown for {self.address}: {e}")
            finally:
                try:
                    self.socket.close()
                except (OSError, socket.error) as e:
                    pass # self.logger.debug(f"Error during socket close for {self.address}: {e}")

        if self.receiver_thread and self.receiver_thread.is_alive():
            self.receiver_thread.join(timeout=2.0) # Wait for receiver thread to exit
            if self.receiver_thread.is_alive():
                 self.logger.warning(f"Receiver thread for {self.address} did not terminate cleanly.")

        self.connected = False
        self.logger.info(f"Socket closed for {self.address or self.name}")

    def is_connected(self) -> bool:
        """Check if the socket is currently considered connected."""
        # A more robust check might involve a periodic PING/PONG if just self.connected isn't enough
        return self.connected
