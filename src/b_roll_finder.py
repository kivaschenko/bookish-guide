#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de recherche intelligente des b-rolls pour illustrer les vidéos rush.
Utilise l'API OpenAI pour analyser le contenu des rushes et sélectionner les b-rolls les plus pertinentes.
"""

import os
import sys
import logging
import json
import math
import re
from pathlib import Path
import openai
import traceback
import requests
from src.vector_matcher import VectorMatcher
from jouer_son import fin_vector_broll

class BRollFinder:
    """
    Classe responsable de la sélection intelligente des b-rolls pour chaque rush.
    Analyse le contenu textuel du rush et les métadonnées des b-rolls pour faire la meilleure sélection.
    """
    
    def __init__(self, config):
        """
        Initialise le sélecteur de b-rolls avec la configuration.
        
        Args:
            config (dict): Configuration chargée depuis config.yml
        """
        self.config = config
        self.temp_path = Path(config['paths']['temp'])
        self.b_roll_path = Path(config['paths']['b_roll'])
    

        # Editing parameters for b-rolls
        self.b_roll_seconds = config.get('editing', {}).get('b_roll_seconds', 4)
        self.b_roll_spacing = config.get('editing', {}).get('b_roll_spacing', 4)
        self.b_roll_start_delay = config.get('editing', {}).get('b_roll_start_delay', 4)
        
        # Temporary JSON file path
        self.broll_json_path = self.temp_path / 'broll_selections.json'
        
        # List of available b-rolls (MP4 and MOV)
        self.b_roll_files = list(self.b_roll_path.glob('*.mp4'))
        self.b_roll_files.extend(list(self.b_roll_path.glob('*.mov')))
        
        # Set of already used b-rolls
        self.used_b_rolls = set()
        
        # Get OpenAI API key from configuration
        self.api_key = None
        if 'api' in config and 'openai' in config['api'] and 'api_key' in config['api']['openai']:
            self.api_key = config['api']['openai']['api_key']
            logging.info("OpenAI API key found in configuration")
        else:
            raise ValueError("Clé API OpenAI non trouvée dans la configuration")
        
        # Initialiser le client OpenAI
        self.openai_client = openai.OpenAI(api_key=self.api_key)
        self.openai_model = config['api']['openai']['model']
        
        logging.info(f"BRollFinder initialized with {len(self.b_roll_files)} available b-rolls")
    
    def calculate_needed_b_rolls(self, rush_duration):
        """
        Calcule le nombre de b-rolls nécessaires pour un rush donné.
        
        Args:
            rush_duration (float): Durée du rush en secondes
            
        Returns:
            int: Nombre de b-rolls nécessaires
        """
        # Calculate available space for b-rolls (accounting for initial delay)
        available_space = rush_duration - self.b_roll_start_delay
        
        # If not enough space, no b-roll is needed
        if available_space <= 0:
            logging.info(f"Rush trop court ({rush_duration}s) pour ajouter des b-rolls")
            return 0
        
        # Calculate number of b-rolls that can fit in available space
        # Each b-roll occupies: b_roll_seconds + b_roll_spacing (except the last one)
        num_b_rolls = math.floor(available_space / (self.b_roll_seconds + self.b_roll_spacing))
        
        # If we can add at least one b-roll
        if num_b_rolls >= 1:
            # We can add an additional b-roll because the last one doesn't need spacing
            # after it (it ends with the rush)
            space_without_last_spacing = available_space + self.b_roll_spacing
            num_b_rolls = math.floor(space_without_last_spacing / (self.b_roll_seconds + self.b_roll_spacing))
        
        # Ensure at least one b-roll if space is sufficient
        if available_space >= self.b_roll_seconds and num_b_rolls == 0:
            num_b_rolls = 1
        
        logging.info(f"Rush duration: {rush_duration}s, b-rolls needed: {num_b_rolls}")
        return num_b_rolls
    
    def get_rush_paragraph(self, rush_index):
        """
        Récupère le paragraphe correspondant au rush dans le fichier i3.txt.
        
        Args:
            rush_index (int): Indice du rush (0-indexé)
            
        Returns:
            str: Paragraphe correspondant au rush
        """
        i3_path = self.temp_path / 'i3.txt'
        if not i3_path.exists():
            error_msg = f"Le fichier {i3_path} est manquant. Veuillez d'abord exécuter l'étape de paraphrase avec -s"
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            with open(i3_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split content into paragraphs
            paragraphs = content.split('\n\n')
            
            # Check that there are enough paragraphs
            if rush_index >= len(paragraphs):
                error_msg = f"Le fichier i3.txt ne contient que {len(paragraphs)} paragraphes, mais le rush {rush_index+1} est demandé"
                logging.error(error_msg)
                raise ValueError(error_msg)
            
            paragraph = paragraphs[rush_index]
            logging.info(f"Paragraphe du rush {rush_index+1} extrait: {paragraph[:100]}...")
            return paragraph
        
        except Exception as e:
            error_msg = f"Erreur lors de la lecture du paragraphe pour le rush {rush_index+1}: {e}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            raise
    
    def get_broll_metadata(self, broll_file):
        """
        Récupère les métadonnées d'une b-roll depuis son fichier .txt.
        Le fichier contient maintenant uniquement du texte brut (la description contextuelle).
        
        Args:
            broll_file (Path): Chemin vers le fichier b-roll
            
        Returns:
            dict: Métadonnées de la b-roll dans un format compatible
        """
        meta_file = broll_file.with_suffix('.txt')
        if not meta_file.exists():
            error_msg = f"Le fichier de métadonnées {meta_file} est manquant. Veuillez exécuter --meta"
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                context = f.read().strip()
            
            # Return formatted dictionary to remain compatible with rest of code
            return {
                "error": None,
                "description": ["Description extraite du fichier texte"],
                "context": context
            }
        except Exception as e:
            error_msg = f"Erreur lors de la lecture des métadonnées de {broll_file.name}: {e}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            return {
                "error": str(e),
                "description": [],
                "context": "Erreur de lecture du fichier"
            }
    
    def rank_brolls_for_rush(self, rush_index, rush_text):
        """
        Classe les b-rolls disponibles par pertinence pour un rush donné.
        
        Args:
            rush_index (int): Indice du rush (0-indexé)
            rush_text (str): Texte du paragraphe du rush
            
        Returns:
            list: Liste des chemins vers les b-rolls classées par pertinence
        """
        # Check that there are still available b-rolls
        available_brolls = [f for f in self.b_roll_files if f not in self.used_b_rolls]
        if not available_brolls:
            logging.warning(f"Aucune b-roll disponible pour le rush {rush_index+1}")
            return []
        
        # Collect metadata from available b-rolls
        broll_data = []
        for broll in available_brolls:
            try:
                metadata = self.get_broll_metadata(broll)
                # Keep only b-rolls with valid metadata
                if metadata.get("error") is None:
                    description = ", ".join(metadata.get("description", ["Pas de description"]))
                    context = metadata.get("context", "Pas de contexte")
                    broll_data.append({
                        "path": str(broll),
                        "name": broll.name,
                        "description": description,
                        "context": context
                    })
            except Exception as e:
                logging.error(f"Error retrieving metadata for {broll.name}: {e}")
        
        if not broll_data:
            error_msg = f"ERREUR B_ROLL: Aucune b-roll avec des métadonnées valides disponible pour le rush {rush_index+1}"
            logging.error(error_msg)
            raise ValueError(error_msg)
        
        # Construire le prompt pour OpenAI
        prompt = f"""
