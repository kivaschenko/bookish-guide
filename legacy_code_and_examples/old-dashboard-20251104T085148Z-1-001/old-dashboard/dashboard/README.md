# 🎬 Video Pipeline Dashboard

Interface web moderne pour gérer le pipeline de génération vidéo automatisé.

## 🚀 Fonctionnalités

### 📋 Gestion des Projets
- ✅ Sélection de projet via dropdown
- ✅ Aperçu des scripts I1, I2, I3 et transcript original
- ✅ Compteurs de mots/lignes en temps réel
- ✅ Mode lecture seule pour éviter les modifications accidentelles

### 🔧 Configuration Pipeline
- ✅ Choix du mode audio (Gemini TTS, OpenAI TTS, Heygen)
- ✅ Sélection des étapes à exécuter
- ✅ Support du mode pipeline complet (`--pipeline`)
- ✅ Option B-roll sauvegardées (`--usebroll`)

### 📊 File d'attente des Tâches
- ✅ Exécution séquentielle automatique
- ✅ Suivi en temps réel du statut
- ✅ Historique des commandes exécutées
- ✅ Gestion des erreurs et timeouts

### 📺 Console Live
- ✅ Logs en temps réel pendant l'exécution
- ✅ Codes couleur pour les différents types de messages
- ✅ Auto-scroll vers les nouveaux messages

## 🏗️ Architecture

```
dashboard/
├── index.html          # Interface principale
├── dashboard.js        # Logique frontend
├── README.md          # Documentation
└── server.py          # Serveur backend (à venir)
```

### 🔌 Découplage
- **Frontend** : Interface web pure (HTML/CSS/JS)
- **Backend** : Serveur Python pour l'intégration CLI
- **CLI** : Scripts existants inchangés

## 🛠️ Installation & Usage

### Installation des dépendances
```bash
cd dashboard/
pip install -r requirements.txt
```

### Lancement (Mode Production uniquement)
```bash
# Méthode 1: Script de lancement automatique
python3 start.py

# Méthode 2: Lancement manuel
python3 server.py

# Le dashboard sera accessible sur http://localhost:8080
```

### Fonctionnalités Production
- ✅ **Projets réels** : Scan automatique du dossier `projects/`
- ✅ **Scripts réels** : Lecture des fichiers `i1.txt`, `i2.txt`, `i3.txt`, `ori_vid.txt`
- ✅ **Exécution CLI** : Subprocess réel avec capture des logs
- ✅ **WebSocket** : Logs temps réel pendant l'exécution
- ✅ **File d'attente** : Gestion automatique des tâches séquentielles

## 🎯 Intégration avec le CLI existant

### Commandes supportées
- `python3 exponential_video.py --meta project-name`
- `python3 exponential_video.py -s project-name`
- `python3 exponential_video.py -ag project-name` (Gemini TTS)
- `python3 exponential_video.py -a project-name` (OpenAI TTS)
- `python3 exponential_video.py -r project-name` (Heygen)
- `python3 exponential_video.py --vectorbroll project-name`
- `python3 exponential_video.py --premontage project-name`
- `python3 exponential_video.py -m project-name`
- `python3 exponential_video.py --pipeline project-name`

### Paramètres dynamiques
- ✅ Mode audio configurable
- ✅ Projet sélectionnable
- ✅ Étapes customisables
- ✅ Options avancées (--usebroll, etc.)

## 🎨 Interface

### Design System
- **Couleurs** : Palette cohérente avec codes CSS variables
- **Typography** : System fonts optimisées
- **Layout** : Grid responsive 2 colonnes
- **Components** : Cartes, boutons, tableaux, console

### Responsive
- ✅ Desktop (1200px+) : Layout 2 colonnes
- ✅ Tablet/Mobile : Stack vertical automatique
- ✅ Console adaptative avec scroll

## 🔮 Roadmap

### Phase 1 : Interface (✅ Terminé)
- [x] Interface HTML/CSS/JS
- [x] Design system complet
- [x] Gestion de la file d'attente

### Phase 2 : Backend (✅ Terminé)
- [x] Serveur Python FastAPI
- [x] Intégration CLI réelle
- [x] WebSocket pour logs temps réel
- [x] API REST pour les projets

### Phase 3 : Avancé (📋 Planifié)
- [ ] Monitoring des ressources
- [ ] Gestion des erreurs avancée
- [ ] Notifications en temps réel
- [ ] Export des logs
- [ ] Mode sombre/clair
- [ ] Raccourcis clavier

## 🧪 Utilisation

### Données Réelles (Mode Production)
- **Projets** : Scan automatique du dossier `projects/`
- **Scripts** : Lecture réelle des fichiers `i1.txt`, `i2.txt`, etc.
- **Exécution** : Subprocess réel avec capture des logs
- **WebSocket** : Mises à jour temps réel via WebSocket

## 🔧 Configuration

### Variables d'environnement
```javascript
const CONFIG = {
    projectsPath: '../projects',
    cliScript: '../exponential_video.py',
    premontageUrl: 'http://localhost:47393',
    websocketPort: 47393
};
```

### Personalisation
- **Projets** : Modifier `CONFIG.projectsPath`
- **CLI** : Adapter `CONFIG.cliScript`
- **Ports** : Configurer `websocketPort` et `premontageUrl`

## 🤝 Contribution

### Structure du code
- **HTML** : Structure sémantique et accessible
- **CSS** : Variables CSS, design system cohérent
- **JS** : Modules ES6, async/await, gestion d'erreurs

### Conventions
- **Nommage** : camelCase pour JS, kebab-case pour CSS
- **Fonctions** : Documentation JSDoc
- **Erreurs** : Try/catch systématique
- **Logs** : Messages avec émojis et couleurs

---

*Interface créée pour compléter le CLI existant sans modification du code principal* 🎯
