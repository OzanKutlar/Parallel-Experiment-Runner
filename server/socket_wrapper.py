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
    Handles message framing (length prefix) to support arbitrary message sizes.
    """

    def __init__(self, sock: Optional[socket.socket] = None, start_receiver_on_init: bool = False):
        """
        Initialize the socket wrapper.

        Args:
            sock: An optional existing socket. If provided, the wrapper uses this socket.
                  Typically used server-side after accepting a connection.
            start_receiver_on_init: If True and a socket 'sock' is provided,
                                    start the receiver loop immediately.
                                    Useful for server-side client handlers.
        """
        if sock:
            self.socket = sock
            self.connected = True # Assume connected if socket is passed
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connected = False
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Message handling
        self.message_cache: Dict[str, Dict[str, Any]] = {} # Stores sent messages
        self.response_cache: Dict[str, Dict[str, Any]] = {} # Stores responses generated for received messages
        self.message_callbacks: Dict[str, Callable] = {} # Handlers for specific message types
        self.default_callback: Optional[Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]] = None # Default handler

        # Ensure thread safety for cache operations
        self.cache_lock = threading.Lock()

        # For connection management
        self.shutdown_flag = False
        self.receiver_thread: Optional[threading.Thread] = None

        if self.connected and start_receiver_on_init:
            self.start_receiver()

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
        if self.connected:
            logger.warning("Already connected.")
            return True

        attempts = 0
        current_delay = retry_delay

        while not self.shutdown_flag and (max_attempts == -1 or attempts < max_attempts):
            attempts += 1
            try:
                # Create a new socket for each attempt if the previous failed
                if not self.connected: # Only create new socket if not already connected
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                logger.info(f"Connecting to {host}:{port}, attempt {attempts}")
                self.socket.connect((host, port))
                self.connected = True
                self.shutdown_flag = False # Reset flag on successful connection

                # Start the receiver thread
                self.start_receiver()

                logger.info(f"Successfully connected to {host}:{port}")
                return True

            except ConnectionRefusedError:
                logger.warning(f"Connection refused by {host}:{port}")
            except socket.timeout:
                 logger.warning(f"Connection attempt to {host}:{port} timed out")
            except OSError as e: # Handle cases like "Network is unreachable"
                 logger.error(f"OS error during connection attempt {attempts}: {e}")
            except Exception as e:
                logger.error(f"Connection error on attempt {attempts}: {str(e)}")
                # Close the failed socket before retrying
                if self.socket:
                    try:
                        self.socket.close()
                    except Exception:
                        pass
                self.connected = False # Ensure state is disconnected

            if max_attempts == -1 or attempts < max_attempts:
                logger.info(f"Retrying connection in {current_delay} seconds...")
                time.sleep(current_delay)
                # Exponential backoff (optional, but good practice)
                current_delay = min(current_delay * 2, 60) # Double delay up to 60 seconds
            else:
                 logger.error(f"Failed to connect to {host}:{port} after {attempts} attempts")

        return False

    def bind(self, host: str, port: int) -> bool:
        """
        Bind the socket to a specific address and port.

        Args:
            host: Hostname or IP address to bind to
            port: Port to bind to

        Returns:
            True if binding successful, False otherwise
        """
        if self.connected:
             logger.warning("Cannot bind, already connected.")
             return False
        try:
            self.socket.bind((host, port))
            logger.info(f"Socket bound to {host}:{port}")
            return True
        except Exception as e:
            logger.error(f"Binding error: {str(e)}")
            return False

    def listen(self, backlog: int = 5) -> None:
        """
        Start listening for incoming connections.

        Args:
            backlog: Maximum number of queued connections
        """
        try:
            self.socket.listen(backlog)
            logger.info(f"Server listening with backlog {backlog}")
        except Exception as e:
            logger.error(f"Listen error: {str(e)}")


    def accept(self) -> Tuple[Optional['SocketWrapper'], Optional[Tuple[str, int]]]:
        """
        Accept a new connection.

        Returns:
            A tuple of (SocketWrapper, client_address) or (None, None) if error.
            The returned SocketWrapper is ready to communicate with the client,
            but its receiver loop needs to be started explicitly using start_receiver().
        """
        try:
            client_socket, client_address = self.socket.accept()
            logger.info(f"Accepted connection from {client_address}")
            # Pass start_receiver_on_init=True if you want the receiver to start immediately
            # Otherwise, call start_receiver() manually later.
            # Let's default to manual start for flexibility in server design.
            return SocketWrapper(client_socket, start_receiver_on_init=False), client_address
        except OSError as e:
             # Handle potential errors if the listening socket is closed prematurely
             logger.error(f"Accept error (OSError): {str(e)}")
             return None, None
        except Exception as e:
            logger.error(f"Accept error: {str(e)}")
            return None, None

    def send_to(self, obj: Dict[str, Any], message_id: Optional[str] = None) -> Optional[str]:
        """
        Send a JSON object to the connected socket.

        Args:
            obj: The Python dictionary to send as JSON
            message_id: Optional message ID (will be generated if not provided).
                        If provided, allows for resending the same logical message.

        Returns:
            The message ID used, or None if sending failed.
        """
        if not self.connected or self.shutdown_flag:
            logger.error("Cannot send: not connected or shutting down")
            return None

        # Generate message ID if not provided
        msg_id = message_id if message_id else str(uuid.uuid4())

        # Add the message_id to the object
        message_payload = obj.copy() # Avoid modifying the original object
        message_payload['message_id'] = msg_id

        try:
            # Convert to JSON and encode
            message_json = json.dumps(message_payload)
            message_bytes = message_json.encode('utf-8')

            # Prefix the message with its length as a 4-byte integer (big-endian)
            message_length = len(message_bytes)
            length_prefix = message_length.to_bytes(4, byteorder='big')

            # Send the length prefix followed by the message
            self.socket.sendall(length_prefix + message_bytes)
            # logger.debug(f"Sent message (ID: {msg_id}): {message_json[:100]}...") # Log truncated message

            # Cache the sent message (optional, primarily for debugging or potential future retry logic)
            # with self.cache_lock:
            #     self.message_cache[msg_id] = message_payload

            return msg_id

        except (BrokenPipeError, ConnectionResetError) as e:
             logger.error(f"Send error (connection closed): {str(e)}")
             self.close() # Close the connection properly on send failure
             return None
        except Exception as e:
            logger.error(f"Send error: {str(e)}")
            self.close() # Assume connection is broken
            return None

    def register_callback(self, callback: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]], message_type: Optional[str] = None) -> None:
        """
        Register a callback function for a specific message type or as default.
        The callback should accept the received message dictionary and
        optionally return a response dictionary.

        Args:
            callback: Function to call when message is received.
                      Signature: `callback(message: Dict[str, Any]) -> Optional[Dict[str, Any]]`
            message_type: Message type (value of 'type' key) to trigger this callback,
                          or None to register as the default callback.
        """
        if message_type:
            self.message_callbacks[message_type] = callback
            logger.info(f"Registered callback for message type '{message_type}'")
        else:
            self.default_callback = callback
            logger.info("Registered default message callback")

    def start_receiver(self) -> None:
        """
        Starts the background thread that receives and processes incoming messages.
        Should be called after establishing a connection (client-side) or
        after creating a wrapper for an accepted connection (server-side).
        """
        if self.receiver_thread and self.receiver_thread.is_alive():
            logger.warning("Receiver thread already running.")
            return

        if not self.connected:
            logger.error("Cannot start receiver: not connected.")
            return

        self.shutdown_flag = False # Ensure flag is reset
        self.receiver_thread = threading.Thread(target=self._receiver_loop, daemon=True)
        self.receiver_thread.start()
        logger.info("Receiver thread started.")

    def _receiver_loop(self) -> None:
        """Background thread that receives and processes incoming messages."""
        buffer = b""
        expected_length = None

        while not self.shutdown_flag:
            try:
                # Read data from the socket
                # Use a reasonable chunk size, not the full buffer_size at once
                # unless necessary. This can improve responsiveness.
                chunk = self.socket.recv(4096)
                if not chunk:
                    # Connection closed gracefully by the remote host
                    logger.info("Connection closed by remote host.")
                    break
                buffer += chunk

                # Process messages from the buffer
                while True:
                    if expected_length is None:
                        # Need at least 4 bytes for the length prefix
                        if len(buffer) >= 4:
                            length_bytes = buffer[:4]
                            expected_length = int.from_bytes(length_bytes, byteorder='big')
                            buffer = buffer[4:] # Remove length prefix from buffer
                        else:
                            break # Need more data for length

                    # If we know the expected length, check if we have the full message
                    if expected_length is not None and len(buffer) >= expected_length:
                        message_bytes = buffer[:expected_length]
                        buffer = buffer[expected_length:] # Keep remaining buffer
                        expected_length = None # Reset for next message

                        # Decode and parse JSON
                        try:
                            message_json = message_bytes.decode('utf-8')
                            message_obj = json.loads(message_json)
                            # logger.debug(f"Received message: {message_json[:100]}...") # Log truncated
                            # Process the message
                            self._process_message(message_obj)
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode JSON message: {message_bytes.decode('utf-8', errors='ignore')}")
                        except UnicodeDecodeError:
                             logger.error("Failed to decode message bytes (not valid UTF-8)")
                        except Exception as e:
                             logger.error(f"Error processing message content: {e}")

                    else:
                        # Need more data for the current message
                        break

            except ConnectionResetError:
                logger.warning("Connection reset by peer.")
                break
            except socket.timeout:
                # This shouldn't happen with blocking sockets unless a timeout is set
                logger.warning("Socket operation timed out.")
                continue # Or break, depending on desired behavior
            except OSError as e:
                # Handle cases like socket being closed by another thread
                if not self.shutdown_flag:
                     logger.error(f"Receiver error (OSError): {str(e)}")
                break # Exit loop if socket is likely closed
            except Exception as e:
                 # Catch other potential errors
                 if not self.shutdown_flag:
                     logger.error(f"Unexpected receiver error: {str(e)}")
                 break # Exit loop on unexpected errors

        # Mark as disconnected and log termination
        self.connected = False
        if not self.shutdown_flag: # Log only if not a planned shutdown
             logger.info("Receiver loop terminated due to connection issue or error.")
        else:
             logger.info("Receiver loop terminated due to shutdown.")
        # Optionally, call a disconnect callback here
        # self.on_disconnect()


    def _recv_all(self, n: int) -> Optional[bytes]:
        """
        DEPRECATED (Logic moved into _receiver_loop with buffering)
        Receive exactly n bytes from the socket.

        Args:
            n: Number of bytes to receive

        Returns:
            The received bytes or None if connection closed or error.
        """
        # This logic is now integrated into the buffered reading in _receiver_loop
        # Kept here for reference but should not be called directly.
        data = b''
        try:
            while len(data) < n:
                packet = self.socket.recv(n - len(data))
                if not packet:
                    logger.warning(f"Connection closed while receiving {n} bytes (got {len(data)}).")
                    return None # Connection closed
                data += packet
            return data
        except (ConnectionResetError, BrokenPipeError) as e:
             logger.error(f"Socket error while receiving: {e}")
             self.close()
             return None
        except Exception as e:
             logger.error(f"Unexpected error in _recv_all: {e}")
             self.close()
             return None


    def _process_message(self, message: Dict[str, Any]) -> None:
        """
        Process a received message based on its message_id and type.
        Calls the appropriate registered callback and handles response caching/sending.

        Args:
            message: The received message object (dictionary).
        """
        message_id = message.get('message_id')
        if not message_id:
            logger.warning(f"Received message without message_id: {message}")
            return # Ignore messages without an ID

        # --- Response Cache Check ---
        # Check if we have already processed this message ID and have a response cached
        with self.cache_lock:
            if message_id in self.response_cache:
                cached_response = self.response_cache[message_id]
                logger.info(f"Duplicate message received (ID: {message_id}). Resending cached response.")
                # Resend the cached response. Use the *original* message_id for the response.
                # The 'response_to' field helps the other side match it.
                response_payload = cached_response.copy()
                response_payload['response_to'] = message_id # Link response to original msg
                self.send_to(response_payload) # Let send_to generate a new ID for the *response* message
                return # Stop further processing for this duplicate

        # --- New Message Handling ---
        message_type = message.get('type')
        handler: Optional[Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]] = None

        # Find the appropriate handler
        if message_type and message_type in self.message_callbacks:
            handler = self.message_callbacks[message_type]
        elif self.default_callback:
            handler = self.default_callback
        else:
            logger.warning(f"No handler found for message type '{message_type}' or default. Message ID: {message_id}")
            # Optionally send a generic "not supported" response
            # error_response = {'type': 'ERROR', 'code': 'NO_HANDLER', 'detail': f"No handler for type '{message_type}'"}
            # error_response['response_to'] = message_id
            # self.send_to(error_response)
            return

        # --- Execute Handler and Send Response ---
        try:
            # Call the handler with the message content
            response_content = handler(message) # Handler returns the *content* of the response

            # If the handler returns a response dictionary, process and send it
            if response_content is not None and isinstance(response_content, dict):
                # Add metadata to the response
                response_content['response_to'] = message_id # Link to the request ID

                # Cache the response *content* before sending
                with self.cache_lock:
                    # Store the response content associated with the *request's* message_id
                    self.response_cache[message_id] = response_content

                # Send the response (send_to will add a new unique message_id for the response itself)
                self.send_to(response_content)
                # logger.debug(f"Sent response for message ID {message_id}")

            # If handler returns None, it means no direct response is needed for this message
            # (e.g., it was just an ACK or an event notification)
            # else:
            #     logger.debug(f"Handler for message ID {message_id} returned None (no response sent).")


        except Exception as e:
            logger.exception(f"Error executing handler for message type '{message_type}' (ID: {message_id}): {str(e)}")
            # Optionally send an error response back to the client
            error_response = {'type': 'ERROR', 'code': 'HANDLER_EXCEPTION', 'detail': str(e)}
            error_response['response_to'] = message_id
            self.send_to(error_response)


    def close(self) -> None:
        """Close the socket connection and clean up."""
        if self.shutdown_flag:
            return # Already closing

        logger.info("Closing socket connection...")
        self.shutdown_flag = True
        self.connected = False

        # Close the socket
        if hasattr(self, 'socket'):
            try:
                # Shut down communication first
                self.socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                 # Ignore errors if the socket is already closed or not connected
                 pass
            except Exception as e:
                 logger.warning(f"Error during socket shutdown: {e}")

            try:
                self.socket.close()
            except Exception as e:
                 logger.warning(f"Error during socket close: {e}")


        # Wait for the receiver thread to finish
        if self.receiver_thread and self.receiver_thread.is_alive():
            logger.debug("Waiting for receiver thread to join...")
            self.receiver_thread.join(timeout=2.0) # Wait max 2 seconds
            if self.receiver_thread.is_alive():
                logger.warning("Receiver thread did not join in time.")

        logger.info("Socket closed and resources cleaned up.")
        # Clear caches (optional, depending on whether state should persist across connections)
        # with self.cache_lock:
        #      self.message_cache.clear()
        #      self.response_cache.clear()


    def is_connected(self) -> bool:
        """Check if the socket wrapper believes it is connected."""
        # Basic check on the flag. Could add a socket liveness check if needed.
        return self.connected and not self.shutdown_flag

