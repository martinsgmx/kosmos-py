import socket
import ssl
import logging
from threading import Thread
import os


# logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(".//logs//server.log"), logging.StreamHandler()],
)


class TCPServer:
    # 0.0.0.0 as alias for localhost
    def __init__(
        self,
        host=os.getenv("HOST", "localhost"),
        port=os.getenv("SCKT_PORT", 5000),
        certfile="auth//server.crt",
        keyfile="auth//server.key",
    ):
        self.host = host
        self.port = port
        self.certfile = certfile
        self.keyfile = keyfile
        self.context = self._create_ssl_context()
        self.running = False
        self.clients = {}

    def _create_ssl_context(self):
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(cafile="auth//clients//client.crt")
        context.set_ciphers("ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384")
        return context

    def _handle_client(self, connection, address):
        client_id = f"{address[0]}:{address[1]}"
        self.clients[client_id] = connection

        try:
            logging.info(f"Client connected: {client_id}")

            cert = connection.getpeercert()
            if not cert:
                raise ssl.SSLError("No client certificate provided")

            subject = dict(x[0] for x in cert["subject"])
            logging.info(f"Client certificate subject: {subject}")

            while self.running:
                try:
                    data = connection.recv(1024)
                    if not data:
                        break

                    # avoid overflow at console
                    if len(data) > 1024:
                        logging.warning(f"Oversized message from {client_id}")
                        connection.send(b"ERROR: Message too large")
                        continue

                    message = data.decode("utf-8").strip().upper()
                    logging.info(f"Received from {client_id}: {message}")

                    response = f"{message}"
                    connection.send(response.encode("utf-8"))

                except UnicodeDecodeError:
                    logging.warning(f"Invalid UTF-8 data from {client_id}")
                    connection.send(b"ERROR: Invalid UTF-8 encoding")
                except socket.error as e:
                    logging.error(f"Socket error with {client_id}: {e}")
                    break

        except Exception as e:
            logging.error(f"Error with client {client_id}: {e}")
        finally:
            connection.close()
            self.clients.pop(client_id, None)
            logging.info(f"Client disconnected: {client_id}")

    def start(self):
        # entrypoint server
        self.running = True
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((self.host, self.port))
                sock.listen(5)
                logging.info(f"Server started on {self.host}:{self.port}")

                while self.running:
                    try:
                        connection, address = sock.accept()
                        try:
                            # ssl handshake
                            ssl_conn = self.context.wrap_socket(connection, server_side=True)
                            # asycnhronous thread for each client
                            Thread(
                                target=self._handle_client,
                                args=(ssl_conn, address),
                                daemon=True,
                            ).start()
                        except ssl.SSLError as e:
                            logging.error(f"SSL handshake failed: {e}")
                            conn.close()
                    except KeyboardInterrupt:
                        logging.info("Server shutting down...")
                        self.running = False
                    except Exception as e:
                        logging.error(f"Server error: {e}")
                        self.running = False

        except Exception as e:
            logging.error(f"Fatal server error: {e}")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        for client_id, connection in list(self.clients.items()):
            try:
                connection.close()
            except:
                pass
        logging.info("Server stopped")


if __name__ == "__main__":
    server = TCPServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
