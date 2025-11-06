#!/usr/bin/env python3
"""
Timeline Editing Server for StoryForge
Visual interface for editing broll_timing.json with B-roll selection and image upload.

Usage: python editing_server/server.py
"""

import json
import logging
import base64
import secrets
import yaml
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import time


logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


def parse_multipart_form(rfile, headers):
    """
    Parse multipart form data without using deprecated cgi module.
    Returns a dictionary with field names as keys.
    For file fields, the value is a dict with 'filename', 'content', and 'content_type'.
    For regular fields, the value is a dict with 'value'.
    """
    content_type = headers.get("Content-Type", "")
    if not content_type.startswith("multipart/form-data"):
        return {}

    # Extract boundary from content-type
    boundary = None
    for part in content_type.split(";"):
        if "boundary=" in part:
            boundary = part.split("boundary=")[1].strip()
            break

    if not boundary:
        return {}

    # Read the entire body
    content_length = int(headers.get("Content-Length", 0))
    body = rfile.read(content_length)

    # Parse multipart data manually
    boundary_bytes = f"--{boundary}".encode()
    parts = body.split(boundary_bytes)

    form_data = {}

    for part in parts:
        if not part or part == b"--\r\n" or part == b"--":
            continue

        # Split headers and content
        if b"\r\n\r\n" not in part:
            continue

        header_section, content = part.split(b"\r\n\r\n", 1)

        # Remove trailing \r\n
        content = content.rstrip(b"\r\n")

        # Parse headers
        headers_text = header_section.decode("utf-8", errors="ignore")
        field_name = None
        filename = None
        content_type = None

        for line in headers_text.split("\r\n"):
            if line.lower().startswith("content-disposition:"):
                # Extract field name and filename
                for item in line.split(";"):
                    item = item.strip()
                    if 'name="' in item:
                        field_name = item.split('name="')[1].split('"')[0]
                    if 'filename="' in item:
                        filename = item.split('filename="')[1].split('"')[0]
            elif line.lower().startswith("content-type:"):
                content_type = line.split(":", 1)[1].strip()

        if field_name:
            if filename:
                # File field
                form_data[field_name] = {
                    "filename": filename,
                    "content": content,
                    "content_type": content_type or "application/octet-stream",
                }
            else:
                # Regular field
                form_data[field_name] = {
                    "value": content.decode("utf-8", errors="ignore")
                }

    return form_data


def load_auth_config():
    """Load authentication configuration from config.yml"""
    # Get config.yml from project root
    current_dir = Path(
        __file__
    ).parent.parent  # editing_server/server.py -> project root
    config_file = current_dir / "config.yml"
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config.get("dashboard", {}).get("auth", {})
    return {}


