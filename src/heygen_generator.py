#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de génération de vidéos via l'API Heygen.
Crée une vidéo pour chaque paragraphe du script I3 avec un avatar aléatoire.
"""

import logging
import random
import time
import json
import requests
import os
import sys
import traceback
import subprocess
from pathlib import Path
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import re
from selenium.common.exceptions import NoSuchElementException
import platform

def setup_logging():
    """Configure le système de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s',  # Ajout de %(filename)s
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# Fonction pour vérifier si Chrome est installé
def check_chrome_installed():
    """Vérifie si Chrome est installé sur le système."""
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",    # Windows
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        "/usr/bin/google-chrome",                                       # Linux
        "/usr/bin/chromium-browser"
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            logging.info(f"Chrome trouvé: {path}")
            return True
    
    # Tenter de localiser Chrome avec la commande 'which' sur macOS/Linux
    if os.name == 'posix':
        try:
            result = subprocess.run(["which", "google-chrome"], 
                                   capture_output=True, text=True, check=False)
            if result.returncode == 0:
                chrome_path = result.stdout.strip()
                logging.info(f"Chrome trouvé via 'which': {chrome_path}")
                return True
        except Exception as e:
            logging.error(f"Erreur lors de la recherche de Chrome avec 'which': {e}")
    
    logging.error("Chrome non trouvé sur le système")
    return False

