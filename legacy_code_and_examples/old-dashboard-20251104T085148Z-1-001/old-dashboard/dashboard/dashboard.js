// ========================================
// Video Pipeline Dashboard - Frontend Logic
// ========================================

// Configuration
const CONFIG = {
    apiBase: '',  // Même domaine
    premontageUrl: `${window.location.protocol}//${window.location.hostname}:47393`,
    websocketUrl: `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}:47392/ws`
};

// Utilitaires
const $ = sel => document.querySelector(sel);
const $$ = sel => Array.from(document.querySelectorAll(sel));

function now() {
    return new Date().toLocaleTimeString([], {hour12: false});
}

function appendLog(line, type = 'info') {
    const el = $('#console');
    const className = type === 'error' ? 'style="color:#ef4444"' : 
                     type === 'success' ? 'style="color:#10b981"' : 
                     type === 'warning' ? 'style="color:#f59e0b"' : '';
    // Sécuriser et préserver les retours à la ligne pour une meilleure lisibilité
    const safe = String(line ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>');
    el.insertAdjacentHTML('beforeend', 
        `<div><span class="time">[${now()}]</span> <span ${className}>${safe}</span></div>`);
    el.scrollTop = el.scrollHeight;
}

function wordCount(txt) {
    return (txt.trim().match(/\b\w+\b/g) || []).length;
}

function lineCount(txt) {
    return txt.split('\n').length;
}

// ========================================
// Gestion des projets
// ========================================

let availableProjects = [];

// ========================================
// Persistance des états de l'interface
// ========================================

function saveCheckboxStates() {
    const states = {};
    
    // Sauvegarder les étapes
    $$('.step').forEach(checkbox => {
        states[checkbox.value] = checkbox.checked;
    });
    
    // Sauvegarder useBroll
    const useBroll = $('#useBroll');
    if (useBroll) {
        states['useBroll'] = useBroll.checked;
    }
    
    // Sauvegarder le mode audio
    const audioMode = $('#audioMode');
    if (audioMode) {
        states['audioMode'] = audioMode.value;
    }
    
    sessionStorage.setItem('checkboxStates', JSON.stringify(states));
}

function restoreCheckboxStates() {
    try {
        const savedStates = sessionStorage.getItem('checkboxStates');
        if (!savedStates) return;
        
        const states = JSON.parse(savedStates);
        
        // Restaurer les étapes
        $$('.step').forEach(checkbox => {
            if (states.hasOwnProperty(checkbox.value)) {
                checkbox.checked = states[checkbox.value];
            }
        });
        
        // Restaurer useBroll
        const useBroll = $('#useBroll');
        if (useBroll && states.hasOwnProperty('useBroll')) {
            useBroll.checked = states['useBroll'];
        }
        
        // Restaurer le mode audio
        const audioMode = $('#audioMode');
        if (audioMode && states.hasOwnProperty('audioMode')) {
            audioMode.value = states['audioMode'];
        }
        
        appendLog('⚙️ États des cases restaurés');
    } catch (error) {
        appendLog(`❌ Erreur restauration cases: ${error.message}`, 'error');
    }
}

async function loadProjects() {
    try {
        appendLog('📁 Chargement des projets...');
        
        const response = await fetch(`${CONFIG.apiBase}/api/projects`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        availableProjects = data.projects;
        
        const select = $('#projectSelect');
        select.innerHTML = '';
        
        availableProjects.forEach(project => {
            const option = document.createElement('option');
            option.value = project;
            option.textContent = project;
            select.appendChild(option);
        });
        
        // Restaurer le projet précédemment sélectionné ou sélectionner le plus récent
        const savedProject = localStorage.getItem('selectedProject');
        if (savedProject && availableProjects.includes(savedProject)) {
            select.value = savedProject;
            appendLog(`📁 Projet restauré: ${savedProject}`);
        } else if (availableProjects.length > 0) {
            // Sélectionner le projet avec le numéro le plus élevé (le plus récent)
            const sortedProjects = availableProjects.sort((a, b) => {
                const numA = parseInt(a.match(/\d+/)?.[0] || '0');
                const numB = parseInt(b.match(/\d+/)?.[0] || '0');
                return numB - numA; // Tri décroissant
            });
            select.value = sortedProjects[0];
            appendLog(`📁 Projet le plus récent: ${select.value}`);
        }
        
        // Sauvegarder la sélection actuelle
        if (select.value) {
            localStorage.setItem('selectedProject', select.value);
            refreshAllScripts();
            
            // Mettre à jour les indicateurs d'étapes
            updateStepIndicators(select.value);
        }
        
        // Restaurer les états des cases à cocher
        restoreCheckboxStates();
        
        appendLog(`📁 ${availableProjects.length} projets chargés`);
    } catch (error) {
        appendLog(`❌ Erreur chargement projets: ${error.message}`, 'error');
    }
}

// Écouter les changements de projet
$('#projectSelect').addEventListener('change', () => {
    const selectedProject = $('#projectSelect').value;
    if (selectedProject) {
        localStorage.setItem('selectedProject', selectedProject);
        appendLog(`📁 Projet sélectionné: ${selectedProject}`);
        
        // Mettre à jour les indicateurs d'étapes
        updateStepIndicators(selectedProject);
    }
    refreshAllScripts();
});

// ========================================
// Gestion des scripts I1-I3
// ========================================

function switchTab(tabName) {
    $$('.tab').forEach(btn => btn.classList.remove('active'));
    $(`.tab[data-tab="${tabName}"]`).classList.add('active');
    
    ['ori', 'i1', 'i2', 'i3'].forEach(name => {
        $(`#pane-${name}`).style.display = (name === tabName) ? 'block' : 'none';
    });
}

// Gestion des onglets
$$('.tab').forEach(btn => {
    btn.addEventListener('click', () => {
        switchTab(btn.dataset.tab);
    });
});

async function refreshScript(scriptType) {
    const project = $('#projectSelect').value;
    if (!project) {
        appendLog('⚠️ Aucun projet sélectionné', 'warning');
        return;
    }
    
    try {
        appendLog(`📄 Chargement script ${scriptType.toUpperCase()} pour ${project}...`);
        
        const response = await fetch(`${CONFIG.apiBase}/api/projects/${project}/scripts`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        const content = data.scripts[scriptType] || '';
        
        const textarea = $(`#txt-${scriptType}`);
        textarea.value = content;
        
        // Mettre à jour le compteur
        const countEl = $(`#${scriptType}Count`);
        if (countEl) {
            const count = wordCount(content);
            countEl.textContent = `Mots: ${count}`;
        }
        
        appendLog(`📄 Script ${scriptType.toUpperCase()} chargé (${wordCount(content)} mots)`);
    } catch (error) {
        appendLog(`❌ Erreur lecture ${scriptType}: ${error.message}`, 'error');
        
        // Vider le contenu en cas d'erreur
        const textarea = $(`#txt-${scriptType}`);
        textarea.value = '';
        const countEl = $(`#${scriptType}Count`);
        if (countEl) {
            countEl.textContent = 'Mots: 0';
        }
    }
}

// Fonction supprimée - plus de mock en mode production

function refreshAllScripts() {
    ['input', 'ori', 'i1', 'i2', 'i3'].forEach(script => {
        refreshScript(script);
    });
}

// ========================================
// Gestion des tâches et file d'attente
// ========================================

const tasks = [];
let running = false;
let lastTaskId = 0;
let currentTimer = null;

function buildCommand(project, steps, audioMode, useBroll) {
    const commands = [];
    const python = 'python3';
    const script = CONFIG.cliScript;
    
    // Étapes individuelles
    if (steps.includes('get_ori')) {
        commands.push(`${python} ${script} --get_ori https://www.youtube.com/watch?v=VIDEO_ID ${project}`);
    }
    
    if (steps.includes('script')) {
        commands.push(`${python} ${script} -s ${project}`);
    }
    
    if (steps.includes('audio')) {
        const audioFlag = audioMode === 'gemini_tts' ? '-ag' : 
                         audioMode === 'openai_tts' ? '-a' : '-r';
        commands.push(`${python} ${script} ${audioFlag} ${project}`);
    }
    
    if (steps.includes('vectorbroll')) {
        commands.push(`${python} ${script} --vectorbroll ${project}`);
    }
    
    if (steps.includes('premontage')) {
        commands.push(`${python} ${script} --premontage ${project}`);
    }
    
    if (steps.includes('compile')) {
        const useBrollFlag = useBroll ? ' --usebroll' : '';
        commands.push(`${python} ${script} -m${useBrollFlag} ${project}`);
    }
    
    return commands;
}

async function launchPipeline(project, steps, audioMode, useBroll) {
    try {
        appendLog(`📋 Création tâche: ${project} (${steps.join(' → ')})`);
        
        // Get language from the language selector
        const language = document.getElementById('languageSelect').value;
        
        const response = await fetch(`${CONFIG.apiBase}/api/launch-pipeline`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project,
                steps,
                language,
                audio_mode: audioMode,
                use_broll: useBroll
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        appendLog(`✅ Tâche #${result.task_id} créée avec succès`);
        
        // Les tâches seront mises à jour via WebSocket
        
    } catch (error) {
        appendLog(`❌ Erreur création tâche: ${error.message}`, 'error');
    }
}

async function launchPremontageImmediate(project) {
    try {
        appendLog(`🎬 Lancement immédiat du prémontage pour ${project}...`, 'info');
        
        const response = await fetch(`${CONFIG.apiBase}/api/premontage/${project}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        appendLog(`✅ Prémontage ${project} lancé avec succès`, 'success');
        
        // Ouvrir automatiquement le prémontage dans une nouvelle tab
        setTimeout(() => {
            openPremontage();
        }, 1000); // Délai pour laisser le serveur démarrer
        
    } catch (error) {
        appendLog(`❌ Erreur lancement prémontage: ${error.message}`, 'error');
    }
}

function renderTasks() {
    const tbody = $('#taskTable tbody');
    tbody.innerHTML = '';
    
    tasks.forEach(task => {
        const tr = document.createElement('tr');
        const statusClass = {
            'running': 'running',
            'queued': 'queued', 
            'done': 'done',
            'failed': 'fail',
            'cancelled': 'fail'
        }[task.status] || '';
        
        const currentCmd = task.commands ? (task.commands[task.current_command] || task.commands[0] || '') : '';
        const cmdDisplay = currentCmd.length > 50 ? currentCmd.substring(0, 47) + '...' : currentCmd;
        
        // Ajouter la numérotation aux étapes
        const stepNumberMap = {
            'script': '1. script',
            'audio': '2. audio', 
            'vectorbroll': '3. vectorbroll',
            'premontage': '4. prémontage',
            'compile': '5. compilation finale'
        };
        
        const numberedSteps = task.steps ? task.steps.map(step => stepNumberMap[step] || step) : [];
        const stepsLabel = numberedSteps.join(' → ');
        
        // Bouton d'arrêt : visible uniquement pour les tâches en cours ET en mode admin
        const stopButton = (task.status === 'running' && isAdminMode)
            ? `<button class="stop-btn" onclick="stopTask(${task.id})" title="Arrêter la tâche (CTRL+C)">✕</button>`
            : '<span style="width:28px;display:inline-block"></span>';
        
        // Construire le HTML - TOUJOURS inclure toutes les cellules mais avec classe admin-only
        const stepsCell = `<td class="admin-only">${stepsLabel}</td>`;
        const modeCell = `<td class="admin-only">${task.audio_mode || 'N/A'}</td>`;
        const commandCell = `<td class="admin-only"><code class="kbd">${cmdDisplay}</code></td>`;
        const actionsCell = `<td class="admin-only">${stopButton}</td>`;
        
        // Statut cliquable seulement en mode admin
        const statusClickable = isAdminMode ? 'clickable' : '';
        const statusOnclick = isAdminMode ? `onclick="showTaskLogs(${task.id})"` : '';
        
        tr.innerHTML = `
            <td>${task.id}</td>
            <td>${task.project}</td>
            ${stepsCell}
            ${modeCell}
            <td><span class="status ${statusClass} ${statusClickable}" ${statusOnclick}>${task.status}</span></td>
            <td>${task.started_at ? new Date(task.started_at).toLocaleTimeString() : '-'}</td>
            <td>${calculateDuration(task)}</td>
            ${commandCell}
            ${actionsCell}
        `;
        
        tbody.appendChild(tr);
    });
}

function calculateDuration(task) {
    if (!task.started_at) return '-';
    
    const start = new Date(task.started_at);
    const end = task.finished_at ? new Date(task.finished_at) : new Date();
    const diff = Math.floor((end - start) / 1000);
    
    if (diff < 60) return `${diff}s`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ${diff % 60}s`;
    return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`;
}

async function processQueue() {
    if (running) return;
    
    const nextTask = tasks.find(t => t.status === 'Queued');
    if (!nextTask) return;
    
    running = true;
    nextTask.status = 'Running';
    nextTask.startedAt = now();
    nextTask.elapsed = '0s';
    
    appendLog(`▶️ Démarrage tâche #${nextTask.id}: ${nextTask.project}`, 'success');
    renderTasks();
    
    try {
        await executeTask(nextTask);
        nextTask.status = 'Done';
        appendLog(`✅ Tâche #${nextTask.id} terminée avec succès`, 'success');
    } catch (error) {
        nextTask.status = 'Failed';
        appendLog(`❌ Tâche #${nextTask.id} échouée: ${error.message}`, 'error');
    }
    
    running = false;
    renderTasks();
    
    // Continuer avec la tâche suivante
    setTimeout(processQueue, 1000);
}

async function executeTask(task) {
    // L'exécution est maintenant gérée par le serveur
    // Cette fonction n'est plus utilisée côté client
}

// ========================================
// Interface utilisateur - Événements
// ========================================

$('#launchBtn').addEventListener('click', () => {
    const project = $('#projectSelect').value;
    const steps = $$('.step:checked').map(input => input.value);
    const audioMode = $('#audioMode').value;
    const useBroll = $('#useBroll').checked;
    
    if (!project) {
        alert('Veuillez sélectionner un projet');
        return;
    }
    
    if (steps.length === 0) {
        alert('Veuillez sélectionner au moins une étape');
        return;
    }
    
    // Note: Alert VPN supprimée car le proxy français résout le problème géographique
    
    // Séparer prémontage des autres étapes
    const premontageSteps = steps.filter(step => step === 'premontage');
    const queueSteps = steps.filter(step => step !== 'premontage');
    
    // Lancer prémontage immédiatement (hors queue)
    if (premontageSteps.length > 0) {
        launchPremontageImmediate(project);
    }
    
    // Créer tâche pour les autres étapes
    if (queueSteps.length > 0) {
        launchPipeline(project, queueSteps, audioMode, useBroll);
    }
});

$('#clearDoneBtn').addEventListener('click', async () => {
    try {
        const response = await fetch(`${CONFIG.apiBase}/api/tasks/clear-done`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        appendLog(`🗑️ ${result.removed} tâche(s) supprimée(s)`);
        
    } catch (error) {
        appendLog(`❌ Erreur suppression tâches: ${error.message}`, 'error');
    }
});

$('#killProcessBtn').addEventListener('click', async () => {
    if (!confirm('⚠️ Êtes-vous sûr de vouloir tuer tous les processus du pipeline (exponential_video) ? Le dashboard et le prémontage ne seront pas arrêtés.')) {
        return;
    }
    
    try {
        appendLog('🔪 Arrêt de tous les processus pipeline (exponential_video)...', 'info');
        
        const response = await fetch(`${CONFIG.apiBase}/api/kill-exponential-video`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        appendLog(`🔪 ${result.killed} processus arrêté(s): ${result.details}`, 'success');
        
    } catch (error) {
        appendLog(`❌ Erreur arrêt processus: ${error.message}`, 'error');
    }
});

$('#killPremontageBtn').addEventListener('click', async () => {
    if (!confirm('⚠️ Tuer le serveur de prémontage ? (ex: src/premontage/server.py)')) {
        return;
    }
    try {
        appendLog('🔪 Arrêt du serveur de prémontage...', 'info');
        const response = await fetch(`${CONFIG.apiBase}/api/kill-premontage`, { method: 'POST' });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const result = await response.json();
        appendLog(`🔪 ${result.killed} processus prémontage arrêté(s): ${result.details}`, 'success');
    } catch (error) {
        appendLog(`❌ Erreur arrêt prémontage: ${error.message}`, 'error');
    }
});

$('#showProcessesBtn').addEventListener('click', async () => {
    try {
        appendLog('🔎 Récupération des processus pertinents...', 'info');
        const response = await fetch(`${CONFIG.apiBase}/api/show-processes`, { method: 'GET' });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const result = await response.json();
        appendLog(`🔎 Processus exponential_video:\n${result.exponential_video || '—'}`);
        appendLog(`🎬 Processus prémontage:\n${result.premontage || '—'}`);
        appendLog(`🖥️ Processus dashboard server:\n${result.dashboard || '—'}`);
    } catch (error) {
        appendLog(`❌ Erreur récupération processus: ${error.message}`, 'error');
    }
});

// Mise à jour des compteurs en temps réel
$('#txt-ori').addEventListener('input', () => {
    const count = wordCount($('#txt-ori').value);
    $('#oriCount').textContent = `Mots: ${count}`;
});

['i1', 'i2', 'i3'].forEach(script => {
    $(`#txt-${script}`).addEventListener('input', () => {
        const count = wordCount($(`#txt-${script}`).value);
        $(`#${script}Count`).textContent = `Mots: ${count}`;
    });
});

// ========================================
// WebSocket pour mises à jour temps réel
// ========================================

let websocket = null;

function connectWebSocket() {
    try {
        websocket = new WebSocket(CONFIG.websocketUrl);
        
        websocket.onopen = () => {
            appendLog('🔌 Connexion WebSocket établie', 'success');
        };
        
        websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
                case 'log':
                    appendLog(data.message);
                    break;
                    
                case 'task_update':
                    updateTask(data.task);
                    break;
                    
                case 'tasks_update':
                    updateAllTasks(data.tasks);
                    break;
                    
                default:
                    console.log('Message WebSocket inconnu:', data);
            }
        };
        
        websocket.onclose = () => {
            appendLog('🔌 Connexion WebSocket fermée', 'warning');
            // Reconnexion automatique après 3 secondes
            setTimeout(connectWebSocket, 3000);
        };
        
        websocket.onerror = (error) => {
            appendLog('❌ Erreur WebSocket', 'error');
        };
        
    } catch (error) {
        appendLog(`❌ Erreur connexion WebSocket: ${error.message}`, 'error');
    }
}

function updateTask(taskData) {
    // Trouver ou créer la tâche
    let existingTask = tasks.find(t => t.id === taskData.id);
    if (existingTask) {
        Object.assign(existingTask, taskData);
    } else {
        tasks.push(taskData);
    }
    renderTasks();
}

function updateAllTasks(tasksData) {
    tasks.length = 0; // Vider le tableau
    tasks.push(...tasksData);
    renderTasks();
}

// ========================================
// Initialisation
// ========================================

function setupCheckboxListeners() {
    // Écouter les changements sur toutes les cases d'étapes
    $$('.step').forEach(checkbox => {
        checkbox.addEventListener('change', saveCheckboxStates);
    });
    
    // Écouter useBroll
    const useBroll = $('#useBroll');
    if (useBroll) {
        useBroll.addEventListener('change', saveCheckboxStates);
    }
    
    // Écouter le mode audio
    const audioMode = $('#audioMode');
    if (audioMode) {
        audioMode.addEventListener('change', saveCheckboxStates);
    }
    
    appendLog('⚙️ Listeners de sauvegarde activés');
}

function startDurationTimer() {
    // Mettre à jour les durées toutes les secondes
    setInterval(() => {
        const runningTasks = tasks.filter(t => t.status === 'running');
        if (runningTasks.length > 0) {
            renderTasks(); // Re-render pour mettre à jour les durées
        }
    }, 1000); // Toutes les 1 seconde
}

async function init() {
    appendLog('🚀 Initialisation du Dashboard Video Pipeline');
    
    try {
        // Fermer le modal au démarrage
        closeTaskLogsModal();
        
        await loadProjects();
        setupCheckboxListeners();
        connectWebSocket();
        startDurationTimer();
        
        // Restaurer le mode admin après que tout soit chargé
        setTimeout(() => {
            restoreAdminMode();
            
            // Si on n'est pas en mode admin, décocher les étapes invisibles
            if (!isAdminMode) {
                const hiddenSteps = ['script', 'audio', 'vectorbroll', 'compile'];
                hiddenSteps.forEach(step => {
                    const checkbox = document.querySelector(`input.step[value="${step}"]`);
                    if (checkbox) {
                        checkbox.checked = false;
                    }
                });
            }
            
            // Mettre à jour les indicateurs d'étapes même en mode utilisateur
            const selectedProject = $('#projectSelect').value;
            if (selectedProject) {
                updateStepIndicators(selectedProject);
            }
            
            // Ajouter l'event listener pour le lien prémontage
            const openPremontageBtn = $('#openPremontageBtn');
            if (openPremontageBtn) {
                openPremontageBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    openPremontage();
                });
            }
        }, 100);
        
        appendLog('✅ Dashboard prêt!', 'success');
    } catch (error) {
        appendLog(`❌ Erreur d'initialisation: ${error.message}`, 'error');
    }
}

// Démarrer l'application
document.addEventListener('DOMContentLoaded', init);

// ========================================
// Modal pour les logs de tâches
// ========================================

async function showTaskLogs(taskId) {
    // Protection : ne pas ouvrir le modal si on n'est pas en mode admin
    if (!isAdminMode) {
        console.log('Modal bloqué : mode admin requis');
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.apiBase}/api/tasks/${taskId}/logs`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const taskData = await response.json();
        
        // Remplir la modal
        $('#modalTitle').textContent = `Logs de la tâche #${taskId}`;
        $('#modalProject').textContent = taskData.project;
        $('#modalStatus').textContent = taskData.status;
        $('#modalCurrentCmd').textContent = `${taskData.current_command + 1}/${taskData.commands.length}`;
        
        // Afficher les commandes
        const commandsEl = $('#modalCommands');
        commandsEl.innerHTML = '';
        taskData.commands.forEach((cmd, index) => {
            const isActive = index === taskData.current_command;
            const status = index < taskData.current_command ? '✅' : 
                          index === taskData.current_command ? '▶️' : '⏸️';
            commandsEl.innerHTML += `<div><span style="color:#10b981">${status}</span> ${cmd}</div>`;
        });
        
        // Afficher les logs
        const logsEl = $('#modalLogs');
        logsEl.innerHTML = '';
        if (taskData.logs && taskData.logs.length > 0) {
            taskData.logs.forEach(log => {
                logsEl.innerHTML += `<div>${log}</div>`;
            });
        } else {
            logsEl.innerHTML = '<div style="color:#9ca3af">Aucun log disponible</div>';
        }
        
        // Afficher l'erreur si elle existe
        if (taskData.error) {
            logsEl.innerHTML += `<div style="color:#ef4444;margin-top:12px;border-top:1px solid #374151;padding-top:8px"><strong>Erreur:</strong><br/>${taskData.error}</div>`;
        }
        
        // Afficher la modal seulement si on est en mode admin
        if (isAdminMode) {
            $('#taskLogsModal').style.display = 'block';
        }
        
        // Faire défiler vers le bas
        logsEl.scrollTop = logsEl.scrollHeight;
        
    } catch (error) {
        appendLog(`❌ Erreur lecture logs: ${error.message}`, 'error');
    }
}

function closeTaskLogsModal() {
    $('#taskLogsModal').style.display = 'none';
}

// Fermer la modal en cliquant à l'extérieur
window.addEventListener('click', (event) => {
    const modal = $('#taskLogsModal');
    if (event.target === modal) {
        closeTaskLogsModal();
    }
});

// ========================================
// Fonctions globales pour l'HTML
// ========================================

async function stopTask(taskId) {
    try {
        const confirmed = confirm(`Êtes-vous sûr de vouloir arrêter la tâche #${taskId} ?`);
        if (!confirmed) return;
        
        appendLog(`🛑 Arrêt de la tâche #${taskId}...`);
        
        const response = await fetch(`${CONFIG.apiBase}/api/tasks/${taskId}/stop`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        appendLog(`✅ Tâche #${taskId} arrêtée avec succès`);
        
    } catch (error) {
        appendLog(`❌ Erreur arrêt tâche: ${error.message}`, 'error');
    }
}

// ========================================
// Vérification des étapes
// ========================================

async function checkStepStatus(step, project) {
    try {
        switch(step) {
            case 1:
                return await checkScriptStep(project);
            case 2:
                return await checkAudioStep(project);
            case 3:
                return await checkBrollStep(project);
            default:
                return false;
        }
    } catch (error) {
        console.error(`Erreur vérification étape ${step}:`, error);
        return false;
    }
}

async function checkScriptStep(project) {
    try {
        const response = await fetch(`${CONFIG.apiBase}/api/projects/${project}/scripts`);
        if (!response.ok) return false;
        
        const data = await response.json();
        const i3Content = data.scripts?.i3 || '';
        const count = wordCount(i3Content); // Utiliser la même fonction que partout ailleurs
        
        return count >= 2600;
    } catch (error) {
        return false;
    }
}

async function checkAudioStep(project) {
    try {
        const response = await fetch(`${CONFIG.apiBase}/api/projects/${project}/audio-status`);
        if (!response.ok) return false;
        
        const data = await response.json();
        return data.audioComplete || false;
    } catch (error) {
        return false;
    }
}

async function checkBrollStep(project) {
    try {
        const response = await fetch(`${CONFIG.apiBase}/api/projects/${project}/broll-status`);
        if (!response.ok) return false;
        
        const data = await response.json();
        return data.brollComplete || false;
    } catch (error) {
        return false;
    }
}

async function updateStepIndicators(project) {
    if (!project) return;
    
    for (let step = 1; step <= 3; step++) {
        const indicator = document.querySelector(`[data-step="${step}"] .step-status`);
        if (!indicator) continue;
        
        const isComplete = await checkStepStatus(step, project);
        indicator.textContent = isComplete ? '✅' : '❌';
    }
}

// ========================================
// Mode Admin
// ========================================

let isAdminMode = false;
const ADMIN_PASSWORD = "admin2025"; // Changez ce mot de passe !

function toggleAdminMode() {
    if (!isAdminMode) {
        // Vérifier si on est déjà authentifié
        if (localStorage.getItem('adminMode') === 'true') {
            // Déjà authentifié, activer directement
            enableAdminMode();
        } else {
            // Demander le mot de passe
            const password = prompt("Mot de passe admin :");
            if (password === ADMIN_PASSWORD) {
                enableAdminMode();
            } else if (password !== null) {
                alert("❌ Mot de passe incorrect");
            }
        }
    } else {
        disableAdminMode();
    }
}

function enableAdminMode() {
    isAdminMode = true;
    document.body.classList.add('admin-mode');
    $('#adminToggle').classList.add('admin-active');
    $('#adminToggle').textContent = 'Dev ✓';
    
    // Fermer le modal s'il est ouvert
    closeTaskLogsModal();
    
    // Sauvegarder en localStorage (persistant après fermeture navigateur)
    localStorage.setItem('adminMode', 'true');
    
    appendLog('🔓 Mode développeur activé', 'success');
    
    // Re-render les tâches pour afficher les colonnes admin
    renderTasks();
}

function disableAdminMode() {
    isAdminMode = false;
    document.body.classList.remove('admin-mode');
    $('#adminToggle').classList.remove('admin-active');
    $('#adminToggle').textContent = 'Dev';
    
    // Fermer le modal s'il est ouvert
    closeTaskLogsModal();
    
    // Décocher les étapes invisibles en mode utilisateur
    const hiddenSteps = ['script', 'audio', 'vectorbroll', 'compile'];
    hiddenSteps.forEach(step => {
        const checkbox = document.querySelector(`input.step[value="${step}"]`);
        if (checkbox) {
            checkbox.checked = false;
        }
    });
    
    // NE PAS supprimer localStorage - garder l'authentification
    // localStorage.removeItem('adminMode');
    
    appendLog('🔒 Mode utilisateur activé', 'warning');
    
    // Re-render les tâches pour masquer les colonnes admin
    renderTasks();
}

// Restaurer le mode admin si activé dans localStorage
function restoreAdminMode() {
    if (localStorage.getItem('adminMode') === 'true') {
        isAdminMode = true;
        document.body.classList.add('admin-mode');
        
        // Vérifier que l'élément existe avant de le modifier
        const adminToggle = $('#adminToggle');
        if (adminToggle) {
            adminToggle.classList.add('admin-active');
            adminToggle.textContent = 'Dev ✓';
        }
        
        appendLog('🔓 Mode développeur restauré', 'success');
    }
}

// ========================================
// Prémontage
// ========================================

function openPremontage() {
    // Construire l'URL du prémontage avec la même IP que le dashboard
    const premontageUrl = `${window.location.protocol}//${window.location.hostname}:47393`;
    
    // Ouvrir dans une nouvelle tab
    window.open(premontageUrl, '_blank');
    
    appendLog(`🎬 Prémontage ouvert: ${premontageUrl}`, 'success');
}

// ========================================
// Script & Voice Generation (API script_and_voice)
// ========================================

// Script and Voice module now uses CLI instead of API REST

async function createProject() {
    const projectName = document.getElementById('projectNameInput').value.trim();
    const inputText = document.getElementById('inputText').value.trim();
    const createProjectBtn = document.getElementById('createProjectBtn');
    const createProjectStatus = document.getElementById('createProjectStatus');
    const createProjectProgress = document.getElementById('createProjectProgress');
    
    if (!projectName) {
        alert('Veuillez entrer un nom de projet');
        return;
    }
    
    if (!inputText) {
        alert('Veuillez entrer du texte d\'entrée');
        return;
    }
    
    // Validate project name (alphanumeric, hyphens, underscores only)
    if (!/^[a-zA-Z0-9_-]+$/.test(projectName)) {
        alert('Le nom du projet ne peut contenir que des lettres, chiffres, tirets et underscores');
        return;
    }
    
    createProjectBtn.disabled = true;
    createProjectStatus.style.display = 'block';
    createProjectProgress.textContent = '⏳ Création du projet en cours...';
    
    appendLog('📁 Création du projet...', 'info');
    
    try {
        const response = await fetch('/api/save-input-text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project: projectName,
                input_text: inputText
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            appendLog(`✅ Projet créé avec succès: ${projectName}`, 'success');
            createProjectProgress.textContent = `✅ Projet créé: ${projectName}`;
            
            // Clear inputs
            document.getElementById('projectNameInput').value = '';
            document.getElementById('inputText').value = '';
            
            // Refresh project list
            refreshProjects();
            
            // Select the new project
            setTimeout(() => {
                const projectSelect = document.getElementById('projectSelect');
                projectSelect.value = projectName;
            }, 500);
            
        } else {
            throw new Error(result.detail || result.message || 'Erreur inconnue');
        }
    } catch (err) {
        appendLog(`❌ Erreur lors de la création du projet: ${err.message}`, 'error');
        createProjectProgress.textContent = `❌ Erreur: ${err.message}`;
    } finally {
        createProjectBtn.disabled = false;
    }
}


// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    $('#createProjectBtn')?.addEventListener('click', createProject);
    
    
    // Show/hide script options when script checkbox is toggled
    const scriptCheckbox = document.querySelector('input[value="script"]');
    const scriptOptions = document.getElementById('scriptOptions');
    
    if (scriptCheckbox && scriptOptions) {
        function toggleScriptOptions() {
            if (scriptCheckbox.checked) {
                scriptOptions.style.display = 'block';
            } else {
                scriptOptions.style.display = 'none';
            }
        }
        
        scriptCheckbox.addEventListener('change', toggleScriptOptions);
        toggleScriptOptions(); // Initial state
    }
});

window.refreshScript = refreshScript;
window.showTaskLogs = showTaskLogs;
window.closeTaskLogsModal = closeTaskLogsModal;
window.stopTask = stopTask;
window.toggleAdminMode = toggleAdminMode;
window.openPremontage = openPremontage;