Liste des b-rolls disponibles (format: nom_fichier[TAB]description):
{broll_list_text}

Phrases à illustrer:
{json.dumps(sentences_with_ids, indent=2, ensure_ascii=False)}

Pour chaque phrase, sélectionnez la b-roll la plus pertinente en respectant ces règles :
1. Ne jamais utiliser la même b-roll deux fois
2. Si une b-roll parfaite a déjà été utilisée, choisir la deuxième plus pertinente
3. Privilégier la variété des b-rolls pour maintenir l'intérêt visuel

Répondez uniquement avec un JSON contenant l'id de la phrase, le texte de la phrase, et le nom du fichier b-roll choisi.

Exemple:
{{
  "1": "nom_broll1.mp4",
  "2": "nom_broll2.mp4",
  ...
}}"""
        
        # Call to OpenAI API
        logging.info(f"Calling OpenAI API for b-roll ranking of rush {rush_index+1}")
        try:
            # Utiliser GPT-5 avec la nouvelle API
            if self.openai_model == 'gpt-5':
                input_text = f"SYSTEM: Tu es un assistant spécialisé dans la sélection de vidéos b-roll pertinentes pour illustrer un contenu vidéo.\n\nUSER: {prompt}"
                response = self.openai_client.responses.create(
                    model="gpt-5",
                    input=input_text,
                    reasoning={"effort": "low"},
                    text={"verbosity": "low"}
                )
                # Parse JSON from GPT-5 response
                import json
                parsed_content = json.loads(response.output_text)
                # Adapt response to expected format
                response.choices = [type('obj', (object,), {
                    'message': type('obj', (object,), {
                        'content': parsed_content
                    })()
                })()]
            else:
                response = self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": "Tu es un assistant spécialisé dans la sélection de vidéos b-roll pertinentes pour illustrer un contenu vidéo."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500
                )
            
            ranking_text = response.choices[0].message.content.strip()
            logging.info(f"OpenAI response for rush {rush_index+1}: {ranking_text[:100]}...")
            
            # Extraire les noms de fichiers du texte de classement
            ranked_files = []
            for line in ranking_text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                    
                # Essayer de trouver le nom du fichier dans la ligne
                for broll in broll_data:
                    if broll['name'] in line:
                        broll_path = Path(broll['path'])
                        ranked_files.append(broll_path)
                        break
            
            # Check that ranking contains at least one b-roll
            if not ranked_files:
                error_msg = f"ERREUR B_ROLL: OpenAI n'a pas retourné de b-rolls valides pour le rush {rush_index+1}"
                logging.error(error_msg)
                raise ValueError(error_msg)
            
            return ranked_files
            
        except Exception as e:
            error_msg = f"ERREUR B_ROLL: Erreur lors de l'appel à l'API OpenAI pour le rush {rush_index+1}: {e}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            raise
    
    def get_brolls_for_rush(self, rush_index, rush_duration):
        """
        Sélectionne les b-rolls les plus appropriées pour un rush donné.
        
        Args:
            rush_index (int): Indice du rush (0-indexé)
            rush_duration (float): Durée du rush en secondes
            
        Returns:
            list: Liste des chemins vers les b-rolls sélectionnées pour ce rush
        """
        # Determine number of b-rolls needed
        num_brolls_needed = self.calculate_needed_b_rolls(rush_duration)
        
        if num_brolls_needed == 0:
            logging.info(f"Aucune b-roll requise pour le rush {rush_index+1}")
            return []
        
        # Get paragraph text corresponding to rush
        rush_text = self.get_rush_paragraph(rush_index)
        
        # Get b-roll ranking for this rush
        ranked_brolls = self.rank_brolls_for_rush(rush_index, rush_text)
        
        # Select required number of b-rolls
        selected_brolls = ranked_brolls[:num_brolls_needed]
        
        # Mark b-rolls as used
        for broll in selected_brolls:
            self.used_b_rolls.add(broll)
        
        logging.info(f"Selected {len(selected_brolls)}/{num_brolls_needed} b-rolls for rush {rush_index+1}")
        for i, broll in enumerate(selected_brolls):
            logging.info(f"  B-roll {i+1}: {broll.name}")
        
        return selected_brolls
    
    def calculate_broll_positions(self, rush_index, rush_duration, selected_brolls):
        """
        Calcule les positions des b-rolls pour qu'elles soient réparties dans le rush,
        avec la dernière se terminant exactement à la fin du rush.
        
        Args:
            rush_index (int): Indice du rush (0-indexé)
            rush_duration (float): Durée du rush en secondes
            selected_brolls (list): Liste des chemins vers les b-rolls sélectionnées
            
        Returns:
            list: Liste de tuples (b-roll, position_début, durée) pour chaque b-roll
        """
        if not selected_brolls:
            return []
        
        # Initialize position list
        broll_positions = []
        
        # Number of b-rolls to position
        n = len(selected_brolls)
        
        # If only one b-roll, place it at the end
        if n == 1:
            start_pos = rush_duration - self.b_roll_seconds
            if start_pos < self.b_roll_start_delay:
                start_pos = self.b_roll_start_delay
            broll_positions.append((selected_brolls[0], start_pos, min(self.b_roll_seconds, rush_duration - start_pos)))
            return broll_positions
        
        # Espace disponible pour les b-rolls (en tenant compte du délai initial)
        available_space = rush_duration - self.b_roll_start_delay
        
        # Positionner la dernière b-roll pour qu'elle se termine exactement avec le rush
        last_start_pos = rush_duration - self.b_roll_seconds
        
        # Espace restant pour les autres b-rolls
        remaining_space = last_start_pos - self.b_roll_start_delay
        
        # Répartir les autres b-rolls uniformément dans l'espace restant
        if n > 1:
            # Calculer l'intervalle entre chaque b-roll
            interval = remaining_space / (n - 1)
            
            # Positionner chaque b-roll
            for i in range(n - 1):
                start_pos = self.b_roll_start_delay + i * interval
                broll_positions.append((selected_brolls[i], start_pos, self.b_roll_seconds))
        
        # Ajouter la dernière b-roll
        broll_positions.append((selected_brolls[-1], last_start_pos, self.b_roll_seconds))
        
        return broll_positions
    
    def prepare_brolls_for_all_rushes(self, rush_durations):
        """Prépare les sélections de b-rolls pour tous les rushes"""
        try:
            # Générer le fichier de timing
            timing_file = self.generate_broll_timing(rush_durations)
            if not timing_file:
                return None
            
            logging.info("B-roll preparation completed")
            return timing_file
            
        except Exception as e:
            logging.error(f"Error during b-roll preparation: {e}")
            logging.error(traceback.format_exc())
            return None
    
    def split_paragraph_into_sentences(self, paragraph):
        """
        Découpe un paragraphe en phrases individuelles.
        
        Args:
            paragraph (str): Le paragraphe à découper
            
        Returns:
            list: Liste des phrases
        """
        # Regex pour découper aux points, points d'exclamation et d'interrogation
        # tout en préservant ces caractères
        sentence_delimiters = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_delimiters, paragraph)
        
        # Filtrer les phrases vides
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def select_brolls_for_sentences(self, paragraph_text, rush_duration, paragraph_index):
        """
        Sélectionne les b-rolls les plus pertinentes pour chaque phrase d'un paragraphe.
        
        Args:
            paragraph_text (str): Texte du paragraphe
            rush_duration (float): Durée du rush en secondes
            paragraph_index (int): Index du paragraphe
            
        Returns:
            list: Liste de dictionnaires contenant les b-rolls sélectionnées avec leurs positions
        """
        logging.info("Starting b-roll selection for sentences")
        
        # Diviser le paragraphe en phrases
        sentences = self.split_paragraph_into_sentences(paragraph_text)
        logging.info(f"Paragraph split into {len(sentences)} sentences")
        
        # Obtenir la liste des b-rolls disponibles
        available_brolls = [f for f in self.b_roll_files if f not in self.used_b_rolls]
        logging.info(f"{len(available_brolls)} b-rolls disponibles")
        
        # Calculer combien de b-rolls on peut placer dans ce rush
        available_space = rush_duration - self.b_roll_start_delay
        max_brolls = int(available_space / (self.b_roll_seconds + self.b_roll_spacing))
        logging.info(f"Espace disponible pour {max_brolls} b-rolls maximum")
        
        # Limiter le nombre de b-rolls au nombre de phrases ou au maximum calculé
        num_brolls = min(len(sentences), max_brolls)
        logging.info(f"Selecting {num_brolls}/{len(sentences)} b-rolls")
        
        selected_brolls = []
        
        for i in range(num_brolls):
            if i >= len(sentences):
                logging.info(f"No more sentences available after {i} selections")
                break
            
            if not available_brolls:
                logging.info(f"No more b-rolls available after {i} selections")
                break
            
            display_sentence = sentences[i][:100] + "..." if len(sentences[i]) > 100 else sentences[i]
            logging.info(f"Analyse de la phrase {i+1}/{len(sentences)}: \"{display_sentence}\"")
            
            # IMPORTANT: Passer le paragraphe complet comme contexte
            best_broll = self.find_best_brolls_for_rush(rush_text)
            
            if best_broll:
                logging.info(f"  B-roll {i+1}: {best_broll}")
                
                # Calculer la position de début de cette b-roll
                start_position = self.b_roll_start_delay + i * (self.b_roll_seconds + self.b_roll_spacing)
                
                # Ajouter à la liste des sélections
                broll_data = {
                    "broll_path": best_broll,  # Sera converti en str plus tard
                    "start_position": start_position,
                    "duration": self.b_roll_seconds
                }
                
                selected_brolls.append(broll_data)
                
                # Marquer cette b-roll comme utilisée et la retirer des disponibles
                self.used_b_rolls.add(best_broll)
                available_brolls = [f for f in available_brolls if f != best_broll]
            else:
                logging.warning(f"No b-roll selected for sentence {i+1}")
        
        logging.info(f"Selected {len(selected_brolls)}/{len(sentences)} b-rolls for rush {paragraph_index+1}")
        return selected_brolls
    
    def find_best_brolls_for_rush(self, rush_text):
        """
        Trouve les meilleurs b-rolls pour un rush complet en une seule fois.
        
        Args:
            rush_text (str): Texte complet du rush
        
        Returns:
            dict: Dictionnaire avec les b-rolls sélectionnées pour chaque phrase
        """
        try:
            # Découper le texte en phrases
            sentences = self.split_paragraph_into_sentences(rush_text)
            
            # Créer le dictionnaire des phrases avec IDs
            sentences_with_ids = {
                str(i+1): sentence.strip()
                for i, sentence in enumerate(sentences)
            }
            
            # Construire la liste des b-rolls disponibles
            broll_options = []
            for broll_file in Path("b-roll").glob("*.mp4"):
                txt_file = broll_file.with_suffix(".txt")
                if txt_file.exists():
                    with open(txt_file, "r") as f:
                        context = f.read().strip()
                    broll_options.append(f"{broll_file.name}\t{context}")
            
            broll_list_text = "\n".join(broll_options)
            
            # Construire le prompt avec le nouveau format
            prompt = f"""
