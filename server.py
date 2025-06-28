import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# Directories
BASE_DIR = os.getcwd()
COMMAND_DIR = os.path.join(BASE_DIR, "commands")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
LOG_FILE = os.path.join(BASE_DIR, "logs", "server.log")

# Ensure directories exist
os.makedirs(COMMAND_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def log(message):
    """Log server activity to server.log."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {message}\n")

class SimpleBITSRequestHandler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    base_dir = BASE_DIR
    supported_protocols = ["{7df0354d-249b-430f-820d-3d2a9bef4931}"]
    fragment_size_limit = 100 * 1024 * 1024  # 100MB

    # BITS Protocol headers
    K_BITS_SESSION_ID = 'BITS-Session-Id'
    K_BITS_ERROR_CONTEXT = 'BITS-Error-Context'
    K_BITS_ERROR_CODE = 'BITS-Error-Code'
    K_BITS_PACKET_TYPE = 'BITS-Packet-Type'
    K_BITS_SUPPORTED_PROTOCOLS = 'BITS-Supported-Protocols'
    K_BITS_PROTOCOL = 'BITS-Protocol'
    K_ACCEPT_ENCODING = 'Accept-Encoding'
    K_CONTENT_NAME = 'Content-Name'
    K_CONTENT_LENGTH = 'Content-Length'
    K_CONTENT_RANGE = 'Content-Range'
    K_CONTENT_ENCODING = 'Content-Encoding'
    V_ACK = 'Ack'

    # BITS server errors
    class BITSServerHResult:
        BG_ERROR_CONTEXT_REMOTE_FILE = '0x5'
        BG_E_TOO_LARGE = '0x80200020'
        E_INVALIDARG = '0x80070057'
        E_ACCESSDENIED = '0x80070005'
        ZERO = '0x0'
        ERROR_CODE_GENERIC = '0x1'

    def __send_response(self, headers_dict={}, status_code=200, data=b""):
        """Send server response with headers and status code."""
        self.send_response(status_code)
        for k, v in headers_dict.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)
        log(f"Sent response: status={status_code}, headers={headers_dict}, data={data.decode('utf-8', errors='ignore')}")

    def __release_resources(self, packet_type):
        """Release server resources for CLOSE-SESSION or CANCEL-SESSION."""
        headers = {
            self.K_BITS_PACKET_TYPE: self.V_ACK,
            self.K_CONTENT_LENGTH: '0'
        }
        try:
            session_id = self.headers.get(self.K_BITS_SESSION_ID, "").lower()
            headers[self.K_BITS_SESSION_ID] = session_id
            log(f"{packet_type} received for BITS-Session-Id: {session_id}")
            self.sessions[session_id].close()
            self.sessions.pop(session_id, None)
            status_code = 200
        except (AttributeError, KeyError):
            log(f"Error in {packet_type}: Invalid session_id")
            self.__send_response(headers, status_code=400)
            return
        except Exception as e:
            log(f"Error in {packet_type}: {e}")
            self.__send_response(headers, status_code=500)
            return
        self.__send_response(headers, status_code=status_code)

    def _handle_fragment(self):
        """Handle FRAGMENT packet from client."""
        headers = {
            self.K_BITS_PACKET_TYPE: self.V_ACK,
            self.K_CONTENT_LENGTH: '0'
        }
        try:
            session_id = self.headers.get(self.K_BITS_SESSION_ID, "").lower()
            content_length = int(self.headers.get(self.K_CONTENT_LENGTH, "0"))
            content_name = self.headers.get(self.K_CONTENT_NAME, None)
            content_range = self.headers.get(self.K_CONTENT_RANGE, "").split(" ")[-1]
            headers[self.K_BITS_SESSION_ID] = session_id
            crange, total_length = content_range.split("/")
            total_length = int(total_length)
            range_start, range_end = [int(num) for num in crange.split("-")]
            data = self.rfile.read(content_length)
            data_str = data.decode('utf-8', errors='ignore') or "<empty>"
            log(f"Received FRAGMENT: session_id={session_id}, content_name={content_name}, range={range_start}-{range_end}/{total_length}, data_length={len(data)}, data={data_str}")
        except (AttributeError, IndexError, ValueError) as e:
            log(f"Error parsing FRAGMENT headers: {e}")
            self.__send_response(headers, status_code=400)
            return

        try:
            is_last_fragment = self.sessions[session_id].add_fragment(total_length, range_start, range_end, data)
            headers['BITS-Received-Content-Range'] = range_end + 1
            status_code = 200
            if is_last_fragment:
                log(f"Completed FRAGMENT write for session_id={session_id}, file={self.sessions[session_id].absolute_file_path}")
        except Exception as e:
            headers[self.K_BITS_ERROR_CODE] = self.BITSServerHResult.ERROR_CODE_GENERIC
            headers[self.K_BITS_ERROR_CONTEXT] = self.BITSServerHResult.BG_ERROR_CONTEXT_REMOTE_FILE
            status_code = 500
            log(f"Error processing FRAGMENT: {e}")
        self.__send_response(headers, status_code=status_code)

    def _handle_ping(self):
        """Handle PING packet from client."""
        log("PING received")
        headers = {
            self.K_BITS_PACKET_TYPE: self.V_ACK,
            self.K_BITS_ERROR_CODE: '1',
            self.K_BITS_ERROR_CONTEXT: '',
            self.K_CONTENT_LENGTH: '0'
        }
        self.__send_response(headers, status_code=200)

    def _handle_cancel_session(self):
        """Handle CANCEL-SESSION packet."""
        log("CANCEL-SESSION received")
        self.__release_resources("CANCEL-SESSION")

    def _handle_close_session(self):
        """Handle CLOSE-SESSION packet."""
        log("CLOSE-SESSION received")
        self.__release_resources("CLOSE-SESSION")

    def _handle_create_session(self):
        """Handle CREATE-SESSION packet."""
        log(f"CREATE-SESSION received for path {self.path}")
        headers = {
            self.K_BITS_PACKET_TYPE: self.V_ACK,
            self.K_CONTENT_LENGTH: '0'
        }
        if not hasattr(self, "sessions"):
            self.sessions = {}

        try:
            client_supported_protocols = self.headers.get(self.K_BITS_SUPPORTED_PROTOCOLS, "").lower().split()
            protocols_intersection = set(client_supported_protocols).intersection(self.supported_protocols)
            if not protocols_intersection:
                headers[self.K_BITS_ERROR_CODE] = self.BITSServerHResult.E_INVALIDARG
                headers[self.K_BITS_ERROR_CONTEXT] = self.BITSServerHResult.BG_ERROR_CONTEXT_REMOTE_FILE
                log(f"Protocol mismatch: client={client_supported_protocols}, server={self.supported_protocols}")
                self.__send_response(headers, status_code=400)
                return

            headers[self.K_BITS_PROTOCOL] = list(protocols_intersection)[0]
            requested_path = self.path[1:] if self.path.startswith("/") else self.path
            absolute_file_path = os.path.join(self.base_dir, requested_path)
            session_id = str(hash((self.client_address[0], self.path)))
            log(f"Creating BITS-Session-Id: {session_id} for path {requested_path}, resolved to: {absolute_file_path}")

            if session_id not in self.sessions:
                self.sessions[session_id] = BITSUploadSession(absolute_file_path, self.fragment_size_limit)
            headers[self.K_BITS_SESSION_ID] = session_id
            status_code = self.sessions[session_id].get_last_status_code()
            headers[self.K_ACCEPT_ENCODING] = 'identity'
        except Exception as e:
            log(f"Error creating session: {e}")
            headers[self.K_BITS_ERROR_CODE] = self.BITSServerHResult.ERROR_CODE_GENERIC
            headers[self.K_BITS_ERROR_CONTEXT] = self.BITSServerHResult.BG_ERROR_CONTEXT_REMOTE_FILE
            self.__send_response(headers, status_code=500)
            return
        self.__send_response(headers, status_code=status_code)

    def do_GET(self):
        """Handle GET requests for command files."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path.lstrip('/')
        file_path = os.path.join(self.base_dir, path)
        log(f"GET request for path: {path}, resolved to: {file_path}, exists: {os.path.exists(file_path)}")
        if os.path.exists(file_path) and not os.path.isdir(file_path):
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', len(content))
                self.end_headers()
                self.wfile.write(content)
                log(f"Served file: {file_path}, size: {len(content)} bytes")
            except Exception as e:
                log(f"Error serving file {file_path}: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'text/plain')
                self.send_header('Content-Length', 0)
                self.end_headers()
        else:
            log(f"File not found: {file_path}")
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Content-Length', 0)
            self.end_headers()

    def do_HEAD(self):
        """Handle HEAD requests for command files."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path.lstrip('/')
        file_path = os.path.join(self.base_dir, path)
        log(f"HEAD request for path: {path}, resolved to: {file_path}, exists: {os.path.exists(file_path)}")
        if os.path.exists(file_path) and not os.path.isdir(file_path):
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', len(content))
                self.end_headers()
                log(f"HEAD served for file: {file_path}, size: {len(content)} bytes")
            except Exception as e:
                log(f"Error serving HEAD for file {file_path}: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'text/plain')
                self.send_header('Content-Length', 0)
                self.end_headers()
        else:
            log(f"File not found for HEAD: {file_path}")
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Content-Length', 0)
            self.end_headers()

    def do_BITS_POST(self):
        """Handle BITS POST requests."""
        bits_packet_type = self.headers.get(self.K_BITS_PACKET_TYPE, "").lower()
        log(f"Received BITS-POST: packet_type={bits_packet_type}, path={self.path}")
        try:
            do_function = getattr(self, f"_handle_{bits_packet_type.replace('-', '_')}")
            do_function()
        except AttributeError:
            headers = {
                self.K_BITS_ERROR_CODE: self.BITSServerHResult.E_INVALIDARG,
                self.K_BITS_ERROR_CONTEXT: self.BITSServerHResult.BG_ERROR_CONTEXT_REMOTE_FILE
            }
            log(f"Unknown BITS-Packet-Type: {bits_packet_type}")
            self.__send_response(headers, status_code=400)
        except Exception as e:
            headers = {
                self.K_BITS_ERROR_CODE: self.BITSServerHResult.ERROR_CODE_GENERIC,
                self.K_BITS_ERROR_CONTEXT: self.BITSServerHResult.BG_ERROR_CONTEXT_REMOTE_FILE
            }
            log(f"Internal BITS Server Error: {e}")
            self.__send_response(headers, status_code=500)

class BITSUploadSession:
    """Manage BITS upload sessions."""
    files_in_use = []

    def __init__(self, absolute_file_path, fragment_size_limit):
        self.fragment_size_limit = fragment_size_limit
        self.absolute_file_path = absolute_file_path
        self.fragments = []
        self.expected_file_length = -1

        if os.path.exists(absolute_file_path):
            if os.path.isdir(absolute_file_path):
                self._status_code = 403
                log(f"Error: {absolute_file_path} is a directory")
            elif absolute_file_path in self.files_in_use:
                self._status_code = 409
                log(f"Error: {absolute_file_path} already in use")
            else:
                self.files_in_use.append(absolute_file_path)
                self.__open_file()
        elif os.path.exists(os.path.dirname(absolute_file_path)):
            self.files_in_use.append(absolute_file_path)
            self.__open_file()
        else:
            self._status_code = 403
            log(f"Error: Directory {os.path.dirname(absolute_file_path)} does not exist")

    def __open_file(self):
        try:
            self.file = open(self.absolute_file_path, "wb")
            self._status_code = 200
            log(f"Opened file for writing: {self.absolute_file_path}")
        except Exception as e:
            self._status_code = 403
            log(f"Failed to open file {self.absolute_file_path}: {e}")

    def __get_final_data_from_fragments(self):
        return b"".join([frg['data'] for frg in self.fragments])

    def get_last_status_code(self):
        return self._status_code

    def add_fragment(self, file_total_length, range_start, range_end, data):
        """Add a new fragment to the upload session."""
        if self.fragment_size_limit < range_end - range_start:
            log(f"Fragment too large: {range_end - range_start} bytes")
            raise Exception("Fragment too large")

        if self.expected_file_length == -1:
            self.expected_file_length = file_total_length

        last_range_end = self.fragments[-1]['range_end'] if self.fragments else -1
        if last_range_end + 1 < range_start:
            log(f"Invalid fragment: last_range_end={last_range_end}, new_range_start={range_start}")
            raise Exception("Invalid fragment")
        elif last_range_end + 1 > range_start:
            range_start = last_range_end + 1

        self.fragments.append({
            'range_start': range_start,
            'range_end': range_end,
            'data': data
        })
        data_str = data.decode('utf-8', errors='ignore') or "<empty>"
        log(f"Added fragment: range={range_start}-{range_end}, total_length={file_total_length}, data={data_str}")

        if range_end + 1 == self.expected_file_length:
            try:
                final_data = self.__get_final_data_from_fragments()
                self.file.write(final_data)
                self.file.flush()
                data_str = final_data.decode('utf-8', errors='ignore') or "<empty>"
                log(f"Wrote final data to {self.absolute_file_path}: {data_str}")
                return True
            except Exception as e:
                log(f"Error writing final data to {self.absolute_file_path}: {e}")
                raise
        return False

    def close(self):
        """Close the upload session."""
        try:
            self.file.flush()
            self.file.close()
            self.files_in_use.remove(self.absolute_file_path)
            log(f"Closed upload session for {self.absolute_file_path}")
        except Exception as e:
            log(f"Error closing upload session for {self.absolute_file_path}: {e}")

def run(server_class=HTTPServer, handler_class=SimpleBITSRequestHandler, port=80):
    """Run the BITS server."""
    server_address = ('', port)
    try:
        httpd = server_class(server_address, handler_class)
        print(f"Starting BITS server on port {port}...")
        log(f"Starting BITS server on port {port}")
        httpd.serve_forever()
    except PermissionError:
        print(f"Error: Permission denied. Port {port} requires root privileges. Try running with sudo.")
        log(f"Permission denied on port {port}")
        raise
    except Exception as e:
        print(f"Error starting server: {e}")
        log(f"Error starting server: {e}")
        raise
    except KeyboardInterrupt:
        httpd.server_close()
        log("Server stopped")

if __name__ == "__main__":
    from sys import argv
    port = int(argv[1]) if len(argv) == 2 else 80
    run(port=port)