class HeygenGenerator:
    """
    Classe gérant la génération de vidéos via l'API Heygen.
    Utilise le script I3 pour générer une vidéo par paragraphe.
    """

    def __init__(self, config):
        """
        Initialise le générateur Heygen avec la configuration.
        
        Args:
            config (dict): Configuration chargée depuis config.yml
        """
        self.config = config
        self.api_key = config['api']['heygen']['api_key']
        self.check_interval = config['api']['heygen']['check_interval']
        self.max_checks = config['api']['heygen']['max_checks']
        self.avatars = config['heygen_avatars']
        self.temp_path = Path(config['paths']['temp'])
        self.output_path = Path(config['paths']['heygen'])
        self.voice_config = config['audio']['voice']
        
        # Créer le dossier de sortie s'il n'existe pas
        os.makedirs(self.output_path, exist_ok=True)
        
        # Déterminer le mode de génération (API ou navigateur)
        self.generation_mode = config['api']['heygen'].get('generation_mode', 'api')
        # Déterminer si on doit attendre et télécharger les vidéos
        self.wait_and_download = config['api']['heygen'].get('heygen_wait_and_download', True)
        logging.info(f"Mode de génération: {self.generation_mode}")
        logging.info(f"Attendre et télécharger: {self.wait_and_download}")
        
        if self.generation_mode == 'api':
            # Configuration des headers pour l'API
            # Essayons différentes méthodes d'authentification
            self.headers_options = [
                # Option 1: X-Api-Key
                {
                    'X-Api-Key': self.api_key,
                    'Content-Type': 'application/json'
                },
                # Option 2: Authorization Bearer
                {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                # Option 3: Authorization Basic
                {
                    'Authorization': f'Basic {self.api_key}',
                    'Content-Type': 'application/json'
                },
                # Option 4: apikey dans le header
                {
                    'apikey': self.api_key,
                    'Content-Type': 'application/json'
                }
            ]
            
            # Vérifier l'authentification et définir les headers corrects
            self.headers = self.verify_authentication()
            logging.info(f"Headers d'authentification configurés: {self.headers}")
        else:
            # Initialiser le navigateur si le mode est 'browser'
            self.browser = None
            self.browser_config = config['api']['heygen'].get('browser', {})
            self.automation_type = self.browser_config.get('automation_type', 'selenium')
            logging.info(f"Type d'automatisation du navigateur: {self.automation_type}")
            
            # Vérifier si Chrome est installé
            if not check_chrome_installed():
                logging.error("Chrome n'est pas installé, impossible d'utiliser le mode navigateur")
                raise RuntimeError("Chrome n'est pas installé, impossible d'utiliser le mode navigateur")

    def verify_authentication(self):
        """
        Vérifie l'authentification avec l'API Heygen et récupère des informations sur les avatars disponibles.
        
        Returns:
            dict: Headers d'authentification configurés
        """
        logging.info("Vérification de l'authentification avec l'API Heygen...")
        
        # Essai avec X-Api-Key
        headers = {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                'https://api.heygen.com/v1/user/me',
                headers=headers
            )
            
            logging.info(f"Statut de la réponse: {response.status_code}")
            
            if response.status_code == 200:
                logging.info("Authentification réussie avec la méthode 1")
                logging.info(f"Réponse: {response.json()}")
                logging.info(f"Headers d'authentification configurés: {headers}")
                
                # Commenté: Tentative de récupération des informations sur les avatars disponibles
                """
                logging.info("Tentative de récupération des informations sur les avatars disponibles...")
                
                # Utiliser directement l'endpoint v2 qui fonctionne
                try:
                    avatar_response = requests.get(
                        'https://api.heygen.com/v2/avatars',
                        headers=headers
                    )
                    
                    if avatar_response.status_code == 200:
                        logging.info("Succès avec l'endpoint v2 pour les avatars")
                        # Commenté pour éviter d'afficher la liste complète des avatars
                        # logging.info(f"Avatars disponibles: {avatar_response.json()}")
                        logging.info("Liste des avatars récupérée avec succès (non affichée pour plus de clarté)")
                    else:
                        logging.warning(f"Échec avec l'endpoint v2 pour les avatars: {avatar_response.status_code}")
                except Exception as e:
                    logging.error(f"Erreur lors de la récupération des avatars: {str(e)}")
                """
                
                return headers  # Retourner les headers au lieu de True
            else:
                logging.error(f"Échec de l'authentification avec la méthode 1: {response.status_code}")
                return None  # Retourner None au lieu de False
                
        except Exception as e:
            logging.error(f"Erreur lors de la vérification de l'authentification: {str(e)}")
            return None  # Retourner None au lieu de False

    def initialize_browser(self):
        """
        Initialise le navigateur pour l'automatisation web.
        """
        if self.automation_type == 'selenium':
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                logging.info("Initialisation du navigateur avec Selenium...")
                
                # Configuration des options Chrome
                chrome_options = Options()
                if self.browser_config.get('headless', False):
                    chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                
                # Chemin personnalisé du navigateur
                browser_path = self.browser_config.get('browser_path', '')
                if browser_path:
                    chrome_options.binary_location = browser_path
                
                # Configuration du répertoire de téléchargement
                download_dir = os.path.abspath(os.path.join(self.config['paths']['heygen']))
                prefs = {
                    "download.default_directory": download_dir,
                    "download.prompt_for_download": False,
                    "download.directory_upgrade": True,
                    "safebrowsing.enabled": True
                }
                chrome_options.add_experimental_option("prefs", prefs)
                
                # Initialiser le navigateur
                self.browser = webdriver.Chrome(options=chrome_options)
                self.browser.maximize_window()
                
                # Définir les timeouts
                timeouts = self.browser_config.get('timeouts', {})
                self.page_load_timeout = timeouts.get('page_load', 30)
                self.element_timeout = timeouts.get('element_visibility', 10)
                self.generation_timeout = timeouts.get('generation', 300)
                
                # Configurer les classes d'attente
                self.wait = WebDriverWait(self.browser, self.element_timeout)
                
                # Stocker les références aux classes Selenium pour une utilisation ultérieure
                self.selenium = {
                    'By': By,
                    'EC': EC
                }
                
                logging.info(f".... Répertoire de téléchargement configuré: {download_dir}")
                logging.info("Navigateur Selenium initialisé avec succès")
                return True
                
            except ImportError as e:
                logging.error(f"Impossible d'importer Selenium: {e}")
                return False
            except Exception as e:
                logging.error(f"Erreur lors de l'initialisation du navigateur Selenium: {str(e)}")
                return False
                
        elif self.automation_type == 'undetected_chromedriver':
            try:
                # Importation directe et simple
                logging.info("Tentative d'importation de undetected_chromedriver...")
                import undetected_chromedriver as uc
                
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                logging.info("Initialisation du navigateur avec Undetected Chromedriver...")
                
                # Configuration des options Chrome
                chrome_options = uc.ChromeOptions()
                chrome_options.add_argument("--start-maximized")
                
                # Configuration du répertoire de téléchargement
                download_dir = os.path.abspath(os.path.join(self.config['paths']['heygen']))
                prefs = {
                    "download.default_directory": download_dir,
                    "download.prompt_for_download": False,
                    "download.directory_upgrade": True,
                    "safebrowsing.enabled": True
                }
                chrome_options.add_experimental_option("prefs", prefs)
                
                # Initialiser le navigateur
                logging.info("Création de l'instance du navigateur...")
                self.browser = uc.Chrome(options=chrome_options)
                logging.info("Navigateur Chrome initialisé avec succès")
                
                # Définir les timeouts
                self.element_timeout = 10
                
                # Configurer les classes d'attente
                self.wait = WebDriverWait(self.browser, self.element_timeout)
                
                # Stocker les références aux classes Selenium
                self.selenium = {
                    'By': By,
                    'EC': EC
                }
                
                logging.info(f".... Répertoire de téléchargement configuré: {download_dir}")
                logging.info("Navigateur Undetected Chromedriver initialisé avec succès")
                return True
                
            except ImportError as e:
                logging.error(f"Impossible d'importer undetected_chromedriver: {e}")
                logging.error(f"Traceback complet: {traceback.format_exc()}")
                logging.error("Basculement vers Selenium standard")
                self.automation_type = 'selenium'
                return self.initialize_browser()
            except Exception as e:
                logging.error(f"Erreur lors de l'initialisation du navigateur Undetected Chromedriver: {str(e)}")
                logging.error(f"Traceback complet: {traceback.format_exc()}")
                logging.error("Basculement vers Selenium standard")
                self.automation_type = 'selenium'
                return self.initialize_browser()
                
        else:
            logging.error(f"Type d'automatisation non pris en charge: {self.automation_type}")
            return False

    def debug_wait(self, message="Pause de débogage"):
        """
        Ajoute une pause pour le débogage si le mode débogage est activé.
        
        Args:
            message (str): Message à afficher avant la pause
        """
        if hasattr(self, 'debug_mode') and self.debug_mode:
            logging.info(f"DEBUG: {message}. Pause de {self.debug_pause} secondes...")
            time.sleep(self.debug_pause)

    def login_to_heygen(self):
        """
        Se connecte à l'interface web de Heygen en utilisant les touches du clavier.
        
        Returns:
            WebDriver: L'objet driver du navigateur si la connexion a réussi, None sinon
        """
        if self.automation_type in ['selenium', 'undetected_chromedriver']:
            try:
                from selenium.webdriver.common.keys import Keys
                from selenium.webdriver.common.action_chains import ActionChains
                
                # Initialiser le navigateur si ce n'est pas déjà fait
                if not hasattr(self, 'browser') or self.browser is None:
                    if not self.initialize_browser():
                        logging.error("Échec de l'initialisation du navigateur")
                        return None
                
                # Accéder à la page de connexion
                self.browser.get('https://app.heygen.com/login')
                logging.info("Accès à la page de connexion Heygen")
                
                # Attendre 6 secondes
                time.sleep(6)
                
                # Prendre une . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran pour le débogage
                try:
                    screenshot_path = os.path.join(self.temp_path, 'login_page.png')
                    self.browser.save_screenshot(screenshot_path)
                    logging.info(f". . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran enregistrée: {screenshot_path}")
                except Exception as e:
                    logging.warning(f"Impossible de prendre une . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran: {str(e)}")
                
                # Méthode 1: Utiliser ActionChains pour envoyer des touches - pauses réduites
                try:
                    logging.info("Tentative de connexion avec ActionChains...")
                    actions = ActionChains(self.browser)
                    
                    # Envoyer TAB pour atteindre le champ email - pause réduite à 0.3s
                    actions.send_keys(Keys.TAB)
                    actions.pause(0.3)
                    
                    # Saisir l'email
                    actions.send_keys(self.browser_config['login']['email'])
                    actions.pause(0.3)
                    
                    # Envoyer TAB pour atteindre le champ mot de passe
                    actions.send_keys(Keys.TAB)
                    actions.pause(0.3)
                    
                    # Saisir le mot de passe
                    actions.send_keys(self.browser_config['login']['password'])
                    actions.pause(0.3)
                    
                    # Envoyer TAB pour atteindre le bouton de connexion
                    actions.send_keys(Keys.TAB)
                    actions.pause(0.3)
                    
                    # Appuyer sur ENTRÉE pour soumettre le formulaire
                    actions.send_keys(Keys.ENTER)
                    
                    # Exécuter toutes les actions
                    actions.perform()
                    logging.info("Actions exécutées avec succès")
                    
                    # Prendre une . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran après la tentative de connexion
                    try:
                        screenshot_path = os.path.join(self.temp_path, 'after_login_attempt.png')
                        self.browser.save_screenshot(screenshot_path)
                        logging.info(f". . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran après tentative: {screenshot_path}")
                    except Exception as e:
                        logging.warning(f"Impossible de prendre une . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran: {str(e)}")
                    
                    # Attendre un peu pour voir si la connexion a réussi
                    time.sleep(5)
                    
                    # Vérifier si nous sommes déjà connectés après la première méthode
                    if 'login' not in self.browser.current_url:
                        logging.info("Connexion réussie avec ActionChains")
                        
                        # Prendre une . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran finale
                        try:
                            screenshot_path = os.path.join(self.temp_path, 'final_page_actionchains.png')
                            self.browser.save_screenshot(screenshot_path)
                            logging.info(f". . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran finale: {screenshot_path}")
                        except Exception as e:
                            logging.warning(f"Impossible de prendre une . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran: {str(e)}")
                        
                        return self.browser
                    
                except Exception as e:
                    logging.error(f"Erreur lors de l'utilisation d'ActionChains: {str(e)}")
                
                # Si nous sommes toujours sur la page de connexion, essayer la méthode JavaScript
                logging.info("Première méthode non concluante, tentative avec JavaScript...")
                
                # Méthode 2: Utiliser JavaScript pour remplir les champs et soumettre le formulaire
                try:
                    logging.info("Tentative de connexion avec JavaScript...")
                    
                    # Remplir les champs avec JavaScript
                    self.browser.execute_script(f"""
                        // Trouver tous les champs de saisie
                        var inputs = document.querySelectorAll('input');
                        
                        // Remplir le champ email (généralement le premier input de type email)
                        var emailInput = document.querySelector('input[type="email"]');
                        if (emailInput) {{
                            emailInput.value = '{self.browser_config['login']['email']}';
                            // Déclencher un événement pour simuler la saisie utilisateur
                            emailInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            emailInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        }}
                        
                        // Remplir le champ mot de passe (généralement le premier input de type password)
                        var passwordInput = document.querySelector('input[type="password"]');
                        if (passwordInput) {{
                            passwordInput.value = '{self.browser_config['login']['password']}';
                            // Déclencher un événement pour simuler la saisie utilisateur
                            passwordInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            passwordInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        }}
                        
                        // Soumettre le formulaire
                        var form = document.querySelector('form');
                        if (form) {{
                            form.submit();
                        }} else {{
                            // Si pas de formulaire, chercher le bouton de connexion et cliquer dessus
                            var loginButton = document.querySelector('button[type="submit"]');
                            if (loginButton) {{
                                loginButton.click();
                            }}
                        }}
                    """)
                    logging.info("JavaScript exécuté avec succès")
                    
                    # Prendre une . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran après la tentative de connexion
                    try:
                        screenshot_path = os.path.join(self.temp_path, 'after_js_login.png')
                        self.browser.save_screenshot(screenshot_path)
                        logging.info(f". . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran après JS: {screenshot_path}")
                    except Exception as e:
                        logging.warning(f"Impossible de prendre une . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran: {str(e)}")
                except Exception as e:
                    logging.error(f"Erreur lors de l'utilisation de JavaScript: {str(e)}")
                
                # Attendre 8 secondes
                time.sleep(8)
                
                # Prendre une . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran finale
                try:
                    screenshot_path = os.path.join(self.temp_path, 'final_page.png')
                    self.browser.save_screenshot(screenshot_path)
                    logging.info(f". . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran finale: {screenshot_path}")
                except Exception as e:
                    logging.warning(f"Impossible de prendre une . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran: {str(e)}")
                
                # Vérifier si nous sommes connectés
                if 'login' not in self.browser.current_url:
                    logging.info("Connexion à Heygen réussie")
                    return self.browser  # Retourner l'objet driver au lieu de True
                else:
                    logging.error("Échec de la connexion à Heygen")
                    return None
                    
            except Exception as e:
                logging.error(f"Erreur lors de la connexion à Heygen: {str(e)}")
                return None
                
        elif self.automation_type == 'playwright':
            try:
                # Accéder à la page de connexion
                self.page.goto('https://app.heygen.com/login', timeout=60000)  # 60 secondes
                logging.info("Accès à la page de connexion Heygen")
                
                # Attendre 5 secondes
                time.sleep(5)
                
                # Remplir les informations de connexion
                self.page.fill('input[type="email"]', self.browser_config['login']['email'])
                self.page.fill('input[type="password"]', self.browser_config['login']['password'])
                
                # Cliquer sur le bouton de connexion
                self.page.click('button[type="submit"]')
                
                # Attendre que la page d'accueil se charge
                try:
                    # Attente d'un conteneur générique si nécessaire (dashboard supprimé)
                    self.page.wait_for_selector('body', timeout=30000)
                    logging.info("Connexion à Heygen réussie")
                    return self.page  # Retourner l'objet page au lieu de True
                except:
                    logging.error("Échec de la connexion à Heygen")
                    return None
                    
            except Exception as e:
                logging.error(f"Erreur lors de la connexion à Heygen: {str(e)}")
                return None
        else:
            logging.error("Type d'automatisation non pris en charge")
            return None

    def take_screenshot(self, driver, name):
        """
        Prend une . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran du navigateur.
        
        Args:
            driver: Le driver Selenium.
            name (str): Le nom de la . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran.
        """
        try:
            screenshot_dir = os.path.join(self.config['paths']['temp'], 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(screenshot_dir, f"{name}_{int(time.time())}.png")
            driver.save_screenshot(screenshot_path)
            logging.info(f". . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran enregistrée: {screenshot_path}")
        except Exception as e:
            logging.error(f"Erreur lors de la prise de . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran: {str(e)}")

    def generate_video_with_browser(self, text, index):
        """Génère une vidéo en utilisant le navigateur web"""

        time.sleep(3)

        try:
            # Nettoyer le dossier screenshots au démarrage
            screenshots_dir = Path("temp/screenshots")
            if screenshots_dir.exists():
                logging.info("Nettoyage du dossier screenshots...")
                for screenshot in screenshots_dir.glob("*.png"):
                    try:
                        screenshot.unlink()
                        logging.info(f".... Suppression de {screenshot.name}")
                    except Exception as e:
                        logging.warning(f".... Impossible de supprimer {screenshot.name}: {str(e)}")
            else:
                logging.info("Création du dossier screenshots...")
                screenshots_dir.mkdir(parents=True, exist_ok=True)

            driver = self.browser
            if not driver:
                logging.error("Le navigateur n'est pas initialisé")
                return None

            # Sélectionner un avatar aléatoire depuis la liste heygen_avatars_with_browser
            avatar_list = self.config.get('heygen_avatars_with_browser', [])
            if not avatar_list:
                logging.warning("Liste heygen_avatars_with_browser vide dans config.yml, utilisation de l'avatar par défaut")
                avatar = "Gala Casual Sofa with iPad Front"
            else:
                avatar = random.choice(avatar_list)
            
            logging.info(f"Utilisation de l'avatar: {avatar}")
            
            try:
                # Naviguer vers la page de création
                create_url = "https://app.heygen.com/create-v3/draft?vt=l"
                driver.get(create_url)
                
                # Zoomer à 50%
                driver.execute_script("document.body.style.zoom = '50%';")
                
                # Attendre 5 secondes pour que la page se charge complètement
                logging.info("Attente de 10 secondes pour le chargement complet de la page...")
                time.sleep(10)
                
                # Prendre une . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran après navigation
                self.take_screenshot(driver, "after_navigate_to_create")
                
                # Chercher et cliquer sur l'input de recherche
                logging.info("Recherche de l'input de recherche...")
                try:
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    from selenium.webdriver.common.keys import Keys
                    
                    # Attendre que l'input de recherche soit visible et cliquable
                    wait = WebDriverWait(driver, 10)
                    search_input = wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "div > div > input[placeholder='Search']"))
                    )
                    
                    # Prendre une . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran avant de cliquer sur l'input
                    self.take_screenshot(driver, "before_click_search_input")
                    
                    # Cliquer sur l'input de recherche
                    search_input.click()
                    logging.info("Clic sur l'input de recherche réussi")
                    
                    # Attendre un court instant
                    time.sleep(1)
                    
                    # Prendre une . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran après avoir cliqué sur l'input
                    self.take_screenshot(driver, "after_click_search_input")
                    
                    # Extraire le nom de l'avatar pour la recherche (avant le premier espace ou tout l'avatar si pas d'espace)
                    search_term = avatar.split(' ')[0]
                    logging.info(f"Saisie du terme de recherche '{search_term}'...")
                    search_input.clear()
                    search_input.send_keys(search_term)
                    
                    # Prendre une capture d'écran après avoir saisi le terme de recherche
                    self.take_screenshot(driver, f"after_typing_{search_term}")
                    
                    # Attendre 3 secondes pour que les résultats de recherche s'affichent
                    logging.info("Attente de 3 secondes pour l'affichage des résultats...")
                    time.sleep(3)
                    
                    # Prendre une capture d'écran des résultats de recherche
                    self.take_screenshot(driver, f"search_results_{search_term}")
                    
                    # Cliquer sur le terme de recherche dans les résultats pour filtrer les avatars
                    try:
                        # Chercher le terme de recherche dans la liste des résultats
                        search_result = wait.until(
                            EC.element_to_be_clickable((By.XPATH, f"//label[@title='{search_term}'][text()='{search_term}']"))
                        )
                        
                        # Prendre une capture d'écran avant de cliquer sur le terme de recherche
                        self.take_screenshot(driver, f"before_click_search_term_{search_term}")
                        
                        # Cliquer sur le terme de recherche
                        search_result.click()
                        logging.info(f"Clic sur le terme de recherche '{search_term}' réussi")

                        
                        # Attendre 3 secondes pour que les filtres s'appliquent et que les avatars correspondants s'affichent
                        logging.info("Attente de 3 secondes pour l'application des filtres...")
                        time.sleep(3)
                        
                        # Prendre une capture d'écran après avoir cliqué sur le terme de recherche
                        self.take_screenshot(driver, f"after_click_search_term_{search_term}")
                    except Exception as e:
                        logging.warning(f".... Impossible de cliquer sur le terme de recherche '{search_term}': {e}")
                        logging.info(".... Tentative de recherche directe de l'avatar sans filtrer")
                    


                    # Faire défiler la page pour s'assurer que les avatars sont visibles
                    logging.info("Défilement de la page pour rendre les avatars visibles...")
                    driver.execute_script("""
                        // Chercher un div draggable (avatar)
                        var element = document.querySelector('div[draggable="true"][data-active="false"]');

                        if (element) {
                            // Simuler un hover en déclenchant un événement "mouseenter"
                            var event = new MouseEvent("mouseenter", {
                                bubbles: true,
                                cancelable: true,
                                view: window
                            });
                            element.dispatchEvent(event);
                            
                            // Trouver le 4ᵉ parent du div cible
                            var scrollContainer = element;
                            for (let i = 0; i < 4; i++) {
                                if (scrollContainer.parentElement) {
                                    scrollContainer = scrollContainer.parentElement;
                                } else {
                                    console.error("Moins de 4 parents disponibles, utilisation du parent le plus haut trouvé.");
                                    break;
                                }
                            }

                            // Scroller immédiatement de 900px vers le bas
                            scrollContainer.scrollBy({ top: 00, behavior: "smooth" });

                            console.log("Hover simulé et scroll effectué sur le bon div !");
                            return true;
                        } else {
                            console.error("Élément draggable non trouvé !");
                            return false;
                        }
                    """)

                    # Attendre que le défilement soit terminé
                    time.sleep(2)
                    
                    # Chercher et cliquer sur l'avatar sélectionné avec JavaScript (plus robuste)
                    logging.info(f"Clic sur '{avatar}' avec JavaScript...")
                    driver.execute_script(f"""
                        var avatarElement = document.querySelector('div[title="{avatar}"]');
                        if (avatarElement) {{
                            avatarElement.click();
                        }} else {{
                            console.error("Élément '{avatar}' non trouvé");
                            // Recherche alternative avec texte contenant
                            var alternativeElements = Array.from(document.querySelectorAll('div[title]')).filter(el => 
                                el.title.toLowerCase().includes("{avatar.lower()}"));
                            if (alternativeElements.length > 0) {{
                                alternativeElements[0].click();
                                console.log("Élément alternatif trouvé et cliqué");
                            }}
                        }}
                    """)
                    
                    # Attendre un court instant
                    time.sleep(1)
                    
                    # Prendre une . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran après avoir cliqué sur l'élément
                    self.take_screenshot(driver, f"after_click_{search_term}")
                    
                    # Attendre 3 secondes après avoir cliqué sur l'avatar
                    logging.info("Attente de 3 secondes après la sélection de l'avatar...")
                    time.sleep(3)
                    
                    # Appeler notre nouvelle fonction _choose_voice_and_fill_text
                    if self._choose_voice_and_fill_text(driver, wait, text):
                        return self._submit_and_download(driver, wait, index)
                    else:
                        logging.error("Échec du choix de la voix et de la saisie du texte")
                        return None
                
                except Exception as e:
                    logging.error(f"Erreur E : {e}")
                    logging.error(traceback.format_exc())
                    self.take_screenshot(driver, "error_e")
                return None
                
            except Exception as e:
                logging.error(f"Erreur lors de la sélection de l'avatar: {e}")
                logging.error(traceback.format_exc())
                self.take_screenshot(driver, "error_selecting_avatar")
                return None
                
        except Exception as e:
            logging.error(traceback.format_exc())
            if 'driver' in locals():
                self.take_screenshot(driver, "error_during_generation")
            return None

    def monitor_and_download_video(self, first_video, index, driver):
        """Surveille la progression de la vidéo et la télécharge une fois prête"""
        try:
            from selenium.webdriver.common.by import By
            from selenium.common.exceptions import NoSuchElementException
            from selenium.webdriver.common.action_chains import ActionChains
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # Si wait_and_download est désactivé, attendre 10s et passer au suivant
            if not self.wait_and_download:
                logging.info(f".... Paramètre wait_and_download désactivé. Attente de 10 secondes puis passage au rush suivant...")
                time.sleep(10)
                logging.info(f".... Rush {index} soumis, passage au suivant (téléchargement manuel requis)")
                # Revenir à la page de création pour la prochaine vidéo
                driver.get("https://app.heygen.com/create-v3/draft?vt=l")
                time.sleep(5)  # Attendre que la page se charge
                return True
            
            # Variable pour suivre si on a déjà vu le span "Ready"
            has_seen_ready = False
            
            # Boucle de surveillance de la progression
            while True:
                try:
                    # Chercher le span de progression
                    ready_span = first_video.find_element(By.XPATH, ".//span[contains(., 'Ready')]")
                    has_seen_ready = True
                    
                    # Extraire et logger le pourcentage
                    progress_text = ready_span.text
                    percentage_match = re.search(r'(\d+).*Ready', progress_text)
                    if percentage_match:
                        percentage = percentage_match.group(1)
                        logging.info(f".... Progression de la vidéo: {percentage}%")
                    
                    # Attendre 20 secondes avant la prochaine vérification
                    time.sleep(20)
                except NoSuchElementException:
                    # Si le span "Ready" n'est plus trouvé et qu'on l'a vu avant
                    if has_seen_ready:
                        logging.info(".... Vidéo prête! Téléchargement en cours...")
                        
                        # Prendre une capture d'écran avant de tenter le téléchargement
                        screenshot_path = os.path.join(self.config['paths']['temp'], "screenshots", f"before_download_{int(time.time())}.png")
                        driver.save_screenshot(screenshot_path)
                        logging.info(f".... Capture d'écran avant téléchargement: {screenshot_path}")
                        
                        # Approche 1: Survoler d'abord la vignette pour faire apparaître le bouton
                        try:
                            # Survoler la vignette pour faire apparaître les contrôles
                            actions = ActionChains(driver)
                            actions.move_to_element(first_video).perform()
                            logging.info(".... Survol de la vignette effectué")
                            time.sleep(2)  # Attendre que les contrôles apparaissent
                            
                            # Chercher et cliquer sur le bouton "More" (trois points)
                            more_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, ".//button[@data-more-btn='true']"))
                            )
                            
                            more_button.click()
                            logging.info(".... Clic sur le bouton 'More' réussi")
                            time.sleep(2)
                            
                            # Chercher et cliquer sur l'option de téléchargement
                            download_option = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, "//li[contains(@class, 'rc-menu-item')][contains(., 'Download')]"))
                            )
                            
                            download_option.click()
                            logging.info(".... Clic sur l'option 'Download' réussi")
                            
                            # Attendre que le téléchargement soit terminé
                            time.sleep(10)
                            logging.info(f".... Téléchargement de la vidéo {index} terminé")
                            
                            # Au lieu de retourner True, on continue pour la prochaine vidéo
                            # Revenir à la page de création
                            logging.info(".... Navigation vers la page de création pour la prochaine vidéo...")
                            driver.get("https://app.heygen.com/create-v3/draft?vt=l")
                            time.sleep(5)  # Attendre que la page se charge
                            
                            return True
                        except Exception as e:
                            logging.error(f".... Erreur lors de l'approche 1 pour le téléchargement: {e}")
                            
                            # Approche 2: Utiliser JavaScript pour cliquer directement
                            try:
                                logging.info(".... Tentative avec JavaScript...")
                                # Trouver le bouton avec JavaScript
                                js_script = """
                                let videoCard = arguments[0];
                                let moreBtn = videoCard.querySelector('button[data-more-btn="true"]');
                                if (moreBtn) {
                                    moreBtn.click();
                                    return true;
                                }
                                return false;
                                """
                                result = driver.execute_script(js_script, first_video)
                                
                                if result:
                                    logging.info(".... Clic JavaScript sur le bouton 'More' réussi")
                                    time.sleep(2)
                                    
                                    # Cliquer sur l'option de téléchargement
                                    download_js = """
                                    let downloadOption = document.querySelector('li.rc-menu-item:contains("Download")');
                                    if (downloadOption) {
                                        downloadOption.click();
                                        return true;
                                    }
                                    return false;
                                    """
                                    download_result = driver.execute_script(download_js)
                                    
                                    if download_result:
                                        logging.info(".... Clic JavaScript sur l'option 'Download' réussi")
                                        time.sleep(10)
                                        logging.info(f".... Téléchargement de la vidéo {index} terminé")
                                        
                                        # Au lieu de retourner True, on continue pour la prochaine vidéo
                                        # Revenir à la page de création
                                        logging.info(".... Navigation vers la page de création pour la prochaine vidéo...")
                                        driver.get("https://app.heygen.com/create-v3/draft?vt=l")
                                        time.sleep(5)  # Attendre que la page se charge
                                        
                                        return True
                                
                                logging.error(".... Échec de l'approche JavaScript")
                                return False
                            except Exception as js_error:
                                logging.error(f".... Erreur lors de l'approche JavaScript: {js_error}")
                                return False
                    else:
                        # Continuer à chercher le span "Ready"
                        logging.info(".... En attente du début de la génération...")
                        time.sleep(10)
                    
        except Exception as e:
            logging.error(f"Erreur lors de la surveillance ou du téléchargement de la vidéo: {e}")
            if driver:
                screenshot_path = os.path.join(self.config['paths']['temp'], "screenshots", f"error_download_{int(time.time())}.png")
                driver.save_screenshot(screenshot_path)
                logging.info(f".... Capture d'écran enregistrée: {screenshot_path}")
            return False

    def close_browser(self):
        """
        Ferme le navigateur.
        """
        if self.browser:
            try:
                if self.automation_type in ['selenium', 'undetected_chromedriver']:
                    self.browser.quit()
                elif self.automation_type == 'playwright':
                    self.browser.close()
                    self.playwright.stop()
                logging.info("Navigateur fermé")
            except Exception as e:
                logging.error(f"Erreur lors de la fermeture du navigateur: {str(e)}")

    def read_i3_script(self):
        """
        Lit le fichier i3.txt du dossier temp.
        
        Returns:
            list: Liste des paragraphes du script
        """
        i3_path = self.temp_path / 'i3.txt'
        if not i3_path.exists():
            raise FileNotFoundError(
                "Le fichier i3.txt est manquant. "
                "Veuillez d'abord exécuter l'étape de script avec -s"
            )
        try:
            with open(i3_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return [p.strip() for p in content.split('\n\n') if p.strip()]
        except Exception as e:
            logging.error(f"Erreur lors de la lecture du fichier i3.txt: {e}")
            raise

    def select_random_avatar(self):
        """
        Sélectionne un avatar aléatoire dans la liste.
        
        Returns:
            str: Nom de l'avatar sélectionné
        """
        return random.choice(self.avatars)

    def create_video_request(self, text, avatar):
        """
        Crée la requête pour l'API Heygen.
        
        Args:
            text (str): Texte à dire par l'avatar
            avatar (str): ID de l'avatar à utiliser
            
        Returns:
            dict: Requête formatée pour l'API
        """
        # Format de requête pour l'API v2
        request_v2 = {
            "video_inputs": [
                {
                    "avatar": {
                        "avatar_id": avatar
                    },
                    "voice": {
                        "type": "text",
                        "input_text": text,
                        "voice_id": self.voice_config['id'],
                        "name": self.voice_config['name'],
                        "settings": {
                            "stability": self.voice_config['stability'],
                            "similarity": self.voice_config['clarity_similarity'],
                            "style": self.voice_config['style_exaggeration'],
                            "speed": self.voice_config['speed']
                        }
                    }
                    # Omission du champ background pour utiliser le background par défaut de l'avatar
                }
            ],
            # Utilisation de la résolution définie dans le fichier de configuration
            "dimension": {
                "width": self.config['video']['resolution']['width'],
                "height": self.config['video']['resolution']['height']
            }
        }
        
        return request_v2

    def submit_video_generation(self, request_data):
        """
        Soumet une requête de génération de vidéo à Heygen.
        
        Args:
            request_data (dict): Données de la requête
            
        Returns:
            str: ID de la vidéo en cours de génération
        """
        try:
            # Utiliser l'endpoint v2 qui a fonctionné pour la liste des avatars
            endpoint = 'https://api.heygen.com/v2/video/generate'
            logging.info(f"Soumission de la requête à {endpoint}")
            logging.info(f"Données de la requête: {json.dumps(request_data, indent=2)}")
            
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=request_data
            )
            
            logging.info(f"Statut de la réponse: {response.status_code}")
            if response.status_code == 200 or response.status_code == 201:
                response_data = response.json()
                logging.info(f"Réponse API: {response_data}")
                
                # Adapter l'extraction de l'ID vidéo selon la structure de la réponse
                if 'data' in response_data and 'video_id' in response_data['data']:
                    return response_data['data']['video_id']
                elif 'video_id' in response_data:
                    return response_data['video_id']
                else:
                    raise ValueError(f"Format de réponse inattendu: {response_data}")
            else:
                if hasattr(response, 'text'):
                    logging.error(f"Détails de l'erreur: {response.text}")
                raise ValueError(f"Échec de la génération de vidéo: {response.status_code}")
                
        except Exception as e:
            logging.error(f"Erreur lors de la soumission de la vidéo: {e}")
            if hasattr(e, 'response') and e.response:
                logging.error(f"Détails de l'erreur: {e.response.text}")
            raise

    def check_video_status(self, video_id):
        """
        Vérifie le statut d'une vidéo en cours de génération.
        
        Args:
            video_id (str): ID de la vidéo
            
        Returns:
            tuple: (bool, str) - (est_terminé, url_de_téléchargement)
        """
        try:
            # Utiliser l'endpoint correct selon la documentation officielle
            endpoint = 'https://api.heygen.com/v1/video_status.get'
            logging.info(f"Vérification du statut avec l'endpoint: {endpoint}")
            
            # Préparer les paramètres de la requête
            params = {'video_id': video_id}
            
            response = requests.get(
                endpoint,
                headers=self.headers,
                params=params
            )
            
            logging.info(f"Statut de la réponse: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                logging.info(f"Réponse API: {response_data}")
                
                # Extraire les données selon la structure de la réponse
                if 'data' in response_data:
                    status_data = response_data['data']
                    
                    if 'status' in status_data:
                        status = status_data['status']
                        logging.info(f"Statut de la vidéo: {status}")
                        
                        if status == 'completed':
                            video_url = status_data.get('video_url', '')
                            if video_url:
                                return True, video_url
                            else:
                                logging.warning("Vidéo complétée mais URL manquante")
                                return False, None
                        elif status in ['processing', 'waiting', 'pending']:
                            return False, None
                        elif status == 'failed':
                            error_info = status_data.get('error', {})
                            error_message = error_info.get('message', 'Erreur inconnue')
                            error_detail = error_info.get('detail', '')
                            logging.error(f"Échec de la génération de vidéo: {error_message} - {error_detail}")
                            raise ValueError(f"Échec de la génération de vidéo: {error_message}")
                        else:
                            logging.warning(f"Statut de vidéo inconnu: {status}")
                            return False, None
                    else:
                        raise ValueError(f"Format de réponse inattendu: champ 'status' manquant")
                else:
                    raise ValueError(f"Format de réponse inattendu: champ 'data' manquant")
            else:
                if hasattr(response, 'text'):
                    logging.error(f"Détails de l'erreur: {response.text}")
                raise ValueError(f"Échec de la vérification du statut: {response.status_code}")
                
        except Exception as e:
            logging.error(f"Erreur lors de la vérification du statut: {e}")
            if hasattr(e, 'response') and e.response:
                logging.error(f"Détails de l'erreur: {e.response.text}")
            raise

    def download_video(self, url, output_file):
        """
        Télécharge une vidéo générée.
        
        Args:
            url (str): URL de téléchargement
            output_file (Path): Chemin de destination
        """
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logging.info(f"Vidéo téléchargée: {output_file}")
            
        except Exception as e:
            logging.error(f"Erreur lors du téléchargement de la vidéo: {e}")
            raise

    def generate_video(self, text, index):
        """
        Génère une vidéo pour un paragraphe.
        
        Args:
            text (str): Texte du paragraphe
            index (int): Numéro du paragraphe
            
        Returns:
            Path: Chemin vers la vidéo générée
        """
        avatar = self.select_random_avatar()
        
        if self.generation_mode == 'api':
            # Génération via l'API
            request_data = self.create_video_request(text, avatar)
            
            logging.info(f"Génération de la vidéo {index} avec l'avatar {avatar} via l'API")
            video_id = self.submit_video_generation(request_data)
            
            # Attente et vérification du statut
            checks = 0
            while checks < self.max_checks:
                logging.info(f"Vérification du statut de la vidéo {index} (tentative {checks + 1}/{self.max_checks})")
                is_ready, download_url = self.check_video_status(video_id)
                
                if is_ready:
                    output_file = self.output_path / f"heygen{index:03d}.mp4"
                    self.download_video(download_url, output_file)
                    return output_file
                
                logging.info(f"Vidéo {index} toujours en génération. Nouvelle vérification dans {self.check_interval} secondes...")
                checks += 1
                time.sleep(self.check_interval)
                
            raise TimeoutError(f"Délai dépassé pour la génération de la vidéo {index}")
            
        else:
            # Génération via le navigateur
            return self.generate_video_with_browser(text, index)

    def launch_debug_browser(self):
        """
        Lance un navigateur Chrome avec undetected_chromedriver en mode headfull pour le débogage.
        
        Returns:
            bool: True si le lancement a réussi, False sinon
        """
        logging.info("Lancement du navigateur en mode débogage...")
        
        # Utiliser la méthode initialize_browser standard
        try:
            result = self.initialize_browser()
            if result:
                logging.info("Navigateur lancé avec succès en mode débogage")
                
                # Tester la navigation vers une page simple
                try:
                    self.browser.get("https://www.google.com")
                    logging.info(f"Navigation réussie vers Google. Titre: {self.browser.title}")
                except Exception as e:
                    logging.error(f"Erreur lors de la navigation test: {str(e)}")
            else:
                logging.error("Échec du lancement du navigateur en mode débogage")
            return result
        except Exception as e:
            logging.error(f"Exception lors du lancement du navigateur en mode débogage: {str(e)}")
            logging.error(f"Traceback complet: {traceback.format_exc()}")
            return False

    def generate_videos(self, max_videos=None):
        """
        Génère les vidéos Heygen pour tous les paragraphes du script I3.
        
        Args:
            max_videos (int): Nombre maximum de vidéos à générer (défaut: depuis la config)
        """
        if max_videos is None:
            max_videos = self.config['script']['paragraphs']
        
        logging.info(f"Génération de {max_videos} vidéos Heygen")
        
        # Vérifier qu'il y a des avatars disponibles
        if not self.avatars:
            logging.error("Aucun avatar disponible, impossible de générer des vidéos")
            if self.generation_mode == 'browser':
                self.close_browser()
            return
        
        # Lecture du script I3
        paragraphs = self.read_i3_script()
        expected_paragraphs = self.config['script']['paragraphs']
        if len(paragraphs) < expected_paragraphs:
            raise ValueError(f"Le script I3 doit contenir au minimum {expected_paragraphs} paragraphes, trouvé: {len(paragraphs)}")
        elif len(paragraphs) > expected_paragraphs:
            logging.info(f"ℹ️  Script I3 contient {len(paragraphs)} paragraphes (attendu: {expected_paragraphs}) - génération de vidéo plus longue")
        
        # Limiter le nombre de paragraphes à traiter
        paragraphs_to_process = paragraphs[:max_videos]
        logging.info(f"Génération de {len(paragraphs_to_process)}/{len(paragraphs)} vidéos Heygen")
        
        try:
            # Si nous sommes en mode débogage avec undetected_chromedriver, attendre l'interaction manuelle
            if self.generation_mode == 'browser' and self.automation_type == 'undetected_chromedriver':
                logging.info("Mode débogage activé. Veuillez interagir manuellement avec le navigateur.")
                logging.info("Le script attendra votre interaction. Appuyez sur Ctrl+C pour arrêter le script.")
                
                # Attendre indéfiniment (jusqu'à ce que l'utilisateur arrête le script)
                try:
                    while True:
                        time.sleep(10)
                        logging.info("Script en attente... Appuyez sur Ctrl+C pour arrêter.")
                except KeyboardInterrupt:
                    logging.info("Script arrêté par l'utilisateur.")
                    return
            else:
                # Génération automatique des vidéos
                for i, paragraph in enumerate(paragraphs_to_process, 1):
                    logging.info(f"Traitement du paragraphe {i}/{len(paragraphs_to_process)}")
                    try:
                        self.generate_video(paragraph, i)
                    except Exception as e:
                        logging.error(f"Erreur lors de la génération de la vidéo {i}: {e}")
                        break
                    
                logging.info(f"Génération de vidéos terminée")
            
        finally:
            # Fermer le navigateur si en mode browser
            if self.generation_mode == 'browser' and self.browser:
                # En mode débogage, demander confirmation avant de fermer le navigateur
                if self.automation_type == 'undetected_chromedriver':
                    try:
                        input("Appuyez sur Entrée pour fermer le navigateur...")
                    except:
                        pass
                self.close_browser() 

    def _submit_and_download(self, driver, wait, index):
        """
        Soumet la vidéo à Heygen et gère le téléchargement.
        
        Args:
            driver: Le navigateur WebDriver
            wait: L'objet WebDriverWait
            index: L'index de la vidéo
            
        Returns:
            Path: Le chemin vers la vidéo téléchargée, ou None en cas d'erreur
        """
        By = self.selenium['By']
        EC = self.selenium['EC']
        
        try:
            # Attendre que l'icône Submit soit cliquable
            logging.info(".... Recherche de l'icône iconpark-icon avec le chemin complet...")
            icon_xpath = "#root > div > div > div > div > div > div > div > div > div > button > span > iconpark-icon"
            icon_element = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, icon_xpath))
            )
            
            # Prendre une capture de l'icône avant le clic
            screenshot_path = str(Path("temp/screenshots") / f"icon_before_click_{int(time.time())}.png")
            icon_element.screenshot(screenshot_path)
            logging.info(f".... Capture d'écran de l'icône enregistrée: {screenshot_path}")
            
            # Cliquer sur l'icône
            icon_element.click()
            logging.info(".... Clic sur l'icône iconpark-icon réussi")
            
            # Attendre 2 secondes
            logging.info(".... DEBUG Attente de 2 secondes après le clic sur l'icône...")
            time.sleep(2)
            
            # Sélectionner tout le texte existant et le supprimer avant de taper "rush" + index
            try:
                actions = ActionChains(driver)
                
                # Utiliser CMD+A sur Mac ou CTRL+A sur Windows/Linux
                if platform.system() == 'Darwin':  # Mac OS
                    actions.key_down(Keys.COMMAND).send_keys('a').key_up(Keys.COMMAND)
                else:  # Windows/Linux
                    actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL)
                
                # Effacer le texte existant
                actions.send_keys(Keys.DELETE)
                actions.perform()
                time.sleep(0.5)
                
                # Saisir le nom du rush (ligne manquante réintégrée)
                actions = ActionChains(driver)
                actions.send_keys(f"rush{index}")
                actions.perform()
                logging.info(f".... Saisie de 'rush{index}' effectuée")
                time.sleep(0.5)
                
            except Exception as e:
                logging.error(f".... Erreur lors de la saisie de 'rush{index}': {e}")
                time.sleep(999)
            
            # Rechercher le div contenant "HeyGen Watermark"
            logging.info(".... Recherche du div contenant 'HeyGen Watermark'...")
            watermark_xpath = "//div[contains(text(), 'HeyGen Watermark')]"
            watermark_element = wait.until(
                EC.element_to_be_clickable((By.XPATH, watermark_xpath))
            )
            
            # Prendre une capture du div watermark avant le clic
            screenshot_path = str(Path("temp/screenshots") / f"watermark_before_click_{int(time.time())}.png")
            watermark_element.screenshot(screenshot_path)
            logging.info(f".... Capture d'écran du watermark enregistrée: {screenshot_path}")
            
            # Attendre 1 seconde
            time.sleep(1)
            
            # Rechercher le bouton Submit dans le parent du div watermark
            logging.info(".... Recherche du bouton Submit...")
            submit_button = watermark_element.find_element(By.XPATH, 
                "..//button[.//span[text()='Submit']]"
            )
            
            # Prendre une capture du bouton Submit avant le clic
            screenshot_path = str(Path("temp/screenshots") / f"submit_button_before_click_{int(time.time())}.png")
            submit_button.screenshot(screenshot_path)
            logging.info(f".... Capture d'écran du bouton Submit enregistrée: {screenshot_path}")
            
            # Cliquer sur le bouton Submit
            submit_button.click()
            logging.info(".... Clic sur le bouton Submit réussi")

            # Attendre 30 secondes
            time.sleep(30)
            
            # Naviguer vers la page des projets
            logging.info(".... Navigation vers la page des projets...")
            driver.get("https://app.heygen.com/projects")
            
            # Attendre que la première video-card soit présente
            logging.info(".... Recherche de la première video-card...")
            first_video = wait.until(
                EC.presence_of_element_located((By.XPATH, "(//div[contains(@class, 'video-card')])[1]"))
            )
            # Prendre une capture de la première video-card
            screenshot_path = str(Path("temp/screenshots") / f"first_video_card_{int(time.time())}.png")
            first_video.screenshot(screenshot_path)
            logging.info(f".... Capture d'écran de la video-card enregistrée: {screenshot_path}")
            
            # Appeler la fonction de surveillance et téléchargement en passant le driver
            return self.monitor_and_download_video(first_video, index, driver)
            
        except Exception as e:
            logging.error(f"Erreur lors de la soumission et du téléchargement: {e}")
            logging.error(traceback.format_exc())
            return None

    def _choose_voice_and_fill_text(self, driver, wait, text):

        """
        Remplit le texte du script et sélectionne la voix appropriée.
        
        Args:
            driver: Le navigateur WebDriver
            wait: L'objet WebDriverWait
            text: Le texte à saisir
            
        Returns:
            bool: True si l'opération est réussie, False sinon
        """
        By = self.selenium['By']
        EC = self.selenium['EC']
        
        try:
            # Cliquer sur le span "Script"
            logging.info("Recherche et clic sur le span 'Script'...")
            script_span = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Script']"))
            )
            
            # Prendre une . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran avant de cliquer sur Script
            self.take_screenshot(driver, "before_click_script_span")
            
            # ------------------------------------------------------------
            # Cliquer sur le span Script
            # modification du texte
            # ------------------------------------------------------------
            script_span.click()
            logging.info("Clic sur le span 'Script' réussi")
            
            # Attendre 2 secondes
            logging.info("Attente de 2 secondes après le clic sur 'Script'...")
            time.sleep(2)
            
            # Prendre une . . .  . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran après avoir cliqué sur Script
            self.take_screenshot(driver, "after_click_script_span")
            
            
            
            
            # Cliquer sur "Gala - Lifelike"
            logging.info("Recherche et clic sur 'Gala - Lifelike'...")
            gala_lifelike_span = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Gala - Lifelike']"))
            )
            
            # Prendre une . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran avant de cliquer
            self.take_screenshot(driver, "before_click_gala_lifelike")
            
            # Cliquer sur "Gala - Lifelike"
            gala_lifelike_span.click()
            logging.info("Clic sur 'Gala - Lifelike' réussi")
            
            # Attendre 1 seconde
            time.sleep(1)
            
            # Prendre une . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran après avoir cliqué
            self.take_screenshot(driver, "after_click_gala_lifelike")
            
            # Cliquer sur "My Voices"
            logging.info("Recherche et clic sur 'My Voices'...")
            my_voices_div = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[text()='My Voices']"))
            )
            
            # Prendre une . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran avant de cliquer
            self.take_screenshot(driver, "before_click_my_voices")
            
            # Cliquer sur "My Voices"
            my_voices_div.click()
            logging.info("Clic sur 'My Voices' réussi")
            
            # Attendre 1 seconde
            time.sleep(1)
            
            # Prendre une . . .  . . .  . . .  . . .  . . .  . . .  . . .  Capture d'écran après avoir cliqué
            self.take_screenshot(driver, "after_click_my_voices")
            
            # Trouver et cliquer sur le parent du parent du parent du parent de "FAV-delf-micro-cravatte-with-amb"
            logging.info("Recherche de 'FAV-delf-micro-cravatte-with-amb' et clic sur son parent éloigné...")
            logging.info("debug-rang1")
            time.sleep(1)
            # Trouver d'abord l'élément span contenant le texte
            fav_span = wait.until(
                # EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'FAV-delf-micro-cravatte-with-amb')]"))
                EC.presence_of_element_located((By.XPATH, "//div[@title='FAV-delf-micro-cravatte-with-amb']"))
            )

            logging.info("debug-rang2")

            screenshot_path1 = str(Path("temp/screenshots") / f"fav_span_{int(time.time())}.png")
            fav_span.screenshot(screenshot_path1)
            logging.info("debug-rang3")

            # Attendre 1 seconde
            logging.info("sleep 2")
            time.sleep(2)
            
            # Naviguer vers le parent du parent du parent du parent du fav delf micro cravatte with amb
            parent_element = fav_span
            for _ in range(2):
                parent_element = parent_element.find_element(By.XPATH, "..")
                logging.info("debug-rang5")
                # Vérifier que l'élément existe et est un div
                
            if not parent_element.tag_name.lower() == 'div':
                logging.info("debug-rang6")
                logging.warning(f".... L'élément parent trouvé est un {parent_element.tag_name}, attendu: div")
                raise Exception("L'élément parent n'est pas un div")
            
            logging.info("debug-rang7")
            # Vérifier que l'élément final est cliquable
            if parent_element and parent_element.is_displayed() and parent_element.is_enabled():
                logging.info("debug-rang8")
                # Prendre une capture d'écran de l'élément parent uniquement
                screenshot_path = str(Path("temp/screenshots") / f"voice_parent_element_{int(time.time())}.png")
                parent_element.screenshot(screenshot_path)
                logging.info(f".... Capture d'écran de l'élément parent enregistrée: {screenshot_path}")
                
                # Cliquer sur l'élément parent
                parent_element.click()
                logging.info(".... Clic sur le parent de 'FAV-delf-micro-cravatte-with-amb' réussi")

                # Attendre 1 secondes
                logging.info(".... Attente de 1 secondes après avoir cliqué sur la voix...")
                time.sleep(1)

                #--------------------------------
                # cliquer sur la croix pour fermer la fenêtre
                # Cliquer sur l'élément use avec xlink:href="#icon_close"
                # try:
                #     logging.info(".... Recherche de l'élément 'use' avec xlink:href='#icon_close'...")
                #     close_icon = wait.until(
                #         EC.element_to_be_clickable((By.CSS_SELECTOR, "use[xlink\\:href='#icon_close']"))
                #     )
                    
                #     # Prendre une capture d'écran avant de cliquer
                #     screenshot_path = str(Path("temp/screenshots") / f"close_icon_before_click_{int(time.time())}.png")
                #     close_icon.screenshot(screenshot_path)
                #     logging.info(f".... Capture d'écran de l'icône de fermeture enregistrée: {screenshot_path}")
                    
                #     # Cliquer sur l'icône de fermeture
                #     close_icon.click()
                #     logging.info(".... Clic sur l'icône de fermeture réussi")
                # except Exception as e:
                #     logging.error(f".... Erreur lors du clic sur l'icône de fermeture: {e}")

                # # Attendre 1 seconde
                # time.sleep(500)
                
            else:
                raise Exception("L'élément parent n'est pas cliquable ou n'existe pas")
            
            
            # ------------------------------------------------------------
            # Ouvrir les paramètres de voix (voice settings) en cliquant sur les 3 petits points
            # ------------------------------------------------------------
            try:
                logging.info("Recherche de l'icône 'more-level' pour les paramètres de voix...")
                more_icon = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "iconpark-icon[name='more-level']"))
                )
                
                # Obtenir le parent de l'icône
                more_button = more_icon.find_element(By.XPATH, "..")
                
                # Prendre une capture d'écran avant le clic
                screenshot_path = str(Path("temp/screenshots") / f"voice_settings_before_click_{int(time.time())}.png")
                more_button.screenshot(screenshot_path)
                logging.info(f".... Capture d'écran du bouton des paramètres enregistrée: {screenshot_path}")
                
                # Cliquer sur le parent
                more_button.click()
                logging.info(".... Clic sur le bouton des paramètres de voix réussi")
                
                # Attendre un court instant pour que le menu s'ouvre
                time.sleep(1)
                
            except Exception as e:
                logging.error(f".... Erreur lors de l'ouverture des paramètres de voix: {e}")
                self.take_screenshot(driver, "error_voice_settings")



            # Attendre 1 seconde
            time.sleep(1)

            # Appuyer 15 fois sur TAB pour aller sur stability
            logging.info(".... Appui de la touche TAB 15 fois...")
            actions = ActionChains(driver)
            for i in range(15):
                actions.send_keys(Keys.TAB)
                actions.pause(0.02)  # Petite pause entre chaque TAB
            actions.perform()
            logging.info(".... 15 TAB effectués")

            # Attendre 1 seconde
            time.sleep(1)

            # Appuyer 50 fois sur la flèche GAUCHE
            logging.info(".... Appui de la touche GAUCHE 50 fois...")
            actions = ActionChains(driver)
            for i in range(50):
                actions.send_keys(Keys.LEFT)
                actions.pause(0.02)  # Petite pause entre chaque flèche
            actions.perform()
            logging.info(".... 50 flèches GAUCHE effectuées")

            # Attendre 1 seconde
            time.sleep(1)

            # Appuyer 1 fois sur TAB pour aller sur clarity + similarity
            actions = ActionChains(driver)
            actions.send_keys(Keys.TAB)
            actions.perform()
            
            # Attendre 1 seconde
            time.sleep(1)

            # Appuyer 75 fois sur la flèche GAUCHE
            logging.info(".... Appui de la touche GAUCHE 75 fois...")
            actions = ActionChains(driver)
            for i in range(75):
                actions.send_keys(Keys.LEFT)
                actions.pause(0.02)  # Petite pause entre chaque flèche
            actions.perform()
            logging.info(".... 75 flèches GAUCHE effectuées")

            # Attendre 1 seconde
            time.sleep(1)

            # Appuyer 1 fois sur TAB pour aller sur style exaggeration
            actions = ActionChains(driver)
            actions.send_keys(Keys.TAB)
            actions.perform()
            
            # Attendre 1 seconde
            time.sleep(1)

            # Appuyer 100 fois sur la flèche DROITE
            logging.info(".... Appui de la touche DROITE 100 fois...")
            actions = ActionChains(driver)
            for i in range(100):
                actions.send_keys(Keys.RIGHT)
                actions.pause(0.02)  # Petite pause entre chaque flèche
            actions.perform()
            logging.info(".... 100 flèches DROITE effectuées")

            # Appuyer 2 fois sur TAB pour aller sur Speed
            actions = ActionChains(driver)
            actions.send_keys(Keys.TAB)
            actions.pause(0.1)  # Petite pause
            actions.send_keys(Keys.TAB)
            actions.pause(0.1)  # Petite pause
            actions.send_keys(Keys.RIGHT)
            actions.pause(0.1)  # Petite pause
            actions.send_keys(Keys.RIGHT)
            actions.perform()

            # Attendre 1 seconde
            time.sleep(1)

            # ------------------------------------------------------------
            # remplissage des blocs de texte
            # ------------------------------------------------------------

            # Trouver la zone de texte du script
            script_textarea = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div[contenteditable='true']"))
            )

            # Cliquer sur la zone de texte
            script_textarea.click()
            logging.info("_choose_voice_and_fill_text : Clic sur la zone de texte du script réussi")

            # Utiliser CTRL+A/CMD+A pour sélectionner tout le texte puis le remplacer
            actions = ActionChains(self.browser)
            if platform.system() == 'Darwin':  # Pour macOS
                actions.key_down(Keys.COMMAND).send_keys('a').key_up(Keys.COMMAND)
            else:  # Pour Windows/Linux
                actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL)
            actions.perform()
            time.sleep(0.5)

            # Diviser le texte en paragraphes basés sur les retours à la ligne
            paragraphs = text.split('\n')
                
            # Afficher le texte original et les paragraphes pour le débogage
            logging.info(f"Texte original (longueur: {len(text)}):")
            logging.info(repr(text))  # Afficher avec les caractères d'échappement visibles
            
            logging.info(f"Nombre de paragraphes après découpage: {len(paragraphs)}")
            for i, para in enumerate(paragraphs):
                logging.info(f"Paragraphe {i+1}/{len(paragraphs)} (longueur: {len(para)}):")
                logging.info(repr(para))  # Afficher avec les caractères d'échappement visibles
            
            # Filtrer les paragraphes vides
            paragraphs = [p for p in paragraphs if p.strip()]
            logging.info(f"Nombre de paragraphes après filtrage des vides: {len(paragraphs)}")
            
            # Vérifier s'il y a d'autres types de retours à la ligne
            if '\r\n' in text:
                logging.info("ATTENTION: Le texte contient des retours à la ligne Windows (\\r\\n)")
                alt_paragraphs = text.split('\r\n')
                alt_paragraphs = [p for p in alt_paragraphs if p.strip()]
                logging.info(f"Nombre de paragraphes avec split('\\r\\n') après filtrage: {len(alt_paragraphs)}")
            
            if '\r' in text:
                logging.info("ATTENTION: Le texte contient des retours chariot Mac (\\r)")
                alt_paragraphs = text.split('\r')
                alt_paragraphs = [p for p in alt_paragraphs if p.strip()]
                logging.info(f"Nombre de paragraphes avec split('\\r') après filtrage: {len(alt_paragraphs)}")
            
            # Essayer une autre approche de découpage plus robuste
            import re
            robust_paragraphs = re.split(r'\n|\r\n|\r', text)
            robust_paragraphs = [p for p in robust_paragraphs if p.strip()]
            logging.info(f"Nombre de paragraphes avec regex après filtrage: {len(robust_paragraphs)}")
            
            # Utiliser cette approche plus robuste
            paragraphs = robust_paragraphs
            
            # Saisir chaque paragraphe séparément avec des touches Entrée entre eux
            for i, paragraph in enumerate(paragraphs):
                if i > 0:  # Ne pas ajouter d'Entrée avant le premier paragraphe
                    logging.info(f"Création d'un nouveau bloc de texte avec la touche Entrée ({i}/{len(paragraphs)})")
                    time.sleep(1)  # Attente avant d'appuyer sur Entrée
                    
                    # Créer un nouveau bloc de paragraphe avec Entrée
                    actions = ActionChains(self.browser)
                    actions.send_keys(Keys.ENTER)
                    actions.perform()
                    
                    time.sleep(1)  # Attente après avoir appuyé sur Entrée
                
                # Saisir le texte du paragraphe
                if paragraph.strip():  # Ne pas saisir les paragraphes vides
                    logging.info(f"Saisie du paragraphe {i+1}: {paragraph[:30]}..." if len(paragraph) > 30 else f"Saisie du paragraphe {i+1}: {paragraph}")
                    actions = ActionChains(self.browser)
                    actions.send_keys(paragraph.strip())
                    actions.perform()
                    time.sleep(2)


            # Appuyer sur TAB pour valider
            actions = ActionChains(self.browser)
            actions.send_keys(Keys.TAB)
            actions.perform()

            
            # Exécuter le script JavaScript pour dupliquer la scène
            if not self._duplicate_scene(driver):
                logging.error("Échec de la duplication de la scène")
                time.sleep(999)  # Gardé de votre code original
                sys.exit(0)      # Gardé de votre code original
            
            # duplique la scène 2 fois de plus pour avoir 4 scènes
            self._duplicate_scene(driver)
            self._duplicate_scene(driver)

            # Cliquer sur play maintenant pour faire les bonnes longueurs de blocs
            # mais avant il faudrait sûrement faire la duplication des scènes
            # Au lieu de chercher l'élément iconpark-icon, chercher directement le bouton spécifique
            try:
                logging.info("Recherche du bouton avec la classe 'css-1d5pxp4'...")
                
                # Trouver le bouton par sa classe CSS
                button = driver.find_element(By.CSS_SELECTOR, "button.css-1d5pxp4")
                logging.info("Bouton avec classe 'css-1d5pxp4' trouvé")
                
                # Prendre un screenshot du bouton avant de cliquer
                screenshot_path = str(Path("temp/screenshots") / f"button_css_1d5pxp4_before_click_{int(time.time())}.png")
                button.screenshot(screenshot_path)
                logging.info(f"Screenshot du bouton enregistré: {screenshot_path}")
                
                # Afficher des informations sur le bouton
                tag_name = button.tag_name
                classes = button.get_attribute("class")
                text = button.text
                is_displayed = button.is_displayed()
                is_enabled = button.is_enabled()
                location = button.location
                size = button.size
                logging.info(f"Informations sur le bouton: tag={tag_name}, classes={classes}, texte='{text}', visible={is_displayed}, activé={is_enabled}, position={location}, taille={size}")
                
                # Cliquer sur le bouton
                logging.info("Clic sur le bouton...")
                button.click()
                logging.info("Clic sur le bouton réussi")
                
                # Attendre un court instant pour voir l'effet du clic
                time.sleep(1)
                
                # Prendre un screenshot après le clic
                self.take_screenshot(driver, "after_click_specific_button")
                
            except Exception as e:
                logging.error(f"Erreur lors de la recherche ou du clic sur le bouton 'css-1d5pxp4': {e}")
                logging.error(traceback.format_exc())
                self.take_screenshot(driver, "error_finding_specific_button")
            

            # Attendre 40 secondes après le clic sur le bouton play car il faut du temps pour générer
            logging.info("Attente de 40 secondes après le bouton play...")
            time.sleep(40)

            

            return True
        
        except Exception as e:
            logging.error(f"Erreur lors du choix de la voix et de la saisie du texte: {str(e)}")
            logging.error(traceback.format_exc())
            self.take_screenshot(driver, "error_choose_voice_and_fill_text")
            return False 
    
    def _duplicate_scene(self, driver):
        """
        Duplique la scène actuelle en utilisant JavaScript.
        
        Args:
            driver: Le navigateur WebDriver
            
        Returns:
            bool: True si la duplication a réussi, False sinon
        """
        try:
            logging.info("Exécution du script JavaScript pour dupliquer la scène...")
            
            js_result1 = driver.execute_script("""
                try {
                    // Chercher le SVG
                    const svg = document.querySelector('svg[data-name="icon_more_level"]');
                    if (!svg) {
                        return "Erreur: SVG 'icon_more_level' non trouvé";
                    }
                    
                    // Trouver et cliquer sur son parent
                    const parent = svg.parentElement;
                    console.log("Parent du SVG trouvé:", parent);
                    parent.click();
                    console.log("Clic sur le parent du SVG effectué");
                    return "Clic sur le parent du SVG réussi";
                } catch (error) {
                    return "Erreur d'exécution du premier script: " + error.message;
                }
            """)
            
            logging.info(f"Résultat du premier script JavaScript: {js_result1}")
            
            # Prendre un screenshot après le premier clic
            self.take_screenshot(driver, "after_svg_parent_click")
            
            # Attendre 1 secondes entre les deux clics
            logging.info("Attente de 1 secondes avant le deuxième script...")
            time.sleep(1)
            
            # Deuxième script: cliquer sur "Duplicate Scene"
            logging.info("Exécution du deuxième script JavaScript: clic sur 'Duplicate Scene'...")
            
            js_result2 = driver.execute_script("""
                try {
                    // Chercher le div contenant "Duplicate Scene"
                    const closestElement = [...document.querySelectorAll('div')].find(el => el.textContent.trim() === 'Duplicate Scene');
                    if (!closestElement) {
                        return "Erreur: Élément 'Duplicate Scene' non trouvé";
                    }
                    
                    console.log("Élément 'Duplicate Scene' trouvé:", closestElement);
                    closestElement.click();
                    console.log("Clic sur 'Duplicate Scene' effectué");
                    return "Clic sur 'Duplicate Scene' réussi";
                } catch (error) {
                    return "Erreur d'exécution du deuxième script: " + error.message;
                }
            """)
            
            logging.info(f"Résultat du deuxième script JavaScript: {js_result2}")
            
            # Prendre un screenshot après la duplication de la scène
            time.sleep(1)  # Attendre un peu pour que l'interface réagisse
            self.take_screenshot(driver, "after_duplicate_scene")
            
            # Attendre encore un peu pour s'assurer que la duplication est terminée
            logging.info("Attente de 5 secondes supplémentaires après la duplication...")
            time.sleep(5)
            
            return True
            
        except Exception as e:
            logging.error(f"Erreur lors de l'exécution du script de duplication: {e}")
            logging.error(traceback.format_exc())
            self.take_screenshot(driver, "error_duplicate_scene")
            return False
        