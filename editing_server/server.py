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

    result = {}

    for part in parts[1:-1]:  # Skip first and last empty parts
        if not part.strip():
            continue

        # Split headers and content
        if b"\r\n\r\n" in part:
            header_section, content = part.split(b"\r\n\r\n", 1)
        else:
            continue

        # Parse headers
        headers_text = header_section.decode("utf-8", errors="ignore")
        field_name = None
        filename = None
        content_type_field = None

        for line in headers_text.split("\r\n"):
            if line.startswith("Content-Disposition:"):
                # Extract name and filename
                if 'name="' in line:
                    start = line.find('name="') + 6
                    end = line.find('"', start)
                    field_name = line[start:end]
                if 'filename="' in line:
                    start = line.find('filename="') + 10
                    end = line.find('"', start)
                    filename = line[start:end]
            elif line.startswith("Content-Type:"):
                content_type_field = line.split(":", 1)[1].strip()

        if field_name:
            if filename:  # File field
                result[field_name] = {
                    "filename": filename,
                    "content": content.rstrip(b"\r\n"),
                    "content_type": content_type_field,
                }
            else:  # Regular field
                result[field_name] = {
                    "value": content.rstrip(b"\r\n").decode("utf-8", errors="ignore")
                }

    return result


def get_file_hash(file_path):
    """Get MD5 hash of a file for change detection."""
    import hashlib

    if not file_path.exists():
        return None
    try:
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        logging.warning(f"Could not calculate hash for {file_path}: {e}")
        return None


def validate_timeline_data(timeline_data):
    """
    Validate timeline data for required fields and data integrity.

    Args:
        timeline_data: List of timeline entries

    Returns:
        dict: {
            'valid': bool,
            'errors': list of error messages,
            'warnings': list of warning messages,
            'stats': dict with statistics
        }
    """
    errors = []
    warnings = []
    stats = {
        "total_entries": len(timeline_data),
        "missing_broll": 0,
        "missing_audio": 0,
        "missing_phrase": 0,
        "has_alternatives": 0,
        "has_images": 0,
        "invalid_times": 0,
    }

    required_fields = ["rush", "phrase", "broll", "start_time", "end_time"]

    for i, entry in enumerate(timeline_data):
        entry_id = f"Entry {i + 1}"

        # Check required fields
        for field in required_fields:
            if field not in entry or not entry[field]:
                errors.append(f"{entry_id}: Missing required field '{field}'")
                if field == "broll":
                    stats["missing_broll"] += 1
                elif field == "rush":
                    stats["missing_audio"] += 1
                elif field == "phrase":
                    stats["missing_phrase"] += 1

        # Check time validity
        if "start_time" in entry and "end_time" in entry:
            try:
                start = float(entry["start_time"])
                end = float(entry["end_time"])
                if start >= end:
                    errors.append(
                        f"{entry_id}: start_time ({start}) >= end_time ({end})"
                    )
                    stats["invalid_times"] += 1
                elif start < 0:
                    errors.append(f"{entry_id}: negative start_time ({start})")
                    stats["invalid_times"] += 1
            except (ValueError, TypeError):
                errors.append(f"{entry_id}: Invalid time format")
                stats["invalid_times"] += 1

        # Check for alternatives and images (not errors, just stats)
        if "broll2" in entry and entry["broll2"]:
            stats["has_alternatives"] += 1
        if "image" in entry and entry["image"]:
            stats["has_images"] += 1

        # Warnings for common issues
        if "selected_broll" in entry:
            selected = entry["selected_broll"]
            if selected not in ["broll", "broll2", "broll3"]:
                warnings.append(
                    f"{entry_id}: Unknown selected_broll value '{selected}'"
                )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
    }


