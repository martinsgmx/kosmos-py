import socket
import ssl
import logging
import sys
import os


# logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(".//logs//client.log"), logging.StreamHandler()],
)


class TCPClient:
    # 0.0.0.0 as alias for localhost
    def __init__(
        self,
        host=os.getenv("HOST", "localhost"),
        port=os.getenv("SCKT_PORT", 5000),
        certfile="auth//clients//client.crt",
        keyfile="auth//clients//client.key",
    ):
        self.host = host
        self.port = port
        self.certfile = certfile
        self.keyfile = keyfile
        self.context = self._create_ssl_context()
        self.connected = False

    def _create_ssl_context(self):
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)
        context.load_verify_locations(cafile="auth//server.crt")
        context.verify_mode = ssl.CERT_REQUIRED
        context.set_ciphers("ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384")
        return context

    def connect(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection = self.context.wrap_socket(sock, server_hostname=self.host)
            self.connection.connect((self.host, self.port))

            cert = self.connection.getpeercert()
            if not cert:
                raise ssl.SSLError("No server certificate provided")

            subject = dict(x[0] for x in cert["subject"])
            logging.info(f"Connected to server with certificate: {subject}")

            self.connected = True
            return True

        except ssl.SSLError as e:
            logging.error(f"SSL error: {e}")
            return False
        except socket.error as e:
            logging.error(f"Connection error: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return False

    def send_message(self, message):
        if not self.connected:
            logging.error("Not connected to server")
            return None

        try:
            if not isinstance(message, str):
                raise ValueError("Message must be a string")
            # avoid terminal overflow
            if len(message) > 1024:
                raise ValueError("Message too large")

            self.connection.sendall(message.encode("utf-8"))
            response = self.connection.recv(1024)
            return response.decode("utf-8")

        except UnicodeEncodeError:
            logging.error("Message contains invalid characters")
            return None
        except socket.error as e:
            logging.error(f"Communication error: {e}")
            self.close()
            return None
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            return None

    def close(self):
        if hasattr(self, "connection"):
            try:
                self.connection.close()
            except:
                pass
        self.connected = False
        logging.info("Connection closed")

    def interactive_session(self):
        if not self.connect():
            return

        try:
            print("Connected to server. Type 'exit' to quit or DESCONEXION.")
            while True:
                try:
                    message = input("> ")
                    if message.lower() == "exit" or message.upper() == "DESCONEXION":
                        break

                    response = self.send_message(message)
                    if response is not None:
                        print(f"Server response: {response}")

                except KeyboardInterrupt:
                    # ctr + c , action
                    print("\nInterrupted by user")
                    break
                except Exception as e:
                    logging.error(f"Error: {e}")
                    break
        finally:
            self.close()


if __name__ == "__main__":
    client = TCPClient()
    if len(sys.argv) > 1:
        if client.connect():
            response = client.send_message(" ".join(sys.argv[1:]))
            if response:
                print(f"Server response: {response}")
            client.close()
    else:
        client.interactive_session()
