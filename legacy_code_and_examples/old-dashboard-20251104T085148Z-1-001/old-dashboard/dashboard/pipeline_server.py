#!/usr/bin/env python3
"""
Serveur backend pour le Dashboard Video Pipeline
Intégration entre l'interface web et le CLI exponential_video.py
"""

import os
import sys
import json
import asyncio
import subprocess
import signal
import secrets
import yaml
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
CLI_SCRIPT = PROJECT_ROOT / "exponential_video.py"
PROJECTS_DIR = PROJECT_ROOT / "projects"

app = FastAPI(title="Video Pipeline Dashboard API", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    """Démarrer les tâches en arrière-plan"""
    if DYNDNS_CONFIG['enabled']:
        print("🌐 Démarrage du service DynDNS intégré")
        asyncio.create_task(dyndns_background_task())

# Fichier de persistance des tâches
TASKS_FILE = PROJECT_ROOT / "tasks_history.json"

# Configuration d'authentification
security = HTTPBasic()

def load_auth_config():
    """Charger la configuration d'authentification depuis config.yml"""
    config_file = PROJECT_ROOT / "config.yml"
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config.get('dashboard', {}).get('auth', {})
    return {}

AUTH_CONFIG = load_auth_config()

# Configuration DynDNS
DYNDNS_CONFIG = {
    'enabled': True,
    'server_url': 'http://leader-referencement.com/update_ip.php',
    'secret_key': 'votre_secret_key_123',
    'interval': 20  # 20 secondes
}

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Vérifier les credentials HTTP Basic Auth"""
    # Si l'auth est désactivée, on passe
    if not AUTH_CONFIG.get('enabled', False):
        return None
    
    # Vérifier username et password
    correct_username = AUTH_CONFIG.get('username', 'admin')
    correct_password = AUTH_CONFIG.get('password', 'admin')
    
    is_correct_username = secrets.compare_digest(credentials.username, correct_username)
    is_correct_password = secrets.compare_digest(credentials.password, correct_password)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Servir les fichiers statiques (CSS, JS) - APRÈS les routes API
# app.mount("/static", StaticFiles(directory=str(Path(__file__).parent)), name="static")

@dataclass
class Task:
    id: int
    project: str
    steps: List[str]
    audio_mode: str
    status: str  # queued, running, done, failed, cancelled
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    commands: List[str] = None
    current_command: int = 0
    logs: List[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.commands is None:
            self.commands = []
        if self.logs is None:
            self.logs = []

def save_tasks():
    """Sauvegarder les tâches dans un fichier JSON"""
    try:
        tasks_data = {}
        for task_id, task in tasks.items():
            # Convertir la tâche en dictionnaire, en excluant les processus
            task_dict = asdict(task)
            tasks_data[str(task_id)] = task_dict
        
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Tâches sauvegardées: {len(tasks_data)} tâches dans {TASKS_FILE}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde des tâches: {e}")

def load_tasks():
    """Charger les tâches depuis le fichier JSON"""
    global task_counter
    try:
        if not TASKS_FILE.exists():
            print("📝 Aucun fichier de tâches existant, démarrage avec une liste vide")
            task_counter = 0  # Initialiser le compteur
            return {}
        
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)
        
        loaded_tasks = {}
        max_id = 0
        
        for task_id_str, task_dict in tasks_data.items():
            task_id = int(task_id_str)
            # Recréer l'objet Task à partir du dictionnaire
            task = Task(**task_dict)
            loaded_tasks[task_id] = task
            max_id = max(max_id, task_id)
        
        # Mettre à jour le compteur de tâches
        task_counter = max_id
        
        print(f"📂 Tâches chargées: {len(loaded_tasks)} tâches depuis {TASKS_FILE}")
        return loaded_tasks
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement des tâches: {e}")
        return {}

# État global
tasks: Dict[int, Task] = load_tasks()  # Charger les tâches au démarrage (task_counter mis à jour dans load_tasks)
active_websockets: List[WebSocket] = []
# Dictionnaire séparé pour les processus (non sérialisable)
running_processes: Dict[int, Any] = {}

# ========================================
# Routes statiques
# ========================================

@app.get("/")
async def dashboard(user: str = Depends(get_current_user)):
    """Servir le dashboard principal"""
    dashboard_file = Path(__file__).parent / "index.html"
    if dashboard_file.exists():
        return FileResponse(dashboard_file)
    else:
        return HTMLResponse("<h1>Dashboard Video Pipeline</h1><p>Fichier index.html non trouvé</p>")

@app.get("/dashboard.js")
async def dashboard_js(user: str = Depends(get_current_user)):
    """Servir le fichier JavaScript"""
    js_file = Path(__file__).parent / "dashboard.js"
    if js_file.exists():
        return FileResponse(js_file, media_type="application/javascript")
    else:
        raise HTTPException(status_code=404, detail="dashboard.js non trouvé")

@app.get("/style.css")
async def dashboard_css():
    """Servir le fichier CSS (si nécessaire)"""
    css_file = Path(__file__).parent / "style.css"
    if css_file.exists():
        return FileResponse(css_file, media_type="text/css")
    else:
        # CSS intégré dans le HTML, donc pas d'erreur
        return HTMLResponse("/* CSS intégré dans index.html */", media_type="text/css")

# ========================================
# API Projets
# ========================================

@app.get("/api/projects")
async def get_projects(user: str = Depends(get_current_user)):
    """Récupérer la liste des projets disponibles"""
    try:
        if not PROJECTS_DIR.exists():
            return {"projects": [], "error": f"Dossier projects non trouvé: {PROJECTS_DIR}"}
        
        projects = []
        for item in PROJECTS_DIR.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                projects.append(item.name)
        
        projects.sort()
        return {"projects": projects}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture projets: {str(e)}")

@app.get("/api/projects/{project_name}/scripts")
async def get_project_scripts(project_name: str):
    """Récupérer les scripts I1, I2, I3 et ori_vid.txt d'un projet"""
    try:
        project_dir = PROJECTS_DIR / project_name
        if not project_dir.exists():
            raise HTTPException(status_code=404, detail=f"Projet non trouvé: {project_name}")
        
        scripts = {}
        
        # Scripts I1, I2, I3 dans temp/
        temp_dir = project_dir / "temp"
        for script_name in ["i1.txt", "i2.txt", "i3.txt"]:
            script_file = temp_dir / script_name
            if script_file.exists():
                scripts[script_name.replace('.txt', '')] = script_file.read_text(encoding='utf-8')
            else:
                scripts[script_name.replace('.txt', '')] = ""
        
        # Fichier input.txt
        input_file = project_dir / "input.txt"
        if input_file.exists():
            scripts['input'] = input_file.read_text(encoding='utf-8')
        else:
            scripts['input'] = ""
        
        # Transcript original (pour compatibilité)
        ori_file = project_dir / "ori_vid.txt"
        if ori_file.exists():
            scripts['ori'] = ori_file.read_text(encoding='utf-8')
        else:
            scripts['ori'] = ""
        
        return {"scripts": scripts}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture scripts: {str(e)}")

@app.get("/api/projects/{project_name}/audio-status")
async def get_audio_status(project_name: str, user: str = Depends(get_current_user)):
    """Vérifier si tous les audios sont générés"""
    try:
        project_dir = PROJECTS_DIR / project_name
        if not project_dir.exists():
            raise HTTPException(status_code=404, detail=f"Projet non trouvé: {project_name}")
        
        temp_dir = project_dir / "temp"
        audio_dir = temp_dir / "audio"
        
        if not audio_dir.exists():
            return {"audioComplete": False, "count": 0, "expected": 0}
        
        # Compter les fichiers audio MP3
        audio_files = list(audio_dir.glob("*.mp3"))
        audio_count = len(audio_files)
        
        # Estimer le nombre attendu basé sur i3.txt (nombre de phrases)
        i3_file = temp_dir / "i3.txt"
        expected_count = 0
        if i3_file.exists():
            content = i3_file.read_text(encoding='utf-8')
            # Compter les phrases (lignes non vides)
            expected_count = len([line for line in content.split('\n') if line.strip()])
        
        return {
            "audioComplete": audio_count >= expected_count and expected_count > 0,
            "count": audio_count,
            "expected": expected_count
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur vérification audio: {str(e)}")

@app.get("/api/projects/{project_name}/broll-status")
async def get_broll_status(project_name: str, user: str = Depends(get_current_user)):
    """Vérifier si broll_timing.json contient 50 bullets avec broll"""
    try:
        project_dir = PROJECTS_DIR / project_name
        if not project_dir.exists():
            raise HTTPException(status_code=404, detail=f"Projet non trouvé: {project_name}")
        
        temp_dir = project_dir / "temp"
        broll_file = temp_dir / "broll_timing.json"
        
        if not broll_file.exists():
            return {"brollComplete": False, "count": 0, "expected": 50}
        
        import json
        with open(broll_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Compter les bullets avec broll et broll2
        bullets_with_broll = 0
        for bullet in data:  # data est directement la liste, pas data.get('bullets', [])
            if bullet.get('broll') and bullet.get('broll2'):
                bullets_with_broll += 1
        
        return {
            "brollComplete": bullets_with_broll >= 50,
            "count": bullets_with_broll,
            "expected": 50
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur vérification B-roll: {str(e)}")

# ========================================
# API Tâches
# ========================================

@app.get("/api/tasks")
async def get_tasks():
    """Récupérer toutes les tâches"""
    return {"tasks": [asdict(task) for task in tasks.values()]}

@app.post("/api/tasks")
async def create_task(task_data: dict, user: str = Depends(get_current_user)):
    """Créer une nouvelle tâche"""
    global task_counter
    
    try:
        task_counter += 1
        
        # Construire les commandes CLI
        commands = build_cli_commands(
            project=task_data['project'],
            steps=task_data['steps'],
            audio_mode=task_data['audio_mode'],
            use_broll=task_data.get('use_broll', False)
        )
        
        # Créer la tâche
        task = Task(
            id=task_counter,
            project=task_data['project'],
            steps=task_data['steps'],
            audio_mode=task_data['audio_mode'],
            status='queued',
            created_at=datetime.now().isoformat(),
            commands=commands
        )
        
        tasks[task.id] = task
        
        # Sauvegarder après création (ne pas faire planter si erreur)
        try:
            save_tasks()
        except Exception as save_error:
            print(f"⚠️ Impossible de sauvegarder les tâches: {save_error}")
        
        # Notifier via WebSocket
        await broadcast_task_update(task)
        
        # Démarrer l'exécution si c'est la seule tâche
        await process_queue()
        
        return {"task_id": task.id, "status": "created"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur création tâche: {str(e)}")

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int):
    """Supprimer une tâche"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    
    task = tasks[task_id]
    if task.status == 'running':
        raise HTTPException(status_code=400, detail="Impossible de supprimer une tâche en cours")
    
    del tasks[task_id]
    save_tasks()  # Sauvegarder après suppression
    await broadcast_message(f"Tâche #{task_id} supprimée")
    
    return {"status": "deleted"}

@app.post("/api/tasks/clear-done")
async def clear_done_tasks():
    """Supprimer toutes les tâches terminées"""
    removed = 0
    for task_id in list(tasks.keys()):
        if tasks[task_id].status in ['done', 'failed', 'cancelled']:
            del tasks[task_id]
            removed += 1
    
    if removed > 0:
        save_tasks()  # Sauvegarder après suppression groupée
    
    await broadcast_message(f"{removed} tâche(s) terminée(s) supprimée(s)")
    
    # Envoyer la liste mise à jour des tâches
    await broadcast_tasks_update()
    
    return {"removed": removed}

@app.post("/api/premontage/{project_name}")
async def launch_premontage_immediate(project_name: str, user: str = Depends(get_current_user)):
    """Lancer le prémontage immédiatement (hors queue)"""
    try:
        venv_python = "./venv_py312/bin/python"
        script = "exponential_video.py"
        
        # Commande prémontage
        command = f"cd \"{PROJECT_ROOT}\" && {venv_python} {script} --premontage {project_name}"
        
        # Lancer la commande de manière asynchrone (fire and forget)
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=PROJECT_ROOT
        )
        
        # Logger le lancement
        print(f"🎬 Prémontage lancé immédiatement pour {project_name} (PID: {process.pid})")
        await broadcast_message(f"🎬 Prémontage {project_name} lancé immédiatement (hors queue)")
        
        return {"status": "launched", "project": project_name, "pid": process.pid}
        
    except Exception as e:
        print(f"❌ Erreur lancement prémontage {project_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lancement prémontage: {str(e)}")

@app.post("/api/kill-exponential-video")
async def kill_exponential_video_processes(user: str = Depends(get_current_user)):
    """Tuer tous les processus du pipeline (exponential_video) uniquement"""
    try:
        import subprocess
        import signal
        
        killed_processes = []
        total_killed = 0
        
        # Commandes pour trouver et tuer les processus (SANS le dashboard ni le prémontage)
        kill_commands = [
            # Tuer tous les processus exponential_video.py (pipeline)
            "pkill -f 'exponential_video.py'"
        ]
        
        for cmd in kill_commands:
            try:
                # Exécuter la commande kill
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    process_name = cmd.split("'")[1] if "'" in cmd else cmd
                    killed_processes.append(process_name)
                    print(f"🔪 Processus tués: {process_name}")
                    
            except Exception as e:
                print(f"⚠️ Erreur lors de l'exécution de {cmd}: {e}")
        
        # Tuer aussi les processus trackés dans running_processes
        for task_id, process in list(running_processes.items()):
            try:
                if process and process.returncode is None:  # Processus encore en vie
                    process.terminate()
                    await asyncio.sleep(0.5)  # Attendre un peu
                    if process.returncode is None:  # Toujours en vie, forcer
                        process.kill()
                    total_killed += 1
                    killed_processes.append(f"Task #{task_id}")
                    print(f"🔪 Processus tâche #{task_id} terminé")
            except Exception as e:
                print(f"⚠️ Erreur lors de l'arrêt du processus tâche #{task_id}: {e}")
        
        # Nettoyer le dictionnaire des processus en cours
        running_processes.clear()
        
        # Mettre à jour le statut des tâches en cours
        for task in tasks.values():
            if task.status == 'running':
                task.status = 'cancelled'
                task.finished_at = datetime.now().isoformat()
        
        save_tasks()
        await broadcast_tasks_update()
        
        details = ", ".join(killed_processes) if killed_processes else "Aucun processus trouvé"
        total_killed += len([p for p in killed_processes if not p.startswith("Task")])
        
        await broadcast_message(f"🔪 Tous les processus ont été arrêtés: {details}")
        
        return {
            "killed": total_killed,
            "details": details,
            "processes": killed_processes
        }
        
    except Exception as e:
        print(f"❌ Erreur lors de l'arrêt des processus: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur arrêt processus: {str(e)}")

@app.post("/api/kill-premontage")
async def kill_premontage(user: str = Depends(get_current_user)):
    """Tuer uniquement le serveur de prémontage (pas le dashboard)."""
    try:
        import subprocess
        killed = 0
        details = []
        
        # Tuer le serveur prémontage standalone
        cmd1 = "pkill -f 'src/premontage/server.py'"
        res1 = subprocess.run(cmd1, shell=True, capture_output=True, text=True)
        if res1.returncode == 0:
            killed += 1
            details.append('src/premontage/server.py')
            print("🔪 Serveur prémontage (server.py) tué")
        
        # Tuer les processus exponential_video lancés avec --premontage
        cmd2 = "pkill -f 'exponential_video.py.*--premontage'"
        res2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
        if res2.returncode == 0:
            killed += 1
            details.append('exponential_video.py --premontage')
            print("🔪 Prémontage lancé via exponential_video tué")
        await broadcast_message("🔪 Serveur prémontage arrêté")
        return {"killed": killed, "details": ", ".join(details) if details else "Aucun processus trouvé"}
    except Exception as e:
        print(f"❌ Erreur arrêt prémontage: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur arrêt prémontage: {str(e)}")

def simplify_process_line(line: str) -> str:
    """Simplifier une ligne de processus en ne gardant que la commande lisible."""
    import shlex
    import os
    
    line = line.rstrip("\n")
    
    # Trouver le début de la commande (1er '/')
    try:
        start = line.index('/')
    except ValueError:
        # pas de chemin → renvoyer la ligne telle quelle
        return line
    
    cmd = line[start:]  # "/opt/homebrew/.../Python exponential_video.py --premontage project-11"
    parts = shlex.split(cmd)  # sépare proprement (gère quotes/escapes)
    if parts:
        parts[0] = os.path.basename(parts[0])  # "Python"
    return " ".join(parts)

@app.post("/api/save-input-text")
async def save_input_text(request: dict, user: str = Depends(get_current_user)):
    """Save input text to a project's input.txt file"""
    try:
        project = request.get('project')
        input_text = request.get('input_text')
        filename = request.get('filename', 'input.txt')  # Default to input.txt

        if not project or not input_text:
            raise HTTPException(status_code=400, detail="Project and input_text required")

        # Create project directory if it doesn't exist
        project_dir = Path(f"projects/{project}")
        project_dir.mkdir(parents=True, exist_ok=True)

        # Save input text to specified filename
        input_file = project_dir / filename
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(input_text)

        logging.info(f"✅ Input text saved to {input_file}")

        return {
            "success": True,
            "message": f"Input text saved to project {project}",
            "file": str(input_file)
        }

    except Exception as e:
        logging.error(f"Error saving input text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/launch-pipeline")
async def launch_pipeline(request: dict, user: str = Depends(get_current_user)):
    """Launch pipeline with specific steps"""
    try:
        project = request.get('project')
        steps = request.get('steps', [])
        language = request.get('language', 'french')
        audio_mode = request.get('audio_mode', 'gemini_tts')

        if not project:
            raise HTTPException(status_code=400, detail="Project name required")

        if not steps:
            raise HTTPException(status_code=400, detail="At least one step required")

        # Create a new task
        global task_counter
        task_counter += 1
        task_id = task_counter

        # Build command based on steps
        if 'script' in steps or 'audio' in steps:
            # Use the new CLI module for script and audio generation
            cmd = ["./venv_py312/bin/python", "module_script_and_voice.py"]
            cmd.extend(["--project", project])
            cmd.extend(["--language", language])
            
            # Input file path is automatically deduced from project name
            
            if 'script' in steps and 'audio' in steps:
                # Both script and audio - default behavior
                pass
            elif 'script' in steps:
                cmd.append("--script-only")
            elif 'audio' in steps:
                cmd.append("--voice-only")
        else:
            # Use exponential_video.py for other steps (rush, movie, etc.)
            cmd = ["./venv_py312/bin/python", "exponential_video.py"]
            
            if 'rush' in steps:
                cmd.append('-r')
            if 'movie' in steps:
                cmd.append('-m')
                
            cmd.append(project)

        # Create task
        task = Task(
            id=task_id,
            project=project,
            commands=[" ".join(cmd)],  # Convert to list format
            status="pending",
            created_at=datetime.now().isoformat(),
            steps=steps,
            audio_mode=audio_mode
        )
        
        tasks[task_id] = task

        # Start the task in background
        asyncio.create_task(execute_task(task))

        print(f"✅ Pipeline task #{task_id} created for project {project}")

        return {
            "success": True,
            "message": f"Pipeline launched for project {project}",
            "task_id": task_id,
            "command": " ".join(cmd)
        }

    except Exception as e:
        print(f"❌ Error launching pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/show-processes")
async def show_processes(user: str = Depends(get_current_user)):
    """Lister les processus pertinents (exponential_video, prémontage, dashboard)."""
    try:
        import subprocess
        def run(cmd: str) -> str:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            out = result.stdout.strip()
            if out and out != '—':
                # Simplifier chaque ligne de processus
                lines = out.split('\n')
                simplified_lines = [simplify_process_line(line) for line in lines]
                return '\n'.join(simplified_lines)
            return '—'
        
        exp = run("ps aux | grep -i 'exponential_video.py' | grep -v grep")
        pre1 = run("ps aux | grep -i 'src/premontage/server.py' | grep -v grep")
        pre2 = run("ps aux | egrep -i 'exponential_video.py.*--premontage' | grep -v grep")
        pre = '\n'.join([p for p in [pre1, pre2] if p and p != '—']) or '—'
        dash = run("ps aux | grep -i 'dashboard/server.py' | grep -v grep")
        return {"exponential_video": exp, "premontage": pre, "dashboard": dash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur show-processes: {str(e)}")

@app.get("/api/tasks/{task_id}/logs")
async def get_task_logs(task_id: int):
    """Récupérer les logs détaillés d'une tâche"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    
    task = tasks[task_id]
    return {
        "task_id": task_id,
        "project": task.project,
        "status": task.status,
        "commands": task.commands,
        "current_command": task.current_command,
        "logs": task.logs,
        "error": task.error,
        "created_at": task.created_at,
        "started_at": task.started_at,
        "finished_at": task.finished_at
    }

@app.post("/api/tasks/{task_id}/stop")
async def stop_task(task_id: int, user: str = Depends(get_current_user)):
    """Arrêter une tâche en cours (CTRL+C)"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    
    task = tasks[task_id]
    
    # Vérifier si la tâche est déjà terminée
    if task.status in ['done', 'failed', 'cancelled']:
        await broadcast_message(f"ℹ️ Tâche #{task_id} déjà terminée (statut: {task.status})")
        return {"message": f"Tâche déjà terminée avec le statut: {task.status}"}
    
    if task.status != 'running':
        raise HTTPException(status_code=400, detail="La tâche n'est pas en cours d'exécution")
    
    # Marquer la tâche comme annulée
    task.status = 'cancelled'
    task.finished_at = datetime.now().isoformat()
    task.error = "Tâche interrompue par l'utilisateur (CTRL+C)"
    # Sauvegarder après modification du statut (non bloquant)
    try:
        save_tasks()
    except Exception:
        pass  # Ne pas faire planter l'arrêt de tâche
    
    await broadcast_message(f"🛑 Arrêt de la tâche #{task_id}...")
    
    # Tuer le processus réel si il existe encore
    if task_id in running_processes:
        process = running_processes[task_id]
        try:
            # Méthode 1: SIGINT au groupe de processus entier
            try:
                os.killpg(process.pid, signal.SIGINT)
                await broadcast_message(f"🛑 Signal SIGINT envoyé au groupe de processus #{task_id}")
            except (ProcessLookupError, OSError):
                # Fallback: SIGINT au processus principal
                process.send_signal(signal.SIGINT)
                await broadcast_message(f"🛑 Signal SIGINT envoyé au processus #{task_id}")
            
            # Attendre un délai court pour terminaison propre
            try:
                await asyncio.wait_for(process.wait(), timeout=2.0)
                await broadcast_message(f"✅ Processus de la tâche #{task_id} terminé proprement")
            except asyncio.TimeoutError:
                # Méthode 2: SIGTERM au groupe de processus
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                    await broadcast_message(f"💀 Signal SIGTERM envoyé au groupe #{task_id}")
                    await asyncio.wait_for(process.wait(), timeout=2.0)
                    await broadcast_message(f"✅ Processus terminé avec SIGTERM")
                except asyncio.TimeoutError:
                    # Méthode 3: SIGKILL brutal au groupe de processus
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                        await broadcast_message(f"💀💀 SIGKILL envoyé au groupe #{task_id}")
                    except (ProcessLookupError, OSError):
                        # Fallback: kill brutal du processus principal
                        process.kill()
                        await broadcast_message(f"💀💀 Processus #{task_id} tué brutalement")
            
            # Nettoyer la référence
            del running_processes[task_id]
                
        except ProcessLookupError:
            await broadcast_message(f"⚠️ Processus de la tâche #{task_id} déjà terminé")
            if task_id in running_processes:
                del running_processes[task_id]
        except Exception as e:
            await broadcast_message(f"❌ Erreur lors de l'arrêt du processus #{task_id}: {str(e)}")
    else:
        await broadcast_message(f"⚠️ Aucun processus actif trouvé pour la tâche #{task_id}")
        # Si aucun processus actif et que la tâche était encore en running,
        # elle s'est probablement terminée entre temps
        if task.status == 'cancelled':
            await broadcast_message(f"ℹ️ Tâche #{task_id} semble s'être terminée naturellement")
    
    await broadcast_message(f"🛑 Tâche #{task_id} marquée comme interrompue")
    await broadcast_task_update(task)
    
    return {"status": "stopped"}

# ========================================
# WebSocket pour logs temps réel
# ========================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        # Envoyer l'état initial
        await websocket.send_json({
            "type": "tasks_update",
            "tasks": [asdict(task) for task in tasks.values()]
        })
        
        # Maintenir la connexion
        while True:
            data = await websocket.receive_text()
            # Echo pour maintenir la connexion
            await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        active_websockets.remove(websocket)

async def broadcast_message(message: str, msg_type: str = "log"):
    """Diffuser un message à tous les clients connectés"""
    if not active_websockets:
        return
    
    data = {
        "type": msg_type,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    for websocket in active_websockets[:]:  # Copie pour éviter les modifications concurrentes
        try:
            await websocket.send_json(data)
        except:
            active_websockets.remove(websocket)

async def broadcast_task_update(task: Task):
    """Diffuser une mise à jour de tâche"""
    data = {
        "type": "task_update",
        "task": asdict(task)
    }
    
    for websocket in active_websockets[:]:
        try:
            await websocket.send_json(data)
        except:
            active_websockets.remove(websocket)

async def broadcast_tasks_update():
    """Diffuser la liste complète des tâches"""
    data = {
        "type": "tasks_update",
        "tasks": [asdict(task) for task in tasks.values()]
    }
    
    for websocket in active_websockets[:]:
        try:
            await websocket.send_json(data)
        except:
            active_websockets.remove(websocket)

# ========================================
# Exécution des tâches
# ========================================

def build_cli_commands(project: str, steps: List[str], audio_mode: str, use_broll: bool = False) -> List[str]:
    """Construire les commandes CLI à partir des paramètres"""
    commands = []
    
    # Commande de base avec cd + activation venv + python
    venv_python = "./venv_py312/bin/python"
    script = "exponential_video.py"
    
    # Étapes individuelles
    if 'get_ori' in steps:
        cmd = f"cd \"{PROJECT_ROOT}\" && {venv_python} {script} --get_ori https://www.youtube.com/watch?v=VIDEO_ID {project}"
        commands.append(cmd)
    
    if 'script' in steps:
        cmd = f"cd \"{PROJECT_ROOT}\" && {venv_python} {script} -s {project}"
        commands.append(cmd)
    
    if 'audio' in steps:
        audio_flag = {'gemini_tts': '-ag', 'openai_tts': '-a', 'heygen': '-r'}[audio_mode]
        cmd = f"cd \"{PROJECT_ROOT}\" && {venv_python} {script} {audio_flag} {project}"
        commands.append(cmd)
    
    if 'vectorbroll' in steps:
        cmd = f"cd \"{PROJECT_ROOT}\" && {venv_python} {script} --vectorbroll {project}"
        commands.append(cmd)
    
    if 'premontage' in steps:
        cmd = f"cd \"{PROJECT_ROOT}\" && {venv_python} {script} --premontage {project}"
        commands.append(cmd)
    
    if 'compile' in steps:
        use_broll_flag = ' --usebroll' if use_broll else ''
        cmd = f"cd \"{PROJECT_ROOT}\" && {venv_python} {script} -m{use_broll_flag} {project}"
        commands.append(cmd)
    
    return commands

async def process_queue():
    """Traiter la file d'attente des tâches"""
    # Vérifier s'il y a une tâche en cours
    running_tasks = [t for t in tasks.values() if t.status == 'running']
    if running_tasks:
        return  # Une tâche est déjà en cours
    
    # Chercher la prochaine tâche en attente
    queued_tasks = [t for t in tasks.values() if t.status == 'queued']
    if not queued_tasks:
        return  # Pas de tâche en attente
    
    # Prendre la plus ancienne
    next_task = min(queued_tasks, key=lambda t: t.created_at)
    
    # Lancer l'exécution
    asyncio.create_task(execute_task(next_task))

async def execute_task(task: Task):
    """Exécuter une tâche"""
    try:
        task.status = 'running'
        task.started_at = datetime.now().isoformat()
        save_tasks()  # Sauvegarder au démarrage
        await broadcast_task_update(task)
        await broadcast_message(f"▶️ Démarrage tâche #{task.id}: {task.project}")
        
        # Exécuter chaque commande
        for i, command in enumerate(task.commands):
            task.current_command = i
            await broadcast_task_update(task)
            await broadcast_message(f"$ {command}")
            
            # Exécuter la commande avec un nouveau groupe de processus
            # Parse command into list for create_subprocess_exec
            import shlex
            cmd_list = shlex.split(command)
            
            process = await asyncio.create_subprocess_exec(
                *cmd_list,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=PROJECT_ROOT,
                preexec_fn=os.setsid  # Créer un nouveau groupe de processus
            )
            
            # Stocker la référence du processus dans le dictionnaire séparé
            running_processes[task.id] = process
            await broadcast_task_update(task)
            
            # Lire la sortie en temps réel
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                log_line = line.decode('utf-8', errors='replace').strip()
                if log_line:
                    task.logs.append(log_line)
                    await broadcast_message(log_line)
            
            # Attendre la fin du processus
            await process.wait()
            
            # Nettoyer la référence du processus
            if task.id in running_processes:
                del running_processes[task.id]
            
            if process.returncode != 0:
                # Vérifier si c'est un arrêt demandé par l'utilisateur
                if task.status == 'cancelled':
                    await broadcast_message(f"🛑 Tâche #{task.id} interrompue avec succès")
                    return  # Sortir sans erreur
                raise subprocess.CalledProcessError(process.returncode, command)
        
        # Succès
        task.status = 'done'
        task.finished_at = datetime.now().isoformat()
        save_tasks()  # Sauvegarder après succès
        await broadcast_message(f"✅ Tâche #{task.id} terminée avec succès")
    
    except Exception as e:
        # Erreur
        task.status = 'failed'
        task.finished_at = datetime.now().isoformat()
        task.error = str(e)
        save_tasks()  # Sauvegarder après échec
        await broadcast_message(f"❌ Tâche #{task.id} échouée: {str(e)}")
    
    finally:
        # Nettoyer la référence du processus
        if task.id in running_processes:
            del running_processes[task.id]
        await broadcast_task_update(task)
        # Continuer avec la tâche suivante
        await process_queue()

# ========================================
# DynDNS intégré
# ========================================

async def get_known_ip():
    """Récupérer l'IP connue par leader-referencement"""
    try:
        response = await asyncio.to_thread(
            requests.get, 'http://leader-referencement.com/get_current_ip.php', timeout=10
        )
        data = response.json()
        return data.get('ip', 'INCONNUE')
    except:
        return 'ERREUR'

async def update_dyndns():
    """Mettre à jour l'IP via DynDNS"""
    if not DYNDNS_CONFIG['enabled']:
        return
    
    try:
        # Obtenir notre IP publique réelle
        ip_response = await asyncio.to_thread(
            requests.get, 'https://api.ipify.org', timeout=10
        )
        current_ip = ip_response.text.strip()
        
        # Obtenir l'IP connue par leader-referencement
        known_ip = await get_known_ip()
        
        print(f"🌐 IP actuelle réelle : {current_ip}")
        print(f"📡 IP connue par leader-referencement : {known_ip}")
        
        # Mettre à jour seulement si différente
        if current_ip != known_ip:
            update_url = f"{DYNDNS_CONFIG['server_url']}?key={DYNDNS_CONFIG['secret_key']}&ip={current_ip}"
            response = await asyncio.to_thread(
                requests.get, update_url, timeout=10
            )
            print(f"✅ Mise à jour effectuée - {response.text}")
        else:
            print("✅ IP déjà synchronisée - Aucune mise à jour nécessaire")
        
    except Exception as e:
        print(f"❌ Erreur DynDNS: {e}")

async def dyndns_background_task():
    """Tâche en arrière-plan pour le DynDNS"""
    while True:
        await update_dyndns()
        await asyncio.sleep(DYNDNS_CONFIG['interval'])

# ========================================
# Lancement du serveur
# ========================================

if __name__ == "__main__":
    print("🚀 Démarrage du Dashboard Video Pipeline")
    print(f"📁 Projet: {PROJECT_ROOT}")
    print(f"📋 CLI: {CLI_SCRIPT}")
    print(f"🎬 Projets: {PROJECTS_DIR}")
    print(f"🌐 Dashboard: http://localhost:47392")
    
    # Afficher l'état de l'authentification
    if AUTH_CONFIG.get('enabled', False):
        print(f"🔒 Authentification: ACTIVÉE (utilisateur: {AUTH_CONFIG.get('username', 'admin')})")
        print("ℹ️  Pour désactiver: config.yml → dashboard.auth.enabled: false")
    else:
        print("🔓 Authentification: DÉSACTIVÉE")
        print("ℹ️  Pour activer: config.yml → dashboard.auth.enabled: true")
    
    # Afficher l'état du DynDNS
    if DYNDNS_CONFIG['enabled']:
        print(f"🌐 DynDNS: ACTIVÉ (mise à jour toutes les {DYNDNS_CONFIG['interval']} secondes)")
        print(f"📡 Serveur: {DYNDNS_CONFIG['server_url']}")
        print(f"🔍 Vérifier IP: http://leader-referencement.com/get_current_ip.php")
    else:
        print("🌐 DynDNS: DÉSACTIVÉ")
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=47392,
        reload=True,
        log_level="info"
    )