def log_file_change(
    file_path, operation_type, details=None, before_content=None, after_content=None
):
    """
    Log detailed file change information.

    Args:
        file_path (Path): Path to the file that changed
        operation_type (str): Type of operation (read, write, upload, selection_change, etc.)
        details (dict): Additional details about the operation
        before_content (dict): Content before the change
        after_content (dict): Content after the change
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    log_message = f"\n{'=' * 80}\n"
    log_message += "📝 BROLL_TIMING.JSON CHANGE DETECTED\n"
    log_message += f"🕒 Timestamp: {timestamp}\n"
    log_message += f"📁 File: {file_path}\n"
    log_message += f"🔧 Operation: {operation_type}\n"

    if details:
        log_message += "📋 Details:\n"
        for key, value in details.items():
            log_message += f"   • {key}: {value}\n"

    # Log content differences if provided
    if before_content and after_content:
        log_message += "🔄 Content Changes:\n"

        # Handle both array format and rushes format
        if isinstance(before_content, list) and isinstance(after_content, list):
            # Array format - direct comparison
            for i, (before_item, after_item) in enumerate(
                zip(before_content, after_content)
            ):
                changes = []

                # Check for selection changes
                before_selection = before_item.get("selected_broll", "broll")
                after_selection = after_item.get("selected_broll", "broll")
                if before_selection != after_selection:
                    changes.append(
                        f"selected_broll: {before_selection} → {after_selection}"
                    )

                # Check for image overlay changes
                before_image = before_item.get("image")
                after_image = after_item.get("image")
                if before_image != after_image:
                    changes.append(f"image: {before_image} → {after_image}")

                if changes:
                    phrase = before_item.get("phrase", f"item_{i}")[:50]
                    log_message += (
                        f"   • Item[{i}] '{phrase}...': {', '.join(changes)}\n"
                    )

        # Check for selection changes in rushes format
        elif (
            isinstance(before_content, dict)
            and isinstance(after_content, dict)
            and "rushes" in before_content
            and "rushes" in after_content
        ):
            for rush_id in before_content.get("rushes", {}):
                if rush_id in after_content.get("rushes", {}):
                    before_rush = before_content["rushes"][rush_id]
                    after_rush = after_content["rushes"][rush_id]

                    # Check for broll changes
                    before_brolls = before_rush.get("brolls", [])
                    after_brolls = after_rush.get("brolls", [])

                    for i, (before_broll, after_broll) in enumerate(
                        zip(before_brolls, after_brolls)
                    ):
                        changes = []

                        # Check for selection changes
                        before_selection = before_broll.get("selected_broll", "broll")
                        after_selection = after_broll.get("selected_broll", "broll")
                        if before_selection != after_selection:
                            changes.append(
                                f"selected_broll: {before_selection} → {after_selection}"
                            )

                        # Check for image overlay changes
                        before_image = before_broll.get("image")
                        after_image = after_broll.get("image")
                        if before_image != after_image:
                            changes.append(f"image: {before_image} → {after_image}")

                        if changes:
                            log_message += (
                                f"   • {rush_id} broll[{i}]: {', '.join(changes)}\n"
                            )

    log_message += f"{'=' * 80}\n"

    logging.info(log_message)

    log_message += f"{'=' * 80}\n"

    logging.info(log_message)


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
        self.ressources_dir.mkdir(exist_ok=True, parents=True)

        # Store project and language info for path resolution
        self.temp_path = temp_path
        self.project_name = "unknown"
        self.language = None

        # Extract project name and language from path
        # Path format: projects/<project-name>/<language>/temp/ or projects/<project-name>/temp/
        parts = temp_path.parts
        if "projects" in parts:
            project_idx = parts.index("projects")
            if len(parts) > project_idx + 1:
                self.project_name = parts[project_idx + 1]
            if len(parts) > project_idx + 2 and parts[project_idx + 2] != "temp":
                self.language = parts[project_idx + 2]

        logging.info(
            f"📁 Project: {self.project_name}, Language: {self.language or 'N/A'}"
        )

        # Store initial file state for change tracking
        self.last_known_hash = get_file_hash(self.broll_timing_file)
        if self.last_known_hash:
            logging.info(
                f"🔍 MONITORING: Initial broll_timing.json hash: {self.last_known_hash[:8]}..."
            )

        super().__init__(*args, **kwargs)

    def _check_file_external_changes(self):
        """Check if the broll_timing.json file was changed externally."""
        current_hash = get_file_hash(self.broll_timing_file)
        if current_hash != self.last_known_hash:
            log_file_change(
                self.broll_timing_file,
                "EXTERNAL_CHANGE_DETECTED",
                details={
                    "previous_hash": self.last_known_hash,
                    "current_hash": current_hash,
                    "detection_source": "server_file_monitoring",
                },
            )
            self.last_known_hash = current_hash
            return True
        return False

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

        # Use stored project name and language
        project_path = self.project_name
        if self.language:
            project_path = f"{self.project_name}/{self.language}"

        logging.debug(f"SERVER: Project path for interface: {project_path}")

        # Read HTML file and replace placeholders
        interface_path = Path(__file__).parent / "interface.html"
        logging.debug(f"SERVER: HTML file path: {interface_path}")

        if not interface_path.exists():
            logging.error(f"SERVER: ERROR - HTML file not found: {interface_path}")
            self._send_404()
            return

        logging.debug("SERVER: HTML file found, reading...")
        with open(interface_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        logging.debug(f"SERVER: HTML read, size: {len(html_content)} characters")
        html_content = html_content.replace("{{PROJECT_NAME}}", self.project_name)
        html_content = html_content.replace("{{PROJECT_PATH}}", project_path)
        html_content = html_content.replace("{{LANGUAGE}}", self.language or "")
        logging.debug("SERVER: PROJECT_NAME replacement done")

        self._send_response(200, html_content, "text/html")
        logging.debug("SERVER: HTML interface sent")

    def _serve_timeline_data(self):
        """Serve timeline data as JSON."""
        logging.debug("SERVER: _serve_timeline_data() called")
        logging.debug(f"SERVER: broll_timing.json path: {self.broll_timing_file}")

        # Check for external file changes before serving
        self._check_file_external_changes()

        if not self.broll_timing_file.exists():
            logging.debug("SERVER: ERROR - broll_timing.json not found")
            self._send_response(
                404, '{"error": "broll_timing.json not found"}', "application/json"
            )
            return

        logging.debug("SERVER: broll_timing.json found, reading...")

        # Log file read operation
        log_file_change(
            self.broll_timing_file,
            "READ",
            details={"request_source": "web_interface", "endpoint": "/api/timeline"},
        )

        with open(self.broll_timing_file, "r", encoding="utf-8") as f:
            timeline_data = json.load(f)

        # Validate timeline data
        validation_result = validate_timeline_data(timeline_data)

        if not validation_result["valid"]:
            logging.warning("⚠️  Timeline validation errors found:")
            for error in validation_result["errors"][:5]:  # Show first 5 errors
                logging.warning(f"   • {error}")
            if len(validation_result["errors"]) > 5:
                logging.warning(
                    f"   • ...and {len(validation_result['errors']) - 5} more errors"
                )

        if validation_result["warnings"]:
            logging.info("ℹ️  Timeline validation warnings:")
            for warning in validation_result["warnings"][:3]:
                logging.info(f"   • {warning}")

        # Log stats
        stats = validation_result["stats"]
        logging.info(
            f"📊 Timeline Stats: {stats['total_entries']} entries, "
            f"{stats['has_alternatives']} with alternatives, "
            f"{stats['has_images']} with images"
        )

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

        logging.debug(f"📹 Requested B-roll file: {file_path}")

        if file_path.exists():
            logging.debug(f"✅ B-roll found: {file_path}")
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
            # Serve placeholder image for missing B-roll thumbnails
            if file_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                logging.debug(f"📦 Serving placeholder for missing B-roll: {file_path}")
                self._serve_placeholder_image(str(file_path))
            else:
                logging.warning(f"❌ B-roll not found: {file_path}")
                self._send_404()

    def _serve_placeholder_image(self, filename):
        """Serve a placeholder SVG image for missing B-roll files."""
        # Extract just the filename without path for display
        display_name = Path(filename).stem[:40] + "..."

        # Create an SVG placeholder
        svg_content = f"""<svg width="240" height="136" xmlns="http://www.w3.org/2000/svg">
            <rect width="240" height="136" fill="#f1f3f4"/>
            <rect x="10" y="10" width="220" height="116" fill="#e1e5e9" stroke="#adb5bd" stroke-width="2" rx="8"/>
            <text x="120" y="60" font-family="Arial, sans-serif" font-size="14" fill="#6c757d" text-anchor="middle">🎥</text>
            <text x="120" y="80" font-family="Arial, sans-serif" font-size="10" fill="#6c757d" text-anchor="middle">B-roll not found</text>
            <text x="120" y="95" font-family="Arial, sans-serif" font-size="8" fill="#adb5bd" text-anchor="middle">{display_name}</text>
        </svg>"""

        self.send_response(200)
        self.send_header("Content-type", "image/svg+xml")
        self.send_header("Content-length", str(len(svg_content.encode())))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(svg_content.encode())

    def _serve_project_file(self):
        """Serve files from projects folder for preview."""
        file_path = Path(self.path[1:])  # Remove initial '/'

        logging.debug(f"📂 Requested project file: {file_path}")

        if file_path.exists():
            logging.debug(f"✅ File found: {file_path}")
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
            logging.warning(f"❌ File not found: {file_path}")
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
            # Read current content for logging
            with open(self.broll_timing_file, "r", encoding="utf-8") as f:
                before_content = json.load(f)

            timeline_data = before_content.copy()

            if 0 <= broll_index < len(timeline_data):
                # Add image field WITHOUT replacing the broll
                timeline_data[broll_index]["image"] = f"ressources/{new_filename}"

                # Write updated content
                with open(self.broll_timing_file, "w", encoding="utf-8") as f:
                    json.dump(timeline_data, f, indent=2, ensure_ascii=False)

                # Update our tracking hash
                self.last_known_hash = get_file_hash(self.broll_timing_file)

                # Log the file change with details
                log_file_change(
                    self.broll_timing_file,
                    "IMAGE_UPLOAD",
                    details={
                        "broll_index": broll_index,
                        "uploaded_filename": file_item["filename"],
                        "saved_as": new_filename,
                        "image_path": f"ressources/{new_filename}",
                        "user_agent": self.headers.get("User-Agent", "unknown"),
                    },
                    before_content=before_content,
                    after_content=timeline_data,
                )

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

            # Read current content for comparison and hash checking
            before_content = {}
            before_hash = get_file_hash(self.broll_timing_file)
            if self.broll_timing_file.exists():
                with open(self.broll_timing_file, "r", encoding="utf-8") as f:
                    before_content = json.load(f)

            # Save modified timeline
            with open(self.broll_timing_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Get after hash to confirm changes
            after_hash = get_file_hash(self.broll_timing_file)
            self.last_known_hash = after_hash  # Update our tracking

            # Log the change with detailed analysis (only if file actually changed)
            if before_hash != after_hash:
                log_file_change(
                    self.broll_timing_file,
                    "BROLL_SELECTION_CHANGE",
                    details={
                        "update_source": "web_interface",
                        "user_agent": self.headers.get("User-Agent", "unknown"),
                        "content_length": content_length,
                        "update_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "before_hash": before_hash,
                        "after_hash": after_hash,
                        "file_size_before": len(str(before_content))
                        if before_content
                        else 0,
                        "file_size_after": len(str(data)),
                    },
                    before_content=before_content,
                    after_content=data,
                )
            else:
                logging.debug(
                    "BROLL_TIMING.JSON: No actual changes detected (same file hash)"
                )

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
