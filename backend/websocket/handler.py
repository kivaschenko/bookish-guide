"""
WebSocket handler for real-time communication.
Provides live logging, progress updates, and bidirectional communication.
"""

import json
import logging
from typing import List, Dict, Any
from datetime import datetime

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, client_info: Dict[str, Any] = {}):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_info[websocket] = client_info or {}
        await self.send_personal_message(
            {
                "type": "connection_established",
                "message": "Connected to Premontage server",
                "timestamp": datetime.now().isoformat(),
            },
            websocket,
        )

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_info:
            del self.connection_info[websocket]

    async def send_personal_message(
        self, message: Dict[str, Any], websocket: WebSocket
    ):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logging.error(f"Error sending WebSocket message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logging.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def send_log_message(
        self, level: str, message: str, details: Dict[str, Any] = {}
    ):
        """Send a formatted log message to all clients."""
        log_data = {
            "type": "log",
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
        }
        await self.broadcast(log_data)

    async def send_progress_update(
        self, task: str, progress: float, status: str, details: Dict[str, Any] = {}
    ):
        """Send a progress update to all clients."""
        progress_data = {
            "type": "progress",
            "task": task,
            "progress": progress,  # 0.0 to 1.0
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
        }
        await self.broadcast(progress_data)

    async def send_system_notification(
        self, title: str, message: str, notification_type: str = "info"
    ):
        """Send a system notification to all clients."""
        notification = {
            "type": "notification",
            "title": title,
            "message": message,
            "notification_type": notification_type,  # info, success, warning, error
            "timestamp": datetime.now().isoformat(),
        }
        await self.broadcast(notification)

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)


class WebSocketManager:
    """Main WebSocket manager with enhanced features."""

    def __init__(self):
        self.manager = ConnectionManager()
        self.setup_logging_handler()

    def setup_logging_handler(self):
        """Setup logging handler to capture logs and send via WebSocket."""

        class WebSocketLoggingHandler(logging.Handler):
            def __init__(self, ws_manager):
                super().__init__()
                self.ws_manager = ws_manager

            def emit(self, record):
                try:
                    # Format the log message
                    message = self.format(record)
                    level = record.levelname.lower()

                    # Send asynchronously (note: this is a simplified approach)
                    # In production, you might want to use asyncio.create_task()
                    import asyncio

                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(
                                self.ws_manager.manager.send_log_message(level, message)
                            )
                    except RuntimeError:
                        pass  # No event loop running
                except Exception:
                    pass  # Ignore errors in logging handler

        # Add the handler to the root logger
        handler = WebSocketLoggingHandler(self)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)

    async def connect(self, websocket: WebSocket, client_info: Dict[str, Any] = {}):
        """Connect a new WebSocket client."""
        await self.manager.connect(websocket, client_info)
        logging.info(
            f"New WebSocket client connected. Total clients: {self.manager.get_connection_count()}"
        )

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        self.manager.disconnect(websocket)
        logging.info(
            f"WebSocket client disconnected. Total clients: {self.manager.get_connection_count()}"
        )

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a personal message to a specific client."""
        await self.manager.send_personal_message(
            {"type": "message", "content": message}, websocket
        )

    async def broadcast_message(self, message: str):
        """Broadcast a message to all clients."""
        await self.manager.broadcast({"type": "message", "content": message})

    async def notify_timeline_update(self, timeline_data: List[Dict[str, Any]]):
        """Notify all clients of a timeline update."""
        await self.manager.broadcast(
            {
                "type": "timeline_update",
                "data": timeline_data,
                "timestamp": datetime.now().isoformat(),
            }
        )

    async def notify_file_upload(self, filename: str, broll_index: int):
        """Notify all clients of a file upload."""
        await self.manager.send_system_notification(
            "File Uploaded",
            f"Image '{filename}' uploaded for B-roll {broll_index}",
            "success",
        )

    async def notify_processing_start(self, task_name: str):
        """Notify clients that processing has started."""
        await self.manager.send_progress_update(task_name, 0.0, "started")
        await self.manager.send_system_notification(
            "Processing Started", f"Started {task_name}", "info"
        )

    async def notify_processing_progress(
        self, task_name: str, progress: float, status: str
    ):
        """Notify clients of processing progress."""
        await self.manager.send_progress_update(task_name, progress, status)

    async def notify_processing_complete(self, task_name: str):
        """Notify clients that processing is complete."""
        await self.manager.send_progress_update(task_name, 1.0, "completed")
        await self.manager.send_system_notification(
            "Processing Complete", f"Completed {task_name}", "success"
        )

    async def notify_error(self, error_message: str, details: Dict[str, Any] = {}):
        """Notify clients of an error."""
        await self.manager.send_system_notification("Error", error_message, "error")
        await self.manager.send_log_message("error", error_message, details)

    async def handle_client_message(self, websocket: WebSocket, message: str):
        """Handle incoming messages from clients."""
        try:
            data = json.loads(message)
            message_type = data.get("type", "unknown")

            if message_type == "ping":
                await self.manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.now().isoformat()}, websocket
                )

            elif message_type == "get_status":
                await self.manager.send_personal_message(
                    {
                        "type": "status",
                        "connected_clients": self.manager.get_connection_count(),
                        "timestamp": datetime.now().isoformat(),
                    },
                    websocket,
                )

            elif message_type == "subscribe_logs":
                # Client wants to receive log messages
                self.manager.connection_info[websocket]["log_subscription"] = True
                await self.manager.send_personal_message(
                    {"type": "subscription_confirmed", "subscription": "logs"},
                    websocket,
                )

            else:
                await self.manager.send_personal_message(
                    {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                    },
                    websocket,
                )

        except json.JSONDecodeError:
            await self.manager.send_personal_message(
                {"type": "error", "message": "Invalid JSON message"}, websocket
            )
        except Exception as e:
            await self.manager.send_personal_message(
                {"type": "error", "message": f"Error processing message: {str(e)}"},
                websocket,
            )
