#!/usr/bin/env python3
"""
Script de lancement pour le Dashboard Video Pipeline
Mode production uniquement - pas de mock
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Vérifier que les dépendances sont installées"""
    try:
        import fastapi
        import uvicorn
        import websockets
        print("✅ Toutes les dépendances sont installées")
        return True
    except ImportError as e:
        print(f"❌ Dépendance manquante: {e}")
        print("💡 Installez les dépendances avec: pip install -r requirements.txt")
        return False

def check_project_structure():
    """Vérifier que la structure du projet est correcte"""
    dashboard_dir = Path(__file__).parent
    project_root = dashboard_dir.parent
    
    required_files = [
        project_root / "exponential_video.py",
        project_root / "config.yml",
        project_root / "projects"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not file_path.exists():
            missing_files.append(str(file_path))
    
    if missing_files:
        print("❌ Fichiers/dossiers manquants dans le projet:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ Structure du projet valide")
    return True

def start_server():
    """Démarrer le serveur FastAPI"""
    print("🚀 Démarrage du Dashboard Video Pipeline")
    print("📍 Mode: Production (intégration CLI réelle)")
    
    dashboard_dir = Path(__file__).parent
    os.chdir(dashboard_dir)
    
    # Lancer le serveur avec uvicorn
    cmd = [
        sys.executable, "-m", "uvicorn",
        "pipeline_server:app",
        "--host", "0.0.0.0",
        "--port", "47392",
        "--reload"
    ]
    
    print(f"🌐 Dashboard: http://localhost:47392")
    print(f"📡 WebSocket: ws://localhost:47392/ws")
    print("🔄 Auto-reload activé")
    print("⚠️  Utilisez Ctrl+C pour arrêter le serveur")
    print("-" * 50)
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Serveur arrêté")

def main():
    print("🎬 Dashboard Video Pipeline - Initialisation")
    print("=" * 50)
    
    # Vérifications préliminaires
    if not check_dependencies():
        sys.exit(1)
    
    if not check_project_structure():
        sys.exit(1)
    
    # Démarrer le serveur
    start_server()

if __name__ == "__main__":
    main()