Liste des b-rolls disponibles (format: nom_fichier[TAB]description):
{broll_list_text}

Phrases à illustrer:
{json.dumps(sentences_with_ids, indent=2, ensure_ascii=False)}

Chaque phrase suit la précédente dans un texte global, l'histoire est cohérente. Pour chaque phrase du texte, choisis la b-roll la plus pertinente en respectant ces règles :
- Chaque b-roll ne peut être utilisée qu'une seule fois.
- Pour chaque phrase, retourne un objet JSON avec les clés suivantes :
- "id" : identifiant de la phrase,
- "filename" : nom de la b-roll choisie,
- "phrase" : le texte complet de la phrase,
- "score" : une note sur 10 représentant la pertinence visuelle et sociale du match.

IMPORTANT: 
Réfléchi au contexte social.
Ne met pas un homme pour une femme. Ne met pas une personne agée pour une jeune. Ne met pas Paris pour les USA...
Tu dois retourner un objet JSON avec une clé "selections" contenant un tableau d'objets comme ceci:
{{
  "selections": [
    {{
      "id": 1,
      "filename": "example-video-clip-01.mp4",
      "phrase": "Elle a commencé avec presque rien.",
      "score": 9
    }},
{{
      "id": 2,
      "filename": "example-video-clip-02.mp4", 
      "phrase": "Elle vendait des vêtements dans une petite boutique.",
      "score": 8
    }}
  ]
}}"""

            logging.info(f"Prompt sent to GPT for complete rush with new format")
            
            # Utiliser GPT-5 avec la nouvelle API
            if self.config['api']['openai']['model'] == 'gpt-5':
                input_text = f"USER: {prompt}"
                response = requests.post(
                    "https://api.openai.com/v1/responses",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.config['api']['openai']['api_key']}"
                    },
                    json={
                        "model": "gpt-5",
                        "input": input_text,
                        "reasoning": {"effort": "low"},
                        "text": {"verbosity": "low", "format": {"type": "json_object"}}
                    }
                )
            else:
                # Utiliser l'ancienne API pour les autres modèles
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.config['api']['openai']['api_key']}"
                    },
                    json={
                        "model": self.config['api']['openai']['model'],
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"}  # Force la réponse en JSON
                    }
                )
            
            # Parser la réponse
            response_json = response.json()
            if self.config['api']['openai']['model'] == 'gpt-5':
                # GPT-5 retourne du JSON dans output_text, il faut le parser
                import json
                parsed_content = json.loads(response_json['output_text'].strip())
            else:
                content = response_json['choices'][0]['message']['content'].strip()
                # Parser le JSON pour l'ancienne API
                parsed_content = json.loads(content)
            logging.info(f"Raw GPT response: {parsed_content}")
            
            # Extraire les sélections
            if "selections" in parsed_content and isinstance(parsed_content["selections"], list):
                selections = parsed_content["selections"]
                logging.info(f"GPT response processed with {len(selections)} selections")
                
                # Convertir en format attendu
                broll_selections = {}
                for item in selections:
                    phrase_id = str(item.get("id", ""))
                    filename = item.get("filename", "")
                    score = item.get("score", 0)
                    
                    if phrase_id and filename:
                        logging.info(f"Sentence {phrase_id}: b-roll '{filename}' selected with score {score}/10")
                        broll_selections[phrase_id] = filename
                
                # Si des sélections ont été faites, les retourner
                if broll_selections:
                    return broll_selections
            
            # Si on arrive ici, c'est qu'on n'a pas pu extraire les sélections
            logging.warning("Incorrect response format, using default b-rolls")
            b_rolls = list(Path("b-roll").glob("*.mp4"))
            default_selections = {}
            for i, sentence in enumerate(sentences):
                if i < len(b_rolls):
                    default_selections[str(i+1)] = b_rolls[i].name
            return default_selections
            
        except Exception as e:
            logging.error(f"Error during b-roll selection: {e}")
            logging.error(traceback.format_exc())
            
            # En cas d'erreur, retourner une sélection par défaut
            logging.warning("Using default b-rolls due to error")
            b_rolls = list(Path("b-roll").glob("*.mp4"))
            default_selections = {}
            for i, sentence in enumerate(sentences):
                if i < len(b_rolls):
                    default_selections[str(i+1)] = b_rolls[i].name
            return default_selections
    
    def get_brolls_with_positions_from_json(self):
        """
        Récupère les sélections de b-rolls depuis le fichier JSON préalablement généré.
        
        Returns:
            dict: Dictionnaire des sélections de b-rolls par rush
        """
        if not self.broll_json_path.exists():
            error_msg = f"Le fichier de sélections {self.broll_json_path} n'existe pas. Veuillez d'abord exécuter --preparebroll"
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            with open(self.broll_json_path, 'r', encoding='utf-8') as f:
                broll_selections = json.load(f)
            
            logging.info(f"B-roll selections loaded from {self.broll_json_path}")
            
            # Convertir les chemins de chaînes en objets Path
            for rush_id, selections in broll_selections.items():
                for selection in selections:
                    selection['broll_path'] = Path(selection['broll_path'])
            
            return broll_selections
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement des sélections de b-rolls: {e}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            raise
    
    def get_brolls_with_positions(self, rush_durations, use_saved=False):
        """
        Sélectionne les b-rolls pour tous les rushes et calcule leurs positions.
        
        Args:
            rush_durations (list): Liste des durées des rushes en secondes
            use_saved (bool): Si True, utilise les sélections sauvegardées plutôt que de faire de nouveaux appels API
            
        Returns:
            list: Liste de listes de tuples (b-roll, position_début, durée) pour chaque rush
        """
        if use_saved:
            # Charger les sélections depuis le fichier JSON
            broll_selections = self.get_brolls_with_positions_from_json()
            
            # Convertir en format attendu par video_editor.py
            all_broll_positions = []
            
            # Vérifier que nous avons des sélections pour tous les rushes
            for i in range(len(rush_durations)):
                rush_id = f"rush{i+1}"
                
                if rush_id not in broll_selections:
                    error_msg = f"Aucune sélection trouvée pour {rush_id} dans le fichier JSON"
                    logging.error(error_msg)
                    raise ValueError(error_msg)
                
                # Récupérer les positions pour ce rush
                rush_positions = []
                for selection in broll_selections[rush_id]:
                    rush_positions.append((
                        selection['broll_path'],
                        selection['start_position'],
                        selection['duration']
                    ))
                
                all_broll_positions.append(rush_positions)
            
            return all_broll_positions
            
        else:
            # Faire de nouveaux appels API pour sélectionner les b-rolls
            all_broll_positions = []
            
            # Pour chaque rush
            for i, duration in enumerate(rush_durations):
                try:
                    # Sélectionner les b-rolls pour ce rush
                    selected_brolls = self.get_brolls_for_rush(i, duration)
                    
                    # Calculer les positions des b-rolls dans ce rush
                    broll_positions = self.calculate_broll_positions(i, duration, selected_brolls)
                    
                    # Ajouter les positions à la liste globale
                    all_broll_positions.append(broll_positions)
                    
                except Exception as e:
                    error_msg = f"ERREUR B_ROLL: Erreur lors de la sélection des b-rolls pour le rush {i+1}: {e}"
                    logging.error(error_msg)
                    logging.error(traceback.format_exc())
                    raise
            
            return all_broll_positions
    
    def calculate_word_positions(self, text, total_duration):
        """
        Calcule la position temporelle de chaque début de phrase basée sur le nombre de mots
        
        Args:
            text (str): Texte complet du rush
            total_duration (float): Durée totale du rush en secondes
            
        Returns:
            dict: Dictionnaire avec l'index de la phrase et sa position temporelle de début
        """
        # Découper en phrases
        sentences = self.split_paragraph_into_sentences(text)
        
        # Compter le nombre total de mots
        total_words = len(text.split())
        
        # Calculer la durée moyenne par mot
        seconds_per_word = total_duration / total_words
        
        # Calculer la position de chaque phrase
        positions = {}
        word_count = 0
        
        for i, sentence in enumerate(sentences, 1):
            # La position de la phrase est déterminée par le nombre de mots qui la précèdent
            start_time = word_count * seconds_per_word
            positions[str(i)] = {
                "sentence": sentence.strip(),
                "start_time": round(start_time, 3),
                "word_count": len(sentence.split())
            }
            word_count += len(sentence.split())
        
        return positions

    def generate_broll_timing(self, rush_durations, selection_mode='gpt', audio_mode='heygen'):
        """
        Génère le fichier broll_timing.json avec les timings précis de chaque b-roll
        basés sur le moment où chaque phrase est prononcée
        selection_mode: 'gpt' (par défaut) ou 'vector'
        """
        try:
            timing_data = []
            current_position = 0
            BROLL_DURATION = 3.5  # Durée fixe de 3.5 secondes pour chaque b-roll (ajout de 0.5s)
            
            # Utiliser la durée d'intro de la configuration pour synchroniser avec le montage
            intro_length = self.config.get('editing', {}).get('intro_length', 3.11)
            TIMING_OFFSET = intro_length  # Décalage pour que les b-rolls apparaissent après l'intro
            logging.info(f"🎬 B-roll timing synchronized with intro: {TIMING_OFFSET}s")

            # Initialiser le VectorMatcher si besoin
            if selection_mode == 'vector':
                vector_matcher = VectorMatcher(config=self.config)
                used_brolls_global = set()
            
            # Pour chaque bullet/rush
            for i, duration in enumerate(rush_durations, 1):
                # En mode TTS bullet, utiliser les fichiers bullet
                if audio_mode in ['openai_tts', 'gemini_tts']:
                    rush_name = f"bullet{i:02d}.mp3"
                    # Essayer d'abord le format avec zéro, puis sans zéro
                    text_file = self.temp_path / f"bullet{i:02d}_text.txt"
                    if not text_file.exists():
                        text_file = self.temp_path / f"bullet{i}_text.txt"
                    
                    # Read actual MP3 duration for maximum precision
                    audio_file_path = self.temp_path / "audio" / rush_name
                    if audio_file_path.exists():
                        try:
                            # Use file size-based approximation
                            file_size = audio_file_path.stat().st_size
                            # Estimation: ~1KB per second for MP3 128kbps
                            real_duration = file_size / 1000.0
                            logging.info(f"🎵 Real duration of {rush_name}: {real_duration:.3f}s (estimated: {duration:.3f}s)")
                            duration = real_duration
                        except Exception as e:
                            logging.warning(f"⚠️ Unable to read real duration of {rush_name}: {e}")
                            logging.info(f"🎵 Using estimated duration: {duration:.3f}s")
                else:
                    rush_name = f"rush{i}.mp4"
                    text_file = self.temp_path / f"rush{i}_text.txt"
                
                if not text_file.exists():
                    logging.error(f"Fichier texte manquant pour {rush_name}")
                    continue
                    
                with open(text_file, "r") as f:
                    rush_text = f.read().strip()
                
                # Calculer les positions des phrases basées sur le nombre de mots
                sentence_positions = self.calculate_word_positions(rush_text, duration)
                
                # Obtenir les b-rolls pour ce rush
                if selection_mode == 'vector':
                    broll_selections = vector_matcher.select_brolls_for_rush(rush_text, used_brolls_global)
                    # Mettre à jour l'ensemble global pour éviter les doublons sur tous les rushes
                    for selection in broll_selections.values():
                        if isinstance(selection, dict):
                            used_brolls_global.add(selection["broll"])
                            if selection.get("broll2"):
                                used_brolls_global.add(selection["broll2"])
                            if selection.get("broll3"):
                                used_brolls_global.add(selection["broll3"])
                        else:
                            used_brolls_global.add(selection)
                else:
                    broll_selections = self.find_best_brolls_for_rush(rush_text)
                
                # Pour chaque b-roll sélectionnée
                for phrase_id, broll_selection in broll_selections.items():
                    # Gérer le nouveau format (dict avec broll, broll2 et broll3) ou l'ancien format (string)
                    if isinstance(broll_selection, dict):
                        broll_filename = broll_selection["broll"]
                        broll2_filename = broll_selection.get("broll2")
                        broll3_filename = broll_selection.get("broll3")
                    else:
                        broll_filename = broll_selection
                        broll2_filename = None
                        broll3_filename = None
                    if phrase_id in sentence_positions:
                        sentence_info = sentence_positions[phrase_id]
                        
                        # Position de base au début de la phrase
                        base_time = current_position + sentence_info["start_time"]
                        
                        # Ajouter le décalage de timing
                        start_time = round(base_time + TIMING_OFFSET, 3)
                        
                        # En mode TTS, on calculera l'extension après avoir collecté toutes les B-rolls
                        # Pour l'instant, durée fixe classique
                        end_time = round(start_time + BROLL_DURATION, 3)
                        
                        # Créer l'entrée de timing avec broll2 si disponible
                        timing_entry = {
                            "rush": rush_name,
                            "broll": broll_filename,
                            "start_time": start_time,
                            "end_time": end_time,
                            "phrase": sentence_info["sentence"],
                            "phrase_id": phrase_id,
                            "word_count": sentence_info["word_count"]
                        }
                        
                        # Ajouter broll2 et broll3 si disponibles
                        if broll2_filename:
                            timing_entry["broll2"] = broll2_filename
                        if broll3_filename:
                            timing_entry["broll3"] = broll3_filename
                        
                        timing_data.append(timing_entry)
                
                current_position += duration
            
            # Post-processing spécifique au mode TTS : étendre les B-rolls jusqu'aux suivantes
            if audio_mode in ['openai_tts', 'gemini_tts'] and timing_data:
                # Trier toutes les B-rolls par heure de début
                timing_data.sort(key=lambda x: x['start_time'])
                
                # Étendre chaque B-roll jusqu'au début de la suivante
                for i in range(len(timing_data) - 1):
                    current_broll = timing_data[i]
                    next_broll = timing_data[i + 1]
                    
                    # Étendre cette B-roll jusqu'au début de la suivante
                    old_end = current_broll['end_time']
                    new_end = next_broll['start_time']
                    
                    if new_end > old_end:
                        extension = new_end - old_end
                        current_broll['end_time'] = round(new_end, 3)
                        logging.info(f"🎵 TTS extension: {current_broll['broll']} → {old_end:.3f}s to {new_end:.3f}s (+{extension:.3f}s)")
                
                # Étendre la dernière B-roll jusqu'à la fin de son bullet
                if timing_data:
                    last_broll = timing_data[-1]
                    # Calculer la fin du dernier bullet
                    bullet_end = current_position  # current_position est maintenant la durée totale
                    
                    if bullet_end > last_broll['end_time']:
                        extension = bullet_end - last_broll['end_time']
                        last_broll['end_time'] = round(bullet_end, 3)
                        logging.info(f"🎵 Extension TTS finale: {last_broll['broll']} → +{extension:.3f}s (fin du contenu)")
                
                logging.info(f"✅ TTS mode: {len(timing_data)} B-rolls extended to eliminate all gaps")
            
            # Sauvegarder les timings
            output_file = Path(self.config['paths']['temp']) / "broll_timing.json"
            with open(output_file, "w") as f:
                json.dump(timing_data, f, indent=2, ensure_ascii=False)
            
            logging.info(f"B-roll timings saved in {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating timings: {e}")
            logging.error(traceback.format_exc())
            return None

# Nouvelle fonction pour --vectorbroll

def prepare_brolls_vector(config=None):
    """
    Fonction pour préparer les sélections de b-rolls pour tous les rushes en mode vectoriel.
    Compatible avec les modes Heygen (rush*.mp4) et TTS (rush*.mp3).
    Génère broll_timing.json (et rien d'autre).
    
    Args:
        config (dict): Configuration du projet (si None, charge depuis config.yml)
    """
    import yaml
    import os
    import json
    import traceback
    from pathlib import Path
    
    # Supprimer les fichiers de log précédents pour repartir à zéro
    log_files = [
        "log-openai-ask_gpt_to_choose_best_broll.txt",
        "log-openai-ask_gpt_to_choose_best_broll.html"
    ]
    for log_file in log_files:
        if os.path.exists(log_file):
            os.remove(log_file)
            print(f"Fichier de log supprimé: {log_file}")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    try:
        # Charger la configuration si pas fournie
        if config is None:
            try:
                with open('config.yml', 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            except Exception as e:
                logging.error(f"Erreur lors du chargement de config.yml: {e}")
                return
        
        finder = BRollFinder(config)
        rush_durations = []
        
        # Détecter le mode audio (TTS ou Heygen)
        audio_mode = config['audio'].get('generation_mode', 'heygen')
        logging.info(f"Audio mode detected: {audio_mode}")
        
        if audio_mode in ['openai_tts', 'gemini_tts']:
            # Mode TTS : lire les durées réelles des MP3
            audio_dir = Path(config['paths']['temp']) / 'audio'
            
            # Chercher tous les fichiers bullet*.mp3
            bullet_files = sorted(audio_dir.glob('bullet*.mp3'))
            
            if not bullet_files:
                logging.error(f"No bullet*.mp3 files found in {audio_dir}")
                if audio_mode == 'openai_tts':
                    logging.error("Run 'python3 exponential_video.py -a' first to generate TTS audio")
                else:
                    logging.error("Run 'python3 exponential_video.py -ag' first to generate Gemini TTS audio")
                return
            
            # Read actual MP3 durations
            for bullet_file in bullet_files:
                try:
                    # Use file size-based approximation
                    file_size = bullet_file.stat().st_size
                    # Estimation: ~1KB per second for MP3 128kbps
                    real_duration = file_size / 1000.0
                    rush_durations.append(real_duration)
                    logging.info(f"{bullet_file.name}: {real_duration:.3f}s")
                except Exception as e:
                    logging.error(f"Unable to read duration of {bullet_file}: {e}")
                    return
                
        else:
            # Mode Heygen : lire les vidéos MP4
            heygen_path = Path(config['paths']['heygen'])
            rush_videos = sorted(heygen_path.glob('rush*.mp4'))
            
            if not rush_videos:
                logging.error("No rush videos found in heygen folder")
                logging.error("Run 'python3 exponential_video.py -r' first to generate Heygen rushes")
                return
            
            for video_path in rush_videos:
                # Use default duration for testing
                rush_durations.append(10.0)  # Approximate duration
                logging.info(f"Duration of {video_path.name}: {rush_durations[-1]}s")
        
        if not rush_durations:
            logging.error("No rush duration found")
            return
        
        # Générer les timings B-roll
        json_path = finder.generate_broll_timing(rush_durations, selection_mode='vector', audio_mode=audio_mode)
        logging.info(f"Vector b-roll preparation completed, results saved in {json_path}")
        
        fin_vector_broll()
        
    except Exception as e:
        logging.error(f"Error during vector b-roll preparation: {e}")
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    # Exécuter la préparation des b-rolls
    prepare_brolls_vector() 