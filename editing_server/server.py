#!/usr/bin/env python3
"""
Timeline Editing Server for StoryForge
Visual interface for editing broll_timing.json with B-roll selection and image upload.

Usage: python editing_server/server.py
"""

import os
import json
import shutil
import logging
import webbrowser
import base64
import secrets
import yaml
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import cgi
import time


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
        """Vérifier l'authentification HTTP Basic"""
        auth_config = load_auth_config()

        # Si l'auth est désactivée, on passe
        if not auth_config.get("enabled", False):
            return True

        # Récupérer l'en-tête Authorization
        auth_header = self.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return False

        try:
            # Décoder les credentials
            encoded_credentials = auth_header[6:]  # Enlever "Basic "
            decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = decoded_credentials.split(":", 1)

            # Vérifier les credentials
            correct_username = auth_config.get("username", "admin")
            correct_password = auth_config.get("password", "admin")

            is_correct_username = secrets.compare_digest(username, correct_username)
            is_correct_password = secrets.compare_digest(password, correct_password)

            return is_correct_username and is_correct_password

        except Exception:
            return False

    def send_auth_required(self):
        """Envoyer une réponse 401 avec demande d'authentification"""
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Premontage Server"')
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>401 Unauthorized</h1><p>Authentication required</p>")

    def do_GET(self):
        """Gère les requêtes GET (interface HTML et données JSON)."""
        # Vérifier l'authentification
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
            logging.error(f"Erreur GET {self.path}: {e}")
            self._send_500()

    def do_POST(self):
        """Gère les requêtes POST (upload d'images, modification timeline)."""
        # Vérifier l'authentification
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
            logging.error(f"Erreur POST {self.path}: {e}")
            self._send_500()

    def _serve_interface(self):
        """Sert l'interface HTML principale."""
        print(f"DEBUG SERVEUR: _serve_interface() appelée")

        # Récupérer le nom du projet depuis le chemin temp
        project_name = "unknown"
        if hasattr(self, "broll_timing_file") and self.broll_timing_file:
            # Extraire le nom du projet depuis le chemin temp
            temp_path = self.broll_timing_file.parent
            if temp_path.name == "temp" and temp_path.parent.name != "temp":
                project_name = temp_path.parent.name

        print(f"DEBUG SERVEUR: Nom du projet détecté: {project_name}")

        # Lire le fichier HTML et remplacer le nom du projet
        interface_path = Path(__file__).parent / "interface.html"
        print(f"DEBUG SERVEUR: Chemin du fichier HTML: {interface_path}")

        if not interface_path.exists():
            print(f"DEBUG SERVEUR: ERREUR - Fichier HTML non trouvé: {interface_path}")
            self._send_404()
            return

        print(f"DEBUG SERVEUR: Fichier HTML trouvé, lecture en cours...")
        with open(interface_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        print(f"DEBUG SERVEUR: HTML lu, taille: {len(html_content)} caractères")
        html_content = html_content.replace("{{PROJECT_NAME}}", project_name)
        print(f"DEBUG SERVEUR: Remplacement PROJECT_NAME effectué")

        self._send_response(200, html_content, "text/html")
        print(f"DEBUG SERVEUR: Interface HTML envoyée")

    def _serve_timeline_data(self):
        """Sert les données de timeline en JSON."""
        print(f"DEBUG SERVEUR: _serve_timeline_data() appelée")
        print(f"DEBUG SERVEUR: Chemin broll_timing.json: {self.broll_timing_file}")

        if not self.broll_timing_file.exists():
            print(f"DEBUG SERVEUR: ERREUR - broll_timing.json non trouvé")
            self._send_response(
                404, '{"error": "broll_timing.json not found"}', "application/json"
            )
            return

        print(f"DEBUG SERVEUR: broll_timing.json trouvé, lecture en cours...")
        with open(self.broll_timing_file, "r", encoding="utf-8") as f:
            timeline_data = json.load(f)

        print(f"DEBUG SERVEUR: Timeline chargée, {len(timeline_data)} éléments")
        response_data = json.dumps(timeline_data, indent=2)
        print(
            f"DEBUG SERVEUR: Réponse JSON préparée, taille: {len(response_data)} caractères"
        )

        self._send_response(200, response_data, "application/json")
        print(f"DEBUG SERVEUR: Timeline JSON envoyée")

    def _serve_broll_file(self):
        """Sert les fichiers B-roll pour prévisualisation."""
        file_path = Path(self.path[1:])  # Enlever le '/' initial

        if file_path.exists():
            # Déterminer le type MIME
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
            self.send_header("Content-length", len(data))
            self.end_headers()
            self.wfile.write(data)
        else:
            self._send_404()

    def _serve_project_file(self):
        """Sert les fichiers du dossier projects pour prévisualisation."""
        file_path = Path(self.path[1:])  # Enlever le '/' initial

        if file_path.exists():
            # Déterminer le type MIME
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
            self.send_header("Content-length", len(data))
            self.end_headers()
            self.wfile.write(data)
        else:
            self._send_404()

    def _handle_upload(self):
        """Gère l'upload d'images pour ajouter comme overlay sur une B-roll."""
        try:
            # Parser les données multipart avec cgi.FieldStorage (plus robuste)
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": self.headers["Content-Type"],
                },
            )

            # Récupérer le fichier et l'index
            if "file" not in form or "broll_index" not in form:
                self._send_400("Fichier ou index manquant")
                return

            file_item = form["file"]
            broll_index = int(form["broll_index"].value)

            if not file_item.filename:
                self._send_400("Aucun fichier sélectionné")
                return

            # Sauvegarder l'image dans b-roll/ressources/
            timestamp = int(time.time())
            file_ext = Path(file_item.filename).suffix
            new_filename = f"uploaded_{timestamp}_{broll_index}{file_ext}"
            save_path = self.ressources_dir / new_filename

            with open(save_path, "wb") as f:
                f.write(file_item.file.read())

            # Mettre à jour broll_timing.json
            with open(self.broll_timing_file, "r", encoding="utf-8") as f:
                timeline_data = json.load(f)

            if 0 <= broll_index < len(timeline_data):
                # Ajouter le champ image SANS remplacer la broll
                timeline_data[broll_index]["image"] = f"ressources/{new_filename}"

                with open(self.broll_timing_file, "w", encoding="utf-8") as f:
                    json.dump(timeline_data, f, indent=2, ensure_ascii=False)

                response = {
                    "success": True,
                    "message": f"Image ajoutée par-dessus la B-roll {broll_index}",
                    "new_path": f"ressources/{new_filename}",
                }
                self._send_response(200, json.dumps(response), "application/json")
            else:
                self._send_400("Index de B-roll invalide")

        except Exception as e:
            logging.error(f"Erreur upload: {e}")
            self._send_500()

    def _handle_timeline_update(self):
        """Gère les mises à jour de la timeline."""
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode("utf-8"))

            # Sauvegarder la timeline modifiée
            with open(self.broll_timing_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            response = {"success": True, "message": "Timeline mise à jour"}
            self._send_response(200, json.dumps(response), "application/json")

        except Exception as e:
            logging.error(f"Erreur mise à jour timeline: {e}")
            self._send_500()

    def _send_response(self, code, data, content_type):
        """Envoie une réponse HTTP."""
        self.send_response(code)
        self.send_header("Content-type", content_type)
        self.send_header(
            "Content-length", len(data.encode() if isinstance(data, str) else data)
        )
        self.end_headers()

        if isinstance(data, str):
            self.wfile.write(data.encode())
        else:
            self.wfile.write(data)

    def _send_404(self):
        """Envoie une erreur 404."""
        self._send_response(404, "Not Found", "text/plain")

    def _send_400(self, message):
        """Envoie une erreur 400."""
        self._send_response(400, message, "text/plain")

    def _send_500(self):
        """Envoie une erreur 500."""
        self._send_response(500, "Internal Server Error", "text/plain")

    def log_message(self, format, *args):
        """Supprime les logs automatiques du serveur."""
        pass


def start_premontage_server(config=None, port=47393):
    """
    Démarre le serveur de prémontage.

    Args:
        config (dict): Configuration du projet (pour le chemin temp)
        port (int): Port du serveur (défaut: 47393)
    """
    # Déterminer le chemin du fichier broll_timing.json
    if config and "paths" in config and "temp" in config["paths"]:
        temp_path = Path(config["paths"]["temp"])
    else:
        temp_path = Path("temp")

    broll_timing_file = temp_path / "broll_timing.json"

    if not broll_timing_file.exists():
        print(f"❌ Erreur: {broll_timing_file} non trouvé")
        print(
            "   Exécutez d'abord: python exponential_video.py --vectorbroll NOM_PROJET"
        )
        return False

    try:
        # Créer le dossier ressources
        ressources_dir = Path("b-roll/ressources")
        ressources_dir.mkdir(exist_ok=True)

        # Start the server
        server = HTTPServer(
            ("0.0.0.0", port),
            lambda *args, **kwargs: TimelineEditingHandler(
                *args, config=config, **kwargs
            ),
        )

        print(f"🎬 Serveur de prémontage démarré sur http://0.0.0.0:{port}")

        # Afficher l'IP publique si disponible
        try:
            import requests

            response = requests.get(
                "http://leader-referencement.com/get_current_ip.php", timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                public_ip = data.get("ip")
                if public_ip:
                    print(
                        f"🌐 Accessible via: http://localhost:{port} (local) ou http://{public_ip}:{port} (externe)"
                    )
                else:
                    print(
                        f"🌐 Accessible via: http://localhost:{port} (local) ou http://votre-ip:{port} (externe)"
                    )
            else:
                print(
                    f"🌐 Accessible via: http://localhost:{port} (local) ou http://votre-ip:{port} (externe)"
                )
        except Exception:
            print(
                f"🌐 Accessible via: http://localhost:{port} (local) ou http://votre-ip:{port} (externe)"
            )

        # Afficher l'état de l'authentification
        auth_config = load_auth_config()
        if auth_config.get("enabled", False):
            print(
                f"🔒 Authentification: ACTIVÉE (utilisateur: {auth_config.get('username', 'admin')})"
            )
            print("ℹ️  Pour désactiver: config.yml → dashboard.auth.enabled: false")
        else:
            print("🔓 Authentification: DÉSACTIVÉE")
            print("ℹ️  Pour activer: config.yml → dashboard.auth.enabled: true")

        print("📝 Interface d'édition de timeline ouverte dans le navigateur")
        print("⏹️  Appuyez sur Ctrl+C pour arrêter le serveur")

        # L'ouverture du navigateur est maintenant gérée par le dashboard
        print("🌐 Interface accessible via le dashboard (bouton 'Open Prémontage')")

        # Start the server
        server.serve_forever()

    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        return True
    except Exception as e:
        print(f"❌ Error starting server: {e}")
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
    start_timeline_server()
    start_premontage_server()