class TimelineEditingHandler(BaseHTTPRequestHandler):
    """HTTP handler for the timeline editing interface."""

    def __init__(self, *args, config=None, **kwargs):
        # Determine the path to broll_timing.json
        if config and "paths" in config and "temp" in config["paths"]:
            temp_path = Path(config["paths"]["temp"])
        else:
            temp_path = Path("temp")
        self.broll_timing_file = temp_path / "broll_timing.json"
        self.ressources_dir = Path("b-roll/ressources")
        self.ressources_dir.mkdir(exist_ok=True)
        super().__init__(*args, **kwargs)

    def check_auth(self):
        """Check HTTP Basic authentication"""
        auth_config = load_auth_config()

        # If auth is disabled, allow access
        if not auth_config.get("enabled", False):
            return True

        # Get Authorization header
        auth_header = self.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return False

        try:
            # Decode credentials
            encoded_credentials = auth_header[6:]  # Remove "Basic "
            decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = decoded_credentials.split(":", 1)

            # Verify credentials
            correct_username = auth_config.get("username", "admin")
            correct_password = auth_config.get("password", "admin")

            is_correct_username = secrets.compare_digest(username, correct_username)
            is_correct_password = secrets.compare_digest(password, correct_password)

            return is_correct_username and is_correct_password

        except Exception:
            return False

    def send_auth_required(self):
        """Send 401 response requesting authentication"""
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Timeline Editing Server"')
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>401 Unauthorized</h1><p>Authentication required</p>")

    def do_GET(self):
        """Handle GET requests (HTML interface and JSON data)."""
        # Check authentication
        if not self.check_auth():
            self.send_auth_required()
            return

        try:
            if self.path == "/" or self.path == "/index.html":
                self._serve_interface()
            elif self.path == "/api/timeline":
                self._serve_timeline_data()
            elif self.path.startswith("/b-roll/"):
                self._serve_broll_file()
            elif self.path.startswith("/projects/"):
                self._serve_project_file()
            else:
                self._send_404()
        except Exception as e:
            logging.error(f"GET error {self.path}: {e}")
            self._send_500()

    def do_POST(self):
        """Handle POST requests (image upload, timeline modification)."""
        # Check authentication
        if not self.check_auth():
            self.send_auth_required()
            return

        try:
            if self.path == "/api/upload":
                self._handle_upload()
            elif self.path == "/api/update_timeline":
                self._handle_timeline_update()
            else:
                self._send_404()
        except Exception as e:
            logging.error(f"POST error {self.path}: {e}")
            self._send_500()

    def _serve_interface(self):
        """Serve the main HTML interface."""
        logging.debug("SERVER: _serve_interface() called")

        # Get project name from temp path
        project_name = "unknown"
        if hasattr(self, "broll_timing_file") and self.broll_timing_file:
            # Extract project name from temp path
            temp_path = self.broll_timing_file.parent
            if temp_path.name == "temp" and temp_path.parent.name != "temp":
                project_name = temp_path.parent.name

        logging.debug(f"SERVER: Detected project name: {project_name}")

        # Read HTML file and replace project name
        interface_path = Path(__file__).parent / "interface.html"
        logging.debug(f"SERVER: HTML file path: {interface_path}")

        if not interface_path.exists():
            logging.debug(f"SERVER: ERROR - HTML file not found: {interface_path}")
            self._send_404()
            return

        logging.debug("SERVER: HTML file found, reading...")
        with open(interface_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        logging.debug(f"SERVER: HTML read, size: {len(html_content)} characters")
        html_content = html_content.replace("{{PROJECT_NAME}}", project_name)
        logging.debug("SERVER: PROJECT_NAME replacement done")

        self._send_response(200, html_content, "text/html")
        logging.debug("SERVER: HTML interface sent")

    def _serve_timeline_data(self):
        """Serve timeline data as JSON."""
        logging.debug("SERVER: _serve_timeline_data() called")
        logging.debug(f"SERVER: broll_timing.json path: {self.broll_timing_file}")

        if not self.broll_timing_file.exists():
            logging.debug("SERVER: ERROR - broll_timing.json not found")
            self._send_response(
                404, '{"error": "broll_timing.json not found"}', "application/json"
            )
            return

        logging.debug("SERVER: broll_timing.json found, reading...")
        with open(self.broll_timing_file, "r", encoding="utf-8") as f:
            timeline_data = json.load(f)

        logging.debug(f"SERVER: Timeline loaded, {len(timeline_data)} elements")
        response_data = json.dumps(timeline_data, indent=2)
        logging.debug(
            f"SERVER: JSON response prepared, size: {len(response_data)} characters"
        )

        self._send_response(200, response_data, "application/json")
        logging.debug("SERVER: Timeline JSON sent")

    def _serve_broll_file(self):
        """Serve B-roll files for preview."""
        file_path = Path(self.path[1:])  # Remove initial '/'

        if file_path.exists():
            # Determine MIME type
            if file_path.suffix.lower() in [".jpg", ".jpeg"]:
                content_type = "image/jpeg"
            elif file_path.suffix.lower() == ".png":
                content_type = "image/png"
            elif file_path.suffix.lower() in [".mp4", ".mov"]:
                content_type = "video/mp4"
            elif file_path.suffix.lower() in [".mp3", ".wav"]:
                content_type = "audio/mpeg"
            else:
                content_type = "application/octet-stream"

            with open(file_path, "rb") as f:
                data = f.read()

            self.send_response(200)
            self.send_header("Content-type", content_type)
            self.send_header("Content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self._send_404()

    def _serve_project_file(self):
        """Serve files from projects folder for preview."""
        file_path = Path(self.path[1:])  # Remove initial '/'

        if file_path.exists():
            # Determine MIME type
            if file_path.suffix.lower() in [".jpg", ".jpeg"]:
                content_type = "image/jpeg"
            elif file_path.suffix.lower() == ".png":
                content_type = "image/png"
            elif file_path.suffix.lower() in [".mp4", ".mov"]:
                content_type = "video/mp4"
            elif file_path.suffix.lower() in [".mp3", ".wav"]:
                content_type = "audio/mpeg"
            elif file_path.suffix.lower() == ".txt":
                content_type = "text/plain"
            elif file_path.suffix.lower() == ".json":
                content_type = "application/json"
            else:
                content_type = "application/octet-stream"

            with open(file_path, "rb") as f:
                data = f.read()

            self.send_response(200)
            self.send_header("Content-type", content_type)
            self.send_header("Content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self._send_404()

    def _handle_upload(self):
        """Handle image uploads to add as overlay on a B-roll."""
        try:
            # Parse multipart data using modern approach (replaces deprecated cgi module)
            form = parse_multipart_form(self.rfile, self.headers)

            # Get file and index
            if "file" not in form or "broll_index" not in form:
                self._send_400("Missing file or index")
                return

            file_item = form["file"]
            broll_index = int(form["broll_index"]["value"])

            if not file_item.get("filename"):
                self._send_400("No file selected")
                return

            # Save image to b-roll/ressources/
            timestamp = int(time.time())
            file_ext = Path(file_item["filename"]).suffix
            new_filename = f"uploaded_{timestamp}_{broll_index}{file_ext}"
            save_path = self.ressources_dir / new_filename

            with open(save_path, "wb") as f:
                f.write(file_item["content"])

            # Update broll_timing.json
            with open(self.broll_timing_file, "r", encoding="utf-8") as f:
                timeline_data = json.load(f)

            if 0 <= broll_index < len(timeline_data):
                # Add image field WITHOUT replacing the broll
                timeline_data[broll_index]["image"] = f"ressources/{new_filename}"

                with open(self.broll_timing_file, "w", encoding="utf-8") as f:
                    json.dump(timeline_data, f, indent=2, ensure_ascii=False)

                response = {
                    "success": True,
                    "message": f"Image added over B-roll {broll_index}",
                    "new_path": f"ressources/{new_filename}",
                }
                self._send_response(200, json.dumps(response), "application/json")
            else:
                self._send_400("Invalid B-roll index")

        except Exception as e:
            logging.error(f"Upload error: {e}")
            self._send_500()

    def _handle_timeline_update(self):
        """Handle timeline updates."""
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode("utf-8"))

            # Save modified timeline
            with open(self.broll_timing_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            response = {"success": True, "message": "Timeline updated"}
            self._send_response(200, json.dumps(response), "application/json")

        except Exception as e:
            logging.error(f"Timeline update error: {e}")
            self._send_500()

    def _send_response(self, code, data, content_type):
        """Send HTTP response."""
        self.send_response(code)
        self.send_header("Content-type", content_type)
        self.send_header(
            "Content-length", str(len(data.encode() if isinstance(data, str) else data))
        )
        self.end_headers()

        if isinstance(data, str):
            self.wfile.write(data.encode())
        else:
            self.wfile.write(data)

    def _send_404(self):
        """Send 404 error."""
        self._send_response(404, "Not Found", "text/plain")

    def _send_400(self, message):
        """Send 400 error."""
        self._send_response(400, message, "text/plain")

    def _send_500(self):
        """Send 500 error."""
        self._send_response(500, "Internal Server Error", "text/plain")

    def log_message(self, format, *args):
        """Suppress automatic server logs."""
        pass


def start_premontage_server(config=None, port=47393):
    """
    Start the timeline editing server.

    Args:
        config (dict): Project configuration (for temp path)
        port (int): Server port (default: 47393)
    """
    # Determine path to broll_timing.json file
    if config and "paths" in config and "temp" in config["paths"]:
        temp_path = Path(config["paths"]["temp"])
    else:
        temp_path = Path("temp")

    broll_timing_file = temp_path / "broll_timing.json"

    if not broll_timing_file.exists():
        logging.error(f"❌ Error: {broll_timing_file} not found")
        logging.debug(
            "   First run: python editing_server/server.py (with proper broll_timing.json)"
        )
        return False

    try:
        # Create resources folder
        ressources_dir = Path("b-roll/ressources")
        ressources_dir.mkdir(exist_ok=True)

        # Start the server
        server = HTTPServer(
            ("0.0.0.0", port),
            lambda *args, **kwargs: TimelineEditingHandler(
                *args, config=config, **kwargs
            ),
        )

        logging.info(f"🎬 Timeline editing server started on http://0.0.0.0:{port}")

        # Display public IP if available
        try:
            import requests

            response = requests.get(
                "http://leader-referencement.com/get_current_ip.php", timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                public_ip = data.get("ip")
                if public_ip:
                    logging.info(
                        f"🌐 Access via: http://localhost:{port} (local) or http://{public_ip}:{port} (external)"
                    )
                else:
                    logging.info(
                        f"🌐 Access via: http://localhost:{port} (local) or http://your-ip:{port} (external)"
                    )
            else:
                logging.info(
                    f"🌐 Access via: http://localhost:{port} (local) or http://your-ip:{port} (external)"
                )
        except Exception:
            logging.info(
                f"🌐 Access via: http://localhost:{port} (local) or http://your-ip:{port} (external)"
            )

        # Display authentication status
        auth_config = load_auth_config()
        if auth_config.get("enabled", False):
            logging.info(
                f"🔒 Authentication: ENABLED (user: {auth_config.get('username', 'admin')})"
            )
            logging.info("ℹ️  To disable: config.yml → dashboard.auth.enabled: false")
        else:
            logging.info("🔓 Authentication: DISABLED")
            logging.info("ℹ️  To enable: config.yml → dashboard.auth.enabled: true")

        logging.info("📝 Timeline editing interface ready")
        logging.info("⏹️  Press Ctrl+C to stop the server")

        # Browser opening is now handled by the dashboard
        logging.info(
            "🌐 Interface accessible via dashboard (button 'Open Timeline Editor')"
        )

        # Start the server
        server.serve_forever()

    except KeyboardInterrupt:
        logging.info("\n🛑 Server stopped")
        return True
    except Exception as e:
        logging.info(f"❌ Error starting server: {e}")
        return False


def start_timeline_server(config=None, port=47393):
    """
    Start the timeline editing server.

    Args:
        config (dict): Project configuration (for temp path)
        port (int): Server port (default: 47393)
    """
    return start_premontage_server(config, port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Start the timeline editing server")
    parser.add_argument(
        "--project", type=str, help="Project name (looks in projects/<name>/temp/)"
    )
    parser.add_argument(
        "--temp",
        type=str,
        help="Direct path to temp directory containing broll_timing.json",
    )
    parser.add_argument(
        "--port", type=int, default=47393, help="Server port (default: 47393)"
    )

    args = parser.parse_args()

    config = None
    if args.project:
        # Use project-specific temp directory
        config = {"paths": {"temp": f"projects/{args.project}/temp"}}
        logging.info(f"📁 Using project: {args.project}")
    elif args.temp:
        # Use custom temp path
        config = {"paths": {"temp": args.temp}}
        logging.info(f"📁 Using temp directory: {args.temp}")
    else:
        # Default to root temp directory
        logging.info("📁 Using default temp directory: temp/")
        logging.info(
            "💡 Tip: Use --project <name> or --temp <path> to specify a different location"
        )

    start_premontage_server(config=config, port=args.port)
