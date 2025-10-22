#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de paraphrase qui utilise GPT-4o pour transformer le texte original
en un nouveau script structuré en paragraphes, avec gestion des étapes I1, I2, I3.
"""

import logging
import json
import os
from pathlib import Path
from openai import OpenAI
import re
from jouer_son import fin_script

class Paraphraser:
    """
    Classe gérant la paraphrase du texte original en utilisant GPT-4o.
    Génère les livrables I1, I2 et I3 dans le dossier temp.
    """

    def __init__(self, config):
        """
        Initialise le paraphraseur avec la configuration.
        
        Args:
            config (dict): Configuration chargée depuis config.yml
        """
        self.client = OpenAI(
            api_key=config['api']['openai']['api_key'],
            max_retries=config['api']['openai'].get('max_retries', 1)
        )
        self.config = config
        self.source_path = Path(config['paths']['source'])
        self.temp_path = Path(config['paths']['temp'])
        self.model = config['api']['openai']['model']
        self.max_retries = config['api']['openai']['max_retries']

    def read_original_text(self):
        """
        Lit le fichier ori_vid.txt du projet.
        
        Returns:
            str: Contenu du fichier ori_vid.txt
        """
        try:
            # Utiliser le fichier ori_vid.txt du projet
            ori_vid_path = Path(self.config['paths']['project_ori_vid'])
            
            with open(ori_vid_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logging.error(f"Erreur lors de la lecture du fichier ori_vid.txt: {e}")
            raise

    def save_intermediate(self, content, filename):
        """
        Sauvegarde un livrable intermédiaire.
        
        Args:
            content (str): Contenu à sauvegarder
            filename (str): Nom du fichier de sauvegarde
        """
        filepath = self.temp_path / filename
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info(f"Fichier {filename} sauvegardé")
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde de {filename}: {e}")
            raise

    #
        """
        Crée le prompt pour le livrable I1.
        2025-08-02 : j'enlève toute contrainte de taille de paragraphe pour qu'il se focus sur le nombre de paragraphes sans se répter déjà.
        """
    def create_i1_prompt(self, original_text):
        """
        Crée le prompt pour le livrable I1.
        
        Args:
            original_text (str): Texte original à paraphraser
            
        Returns:
            dict: Messages formatés pour l'API OpenAI
        """
        prompt = [
            {"role": "system", "content": """Vous êtes un expert en réécriture de scripts vidéo.
             Créez un script de voix off qui paraphrase le texte fourni en français. Attention à ne pas seulement traduire en français, mais à paraphraser le texte et considérer que le public est un public français, utilisant l'euro et pas le dollar.
             Répondez UNIQUEMENT en format JSON valide avec la structure suivante:
             {"paragraphs": ["paragraphe1", "paragraphe2", ...]}"""},
            {"role": "user", "content": f"""Texte original:
             {original_text}
             
Instructions spécifiques :
1. Créez exactement {self.config['script']['paragraphs'] + 2} paragraphes
2. Chaque paragraphe doit être UNIQUE et aborder un aspect différent du sujet
            
             Règles d'enrichissement intelligent:
1. Paraphrasez et DÉVELOPPEZ chaque idée avec des exemples concrets, des chiffres supplémentaires, ou des analogies
2. Ajoutez des contextes historiques, des comparaisons avec d'autres investisseurs, ou des implications pratiques
3. Variez les angles : impact économique, psychologie des marchés, leçons pour les particuliers, tendances actuelles
4. Si le contenu original est insuffisant, créez de NOUVEAUX paragraphes sur des aspects différents
5. INTERDICTION ABSOLUE de répéter le même contenu - chaque paragraphe doit apporter une valeur unique
6. Le script ne doit contenir aucune phrase originale du texte original
7. Répondez UNIQUEMENT en JSON valide

Exemples d'enrichissement :
- Si le texte parle de Buffett, ajoutez des comparaisons avec d'autres investisseurs
- Si ça parle de liquidités, expliquez l'impact sur différents secteurs
- Si ça parle de stratégie, donnez des exemples concrets d'application
- Créez des paragraphes sur les implications pour les investisseurs particuliers"""}
        ]
        
        return prompt

    def create_i2_prompt(self, i1_content):
        """
        Crée le prompt pour le livrable I2.
        
        Args:
            i1_content (str): Contenu du livrable I1
            
        Returns:
            dict: Messages formatés pour l'API OpenAI
        """
        return [
            {"role": "system", "content": "Transformez tout dialogue direct en voix off narrative. Répondez en format JSON."},
            {"role": "user", "content": f"""Convertissez ce script en voix off narrative:
             {i1_content}
             
             Style d'écriture:
             Réécris le texte suivant en SVO, voix active, présent, 12–18 mots par phrase, max 1 virgule, sans listes ni deux-points, concret d'abord, 1 question rhétorique toutes les ~100 mots, transitions courtes (Sauf que. Mais voilà. Et là, tout change.), et termine chaque bloc par une conséquence ou une action. Adresse le public en vous. Corrige le jargon et les nominalisations. Fournis uniquement le texte final.

             Règles:
             1. Remplacez les dialogues directs par "Selon [nom], ..." ou "[nom] explique que ..." et conservez surtout les informations spécifiques, pédagogiques ou factuelles. Supprimez toute référence personnelle au YouTuber (ex. : "comme moi", "je vous invite", "j’ai fait", etc.), toute mention de son expérience, de ses réussites ou de ses formations ainsi que toute mention de ses sponsors, promotion, mention de sponsors, liens, appels à l’action, témoignages de succès ou chiffres d’autorité liés au créateur ou à ses services. Le texte final doit être neutre, informatif et sans auto-promotion.
             2. Gardez la structure en {self.config['script']['paragraphs'] + 2} paragraphes, si il manque des paragraphes, créez-en de nouveaux - NE RÉPÉTEZ AUCUN CONTENU
             3. Pour chaque paragraphe, si il est trop court (moins de {self.config['script']['words_per_paragraph']} mots), enrichissez-les avec des informations nouvelles et pertinentes, pas avec des répétitions
             4. IMPORTANT: Chaque paragraphe doit rester unique et distinct des autres
             5. Répondez en format JSON avec la structure {{"paragraphs": ["paragraphe1", "paragraphe2", ...]}}"""}
        ]

    def create_i3_prompt(self, i2_content):
        """
        Crée le prompt pour le livrable I3.
        
        Args:
            i2_content (str): Contenu du livrable I2
            
        Returns:
            dict: Messages formatés pour l'API OpenAI
        """
        return [
            {"role": "system", "content": "Vérifiez et ajustez le nombre de mots par paragraphe. Répondez en format JSON."},
            {"role": "user", "content": f"""Vérifiez et ajustez ce script:
             {i2_content}
             
             Style:
             Utilise dans tes phrases les tics suivants, pas de politiquement correct / charabia corporate:
             des, les, c’est, ce sont, en fait, donc, alors, voilà, par exemple, typiquement, en gros, autrement dit, imagine, d’abord, ensuite, aujourd’hui, c’est, ce sont, en fait, clairement, attention, regardez, voyez, voilà, incroyable, énorme, dingue, fou, encore une fois
             
             Règles:
             1. Vérifiez d'abord le nombre de paragraphes existants. Si vous avez déjà {self.config['script']['paragraphs'] + 2} paragraphes, NE RÉPÉTEZ PAS le contenu existant. Si vous avez moins de {self.config['script']['paragraphs'] + 2} paragraphes, créez de NOUVEAUX paragraphes avec du contenu différent et original.
             2. Chaque paragraphe doit faire au moins {self.config['script']['words_per_paragraph']} mots. Si un paragraphe est trop court, enrichissez-le avec des informations supplémentaires sans répéter le contenu existant.
             3. Le total doit faire au moins {self.config['script']['total_words']} mots.
             4. IMPORTANT : Ne répétez jamais le même contenu. Chaque paragraphe doit être unique et original.
             5. Répondez en format JSON avec la structure {{"paragraphs": ["paragraphe1", "paragraphe2", ...]}}"""}
        ]
    


    def clean_json_response(self, content):
        """Nettoie la réponse pour extraire uniquement le JSON valide."""
        # Enlève les backticks et le mot 'json' si présents
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        return content.strip()

    def detect_encoding_corruption(self, content):
        """
        Détecte et corrige les problèmes d'encodage d'accents dans le contenu.
        
        Args:
            content (str): Contenu à vérifier
            
        Returns:
            tuple: (is_corrupted, cleaned_content)
        """
        # Détecter les patterns de corruption d'accents
        corruption_patterns = [
            ('\u0000e9', 'é'),  # é corrompu
            ('\u0000e8', 'è'),  # è corrompu
            ('\u0000e0', 'à'),  # à corrompu
            ('\u0000e7', 'ç'),  # ç corrompu
            ('\u0000ea', 'ê'),  # ê corrompu
            ('\u0000ef', 'ï'),  # ï corrompu
            ('\u0000ee', 'î'),  # î corrompu
            ('\u0000f4', 'ô'),  # ô corrompu
            ('\u0000f9', 'ù'),  # ù corrompu
            ('\u0000fb', 'û'),  # û corrompu
            ('\u0000e2', 'â'),  # â corrompu
            ('\u0000c9', 'É'),  # É corrompu
            ('\u0000c0', 'À'),  # À corrompu
        ]
        
        is_corrupted = False
        cleaned_content = content
        
        for corrupted, correct in corruption_patterns:
            if corrupted in content:
                is_corrupted = True
                cleaned_content = cleaned_content.replace(corrupted, correct)
                logging.warning(f"Correction d'encodage: '{corrupted}' → '{correct}'")
        
        # Nettoyer aussi les caractères null génériques
        if '\u0000' in cleaned_content:
            is_corrupted = True
            cleaned_content = cleaned_content.replace('\u0000', '')
            logging.warning("Suppression des caractères null résiduels")
        
        return is_corrupted, cleaned_content

    def call_gpt5(self, messages, max_retries=3):
        """Appelle l'API GPT-5 avec la nouvelle API responses."""
        for attempt in range(max_retries):
            try:
                # Convertir les messages en input string
                input_text = ""
                for msg in messages:
                    if msg['role'] == 'system':
                        input_text += f"SYSTEM: {msg['content']}\n\n"
                    elif msg['role'] == 'user':
                        input_text += f"USER: {msg['content']}\n\n"
                    elif msg['role'] == 'assistant':
                        input_text += f"ASSISTANT: {msg['content']}\n\n"
                
                response = self.client.responses.create(
                    model="gpt-5",
                    input=input_text.strip(),
                    reasoning={"effort": "low"},
                    text={"verbosity": "low", "format": {"type": "json_object"}}
                )
                
                # Debug: Afficher la réponse brute de GPT-5
                # logging.info("🔍 RÉPONSE BRUTE GPT-5:")
                # logging.info(f"Type de réponse: {type(response)}")
                # logging.info(f"Attributs disponibles: {dir(response)}")
                # if hasattr(response, 'output_text'):
                #     logging.info(f"output_text: {response.output_text[:500]}...")
                # else:
                #     logging.info("Pas d'attribut output_text")
                #     logging.info(f"Contenu de la réponse: {response}")
                
                # Parser le JSON de la réponse GPT-5
                import json
                parsed_content = json.loads(response.output_text)
                #logging.info(f"JSON parsé: {parsed_content}")
                
                # Retourner directement le contenu parsé
                return parsed_content
                
            except Exception as e:
                logging.error(f"❌ Erreur GPT-5 (tentative {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    logging.info(f"🔄 Nouvelle tentative dans 2 secondes...")
                    import time
                    time.sleep(2)
                    continue
                else:
                    raise

    def call_gpt5_text_only(self, messages, max_retries=3):
        """Appelle l'API GPT-5 pour des réponses en texte libre (pas JSON)."""
        for attempt in range(max_retries):
            try:
                # Convertir les messages en input string
                input_text = ""
                for msg in messages:
                    if msg['role'] == 'system':
                        input_text += f"SYSTEM: {msg['content']}\n\n"
                    elif msg['role'] == 'user':
                        input_text += f"USER: {msg['content']}\n\n"
                    elif msg['role'] == 'assistant':
                        input_text += f"ASSISTANT: {msg['content']}\n\n"
                
                response = self.client.responses.create(
                    model="gpt-5",
                    input=input_text.strip(),
                    reasoning={"effort": "low"},
                    text={"verbosity": "low"}
                )
                # Retourner directement le texte
                return response.output_text
                
            except Exception as e:
                logging.error(f"❌ Erreur GPT-5 texte (tentative {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    logging.info(f"🔄 Nouvelle tentative dans 2 secondes...")
                    import time
                    time.sleep(2)
                    continue
                else:
                    raise

    # DEPRECATED - Utiliser call_gpt5() à la place
    # def call_gpt4(self, messages, max_retries=3):
    #     """Appelle l'API GPT avec les messages donnés et détection d'encodage."""
    #     for attempt in range(max_retries):
    #         try:
    #             logging.info(f"Envoi de la requête à GPT... (tentative {attempt + 1}/{max_retries})")
    #             logging.info(f"Modèle utilisé: {self.config['api']['openai']['model']}")
    #             logging.info(f"Nombre de messages: {len(messages)}")
    #             logging.info(f"Taille du prompt: {len(str(messages))} caractères")
                
    #             # Debug: Afficher la requête complète pour debug
    #             logging.info("=" * 80)
    #             logging.info("🔍 REQUÊTE COMPLÈTE POUR DEBUG:")
    #             logging.info("=" * 80)
    #             for i, msg in enumerate(messages):
    #                 logging.info(f"Message {i+1} ({msg['role']}):")
    #                 logging.info(f"Contenu: {msg['content']}")  # Contenu complet
    #             logging.info("=" * 80)
                
    #             # Debug: Afficher la requête au format curl
    #             logging.info("🌐 REQUÊTE CURL POUR TEST:")
    #             logging.info("=" * 80)
    #             if self.config['api']['openai']['model'] == 'gpt-5':
    #                 # Convertir les messages en input string pour curl
    #                 input_text = ""
    #                 for msg in messages:
    #                     if msg['role'] == 'system':
    #                         input_text += f"SYSTEM: {msg['content']}\n\n"
    #                     elif msg['role'] == 'user':
    #                         input_text += f"USER: {msg['content']}\n\n"
    #                     elif msg['role'] == 'assistant':
    #                         input_text += f"ASSISTANT: {msg['content']}\n\n"
                    
    #                 # curl_request = f"""curl -X POST "https://api.openai.com/v1/responses" \\
    #                 #   -H "Content-Type: application/json" \\
    #                 #   -H "Authorization: Bearer {self.config['api']['openai']['api_key']}" \\
    #                 #   -d '{{
    #                 #     "model": "gpt-5",
    #                 #     "input": "{input_text.strip().replace('"', '\\"')}",
    #                 #     "reasoning": {{"effort": "low"}},
    #                 #     "text": {{"verbosity": "low", "format": {{"type": "json_object"}}}}
    #                 #   }}'"""
    #             else:
    #                 # curl_request = f"""curl -X POST "https://api.openai.com/v1/chat/completions" \\
    #                 #   -H "Content-Type: application/json" \\
    #                 #   -H "Authorization: Bearer {self.config['api']['openai']['api_key']}" \\
    #                 #   -d '{{
    #                 #     "model": "{self.config['api']['openai']['model']}",
    #                 #     "messages": {json.dumps(messages, ensure_ascii=False)},
    #                 #     "response_format": {{"type": "json_object"}}
    #                 #   }}'"""
    #                 # logging.info(curl_request)
    #                 # logging.info("=" * 80)
                    
    #                 # Utiliser GPT-5 directement
    #                 response = self.call_gpt5(messages)
                
    #             logging.info("✅ Requête GPT envoyée avec succès")
            
    #             # Debug logs
    #             logging.info("Réponse reçue de GPT-4")
    #             content = response.choices[0].message.content
    #             logging.info(f"Type de contenu reçu: {type(content)}")
                
    #             # Détecter et corriger les problèmes d'encodage
    #             is_corrupted, cleaned_content = self.detect_encoding_corruption(content)
                
    #             if is_corrupted:
    #                 logging.error(f"❌ ACCENTS CORROMPUS DÉTECTÉS ! Tentative {attempt + 1}/{max_retries}")
    #                 if attempt < max_retries - 1:
    #                     logging.info("Relance automatique de l'API GPT-4...")
    #                     continue  # Retry
    #                 else:
    #                     logging.warning("⚠️ Utilisation du contenu corrigé après toutes les tentatives")
    #                     content = cleaned_content
    #             else:
    #                 content = cleaned_content
    #                 logging.info("✅ Encodage des accents correct")
            
    #             try:
    #                 parsed_content = json.loads(content)
    #                 logging.info(f"Contenu JSON parsé avec succès")
    #                 return parsed_content
                
    #             except json.JSONDecodeError as je:
    #                 logging.error(f"Erreur de parsing JSON: {je}")
    #                 if attempt < max_retries - 1:
    #                     logging.info("Relance automatique due à l'erreur JSON...")
    #                     continue
    #                 else:
    #                     raise
                
    #         except Exception as e:
    #             error_type = type(e).__name__
    #             logging.error(f"❌ Erreur {error_type} lors de l'appel à GPT (tentative {attempt + 1}): {str(e)}")
                
    #             if "timeout" in str(e).lower():
    #                 logging.error("⏰ TIMEOUT détecté - la requête a pris plus de 60 secondes")
    #             elif "rate" in str(e).lower():
    #                 logging.error("🚫 RATE LIMIT détecté - trop de requêtes")
    #             elif "quota" in str(e).lower():
    #                 logging.error("💳 QUOTA dépassé")
    #             elif "api" in str(e).lower():
    #                 logging.error("🔌 Erreur API")
    #             else:
    #                 logging.error(f"❓ Erreur inconnue: {error_type}")
                
    #             if attempt < max_retries - 1:
    #                 logging.info(f"🔄 Nouvelle tentative dans 2 secondes... (tentative {attempt + 2}/{max_retries})")
    #                 import time
    #                 time.sleep(2)
    #                 continue
    #             else:
    #                 logging.error(f"💥 Échec définitif après {max_retries} tentatives: {str(e)}")
    #             raise

    # DEPRECATED - Utiliser call_gpt5_text_only() à la place
    def _call_gpt4_text_only(self, messages, max_retries=3):
        """Appelle l'API GPT pour des réponses en texte libre (pas JSON)."""
        for attempt in range(max_retries):
            try:
                logging.info(f"Envoi de la requête à GPT (texte libre)... (tentative {attempt + 1}/{max_retries})")
                # Utiliser GPT-5 directement
                response = self.call_gpt5_text_only(messages)
            
                logging.info("Réponse texte reçue de GPT-4")
                content = response.choices[0].message.content
                
                # Détecter et corriger les problèmes d'encodage
                is_corrupted, cleaned_content = self.detect_encoding_corruption(content)
                
                if is_corrupted:
                    logging.error(f"❌ ACCENTS CORROMPUS DÉTECTÉS ! Tentative {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        logging.info("Relance automatique de l'API GPT-4...")
                        continue
                    else:
                        logging.warning("⚠️ Utilisation du contenu corrigé après toutes les tentatives")
                        content = cleaned_content
                else:
                    content = cleaned_content
                    logging.info("✅ Encodage des accents correct")
                
                return content
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logging.warning(f"Erreur lors de l'appel à GPT-4o (tentative {attempt + 1}): {str(e)}")
                    logging.info("Nouvelle tentative...")
                    continue
                else:
                    logging.error(f"Échec définitif après {max_retries} tentatives: {str(e)}")
                raise

    def verify_paragraphs(self, paragraphs):
        """
        Vérifie que les paragraphes respectent les contraintes avec une marge de ±20%.
        
        Args:
            paragraphs (list): Liste des paragraphes
            
        Returns:
            bool: True si les contraintes sont respectées
        """
        expected_paragraphs = self.config['script']['paragraphs']
        # Marge de tolérance de ±2 paragraphes
        min_paragraphs = expected_paragraphs - 2
        max_paragraphs = expected_paragraphs + 2
        
        if len(paragraphs) < min_paragraphs:
            logging.warning(f"Nombre insuffisant de paragraphes: {len(paragraphs)} (minimum: {min_paragraphs})")
            return False
        elif len(paragraphs) > max_paragraphs:
            logging.info(f"✅ Nombre de paragraphes en excès: {len(paragraphs)} (attendu: {expected_paragraphs} ±2)")
            logging.info(f"ℹ️  Le pipeline s'adaptera automatiquement à {len(paragraphs)} paragraphes - vidéo plus longue")
        else:
            logging.info(f"✅ Nombre de paragraphes acceptable: {len(paragraphs)} (attendu: {expected_paragraphs} ±2)")
        
        # Vérifier les répétitions de contenu
        if self._detect_content_repetition(paragraphs):
            logging.error("❌ RÉPÉTITION DE CONTENU DÉTECTÉE dans les paragraphes !")
            return False
        
        # Marge de tolérance élargie : 40-70 mots par paragraphe
        min_words = 40
        max_words = 70
        
        # Identifier les paragraphes problématiques
        problematic_paragraphs = []
        
        for i, para in enumerate(paragraphs, 1):
            words = len(para.split())
            if words < min_words or words > max_words:
                logging.warning(f"Paragraphe {i} : {words} mots (hors de la plage {min_words}-{max_words})")
                problematic_paragraphs.append((i-1, para, words))  # i-1 car enumerate commence à 1
            else:
                logging.info(f"Paragraphe {i} : {words} mots (dans la plage acceptable)")
        
        # Si des paragraphes sont problématiques, les corriger localement
        if problematic_paragraphs:
            logging.info(f"🔧 Correction locale de {len(problematic_paragraphs)} paragraphe(s) problématique(s)")
            corrected_paragraphs = self._fix_short_paragraphs(paragraphs, problematic_paragraphs, min_words, max_words)
            if corrected_paragraphs:
                # Remplacer les paragraphes originaux par les corrigés
                for i, corrected_para in corrected_paragraphs.items():
                    paragraphs[i] = corrected_para
                    logging.info(f"✅ Paragraphe {i+1} corrigé : {len(corrected_para.split())} mots")
            else:
                logging.error("❌ Échec de la correction locale des paragraphes")
                return False
        
        # Vérifier le nombre total de mots avec la même marge de tolérance
        total_words = sum(len(para.split()) for para in paragraphs)
        min_total = int(self.config['script']['total_words'] * 0.8)  # un peu plus petit, ok
        max_total = int(self.config['script']['total_words'] * 2)  # beaucoup plus grand, ok
        
        if total_words < min_total or total_words > max_total:
            logging.warning(f"Total : {total_words} mots (hors de la plage {min_total}-{max_total})")
            return False
        else:
            logging.info(f"Total : {total_words} mots (dans la plage acceptable)")
            
        return True

    def _fix_short_paragraphs(self, paragraphs, problematic_paragraphs, min_words, max_words):
        """
        Corrige localement les paragraphes trop courts en ajoutant des mots.
        
        Args:
            paragraphs (list): Liste complète des paragraphes
            problematic_paragraphs (list): Liste des tuples (index, paragraphe, nb_mots)
            min_words (int): Nombre minimum de mots requis
            max_words (int): Nombre maximum de mots autorisé
            
        Returns:
            dict: Dictionnaire {index: paragraphe_corrigé} ou None si échec
        """
        corrected_paragraphs = {}
        
        for index, para, current_words in problematic_paragraphs:
            if current_words < min_words:
                # Paragraphe trop court - ajouter des mots
                target_words = min_words + 2  # Cibler 42 mots pour avoir une marge
                words_to_add = target_words - current_words
                
                logging.info(f"🔧 Correction du paragraphe {index+1}: {current_words} → {target_words} mots")
                
                # Créer un prompt pour étendre le paragraphe
                extension_prompt = f"""
Tu es un expert en rédaction. Tu dois étendre ce paragraphe en ajoutant environ {words_to_add} mots supplémentaires, 
en gardant le même style et le même sens, sans répéter d'information.

Paragraphe actuel ({current_words} mots):
{para}

Instructions:
- Ajoute environ {words_to_add} mots
- Garde le même style et ton
- Ne répète pas d'information
- Reste cohérent avec le contenu
- Retourne UNIQUEMENT le paragraphe étendu, sans commentaires

Paragraphe étendu:"""

                messages = [
                    {"role": "system", "content": "Tu es un expert en rédaction qui étend des paragraphes de manière naturelle et cohérente."},
                    {"role": "user", "content": extension_prompt}
                ]
                
                try:
                    response = self.call_gpt5_text_only(messages)
                    if response and isinstance(response, str):
                        # Nettoyer la réponse
                        corrected_para = response.strip()
                        # Vérifier que le paragraphe corrigé a le bon nombre de mots
                        corrected_words = len(corrected_para.split())
                        if min_words <= corrected_words <= max_words:
                            corrected_paragraphs[index] = corrected_para
                            logging.info(f"✅ Paragraphe {index+1} corrigé: {current_words} → {corrected_words} mots")
                        else:
                            logging.warning(f"⚠️ Paragraphe {index+1} toujours incorrect après correction: {corrected_words} mots")
                    else:
                        logging.error(f"❌ Réponse invalide pour la correction du paragraphe {index+1}")
                except Exception as e:
                    logging.error(f"❌ Erreur lors de la correction du paragraphe {index+1}: {e}")
            
            elif current_words > max_words:
                # Paragraphe trop long - raccourcir
                target_words = max_words - 2  # Cibler 68 mots pour avoir une marge
                words_to_remove = current_words - target_words
                
                logging.info(f"🔧 Raccourcissement du paragraphe {index+1}: {current_words} → {target_words} mots")
                
                # Créer un prompt pour raccourcir le paragraphe
                shortening_prompt = f"""
Tu es un expert en rédaction. Tu dois raccourcir ce paragraphe en supprimant environ {words_to_remove} mots, 
en gardant le même style et les informations essentielles.

Paragraphe actuel ({current_words} mots):
{para}

Instructions:
- Supprime environ {words_to_remove} mots
- Garde le même style et ton
- Conserve les informations essentielles
- Reste cohérent avec le contenu
- Retourne UNIQUEMENT le paragraphe raccourci, sans commentaires

Paragraphe raccourci:"""

                messages = [
                    {"role": "system", "content": "Tu es un expert en rédaction qui raccourcit des paragraphes en gardant l'essentiel."},
                    {"role": "user", "content": shortening_prompt}
                ]
                
                try:
                    response = self.call_gpt5_text_only(messages)
                    if response and isinstance(response, str):
                        # Nettoyer la réponse
                        corrected_para = response.strip()
                        # Vérifier que le paragraphe corrigé a le bon nombre de mots
                        corrected_words = len(corrected_para.split())
                        if min_words <= corrected_words <= max_words:
                            corrected_paragraphs[index] = corrected_para
                            logging.info(f"✅ Paragraphe {index+1} raccourci: {current_words} → {corrected_words} mots")
                        else:
                            logging.warning(f"⚠️ Paragraphe {index+1} toujours incorrect après raccourcissement: {corrected_words} mots")
                    else:
                        logging.error(f"❌ Réponse invalide pour le raccourcissement du paragraphe {index+1}")
                except Exception as e:
                    logging.error(f"❌ Erreur lors du raccourcissement du paragraphe {index+1}: {e}")
        
        return corrected_paragraphs if corrected_paragraphs else None

    def _detect_content_repetition(self, paragraphs):
        """
        Détecte les répétitions de contenu dans les paragraphes.
        
        Args:
            paragraphs (list): Liste des paragraphes
            
        Returns:
            bool: True si des répétitions sont détectées
        """
        # Normaliser les paragraphes pour la comparaison
        normalized_paragraphs = []
        for para in paragraphs:
            # Supprimer la ponctuation et mettre en minuscules
            normalized = re.sub(r'[^\w\s]', '', para.lower())
            normalized_paragraphs.append(normalized)
        
        # Vérifier les répétitions
        for i, para1 in enumerate(normalized_paragraphs):
            for j, para2 in enumerate(normalized_paragraphs[i+1:], i+1):
                # Calculer la similarité (ratio de mots communs)
                words1 = set(para1.split())
                words2 = set(para2.split())
                
                if len(words1) > 0 and len(words2) > 0:
                    similarity = len(words1.intersection(words2)) / max(len(words1), len(words2))
                    
                    # Si plus de 70% de similarité, c'est une répétition
                    if similarity > 0.7:
                        logging.error(f"🚨 RÉPÉTITION DÉTECTÉE entre paragraphes {i+1} et {j+1} (similarité: {similarity:.2f})")
                        logging.error(f"Paragraphe {i+1}: {paragraphs[i][:100]}...")
                        logging.error(f"Paragraphe {j+1}: {paragraphs[j][:100]}...")
                        return True
        
        logging.info("✅ Aucune répétition de contenu détectée")
        return False

    def process(self):
        """
        Processus principal de paraphrase.
        Génère les trois livrables I1, I2 et I3.
        """
        logging.info("Début du processus de paraphrase")
        
        # Vérifier que le fichier ori_vid.txt du projet existe
        project_ori_vid_path = Path(self.config['paths']['project_ori_vid'])
        if not project_ori_vid_path.exists():
            raise FileNotFoundError(f"Le fichier {project_ori_vid_path} est requis pour la génération des scripts")
        
        # Lecture du texte original
        original_text = self.read_original_text()
        logging.info("Texte original lu avec succès")
        
        # Génération I1
        logging.info("Génération du livrable I1... (environ 2 minutes)")
        i1_messages = self.create_i1_prompt(original_text)
        i1_response = self.call_gpt5(i1_messages)
        logging.info("call_gpt ok")
        
        # Debug: Afficher le contenu de la réponse I1
        logging.info("🔍 DEBUG RÉPONSE I1:")
        logging.info(f"Type de i1_response: {type(i1_response)}")
        logging.info(f"Contenu de i1_response: {i1_response}")
        if isinstance(i1_response, dict):
            logging.info(f"Clés disponibles: {list(i1_response.keys())}")
            if 'paragraphs' in i1_response:
                logging.info(f"Nombre de paragraphes: {len(i1_response['paragraphs'])}")
                logging.info(f"Premier paragraphe: {i1_response['paragraphs'][0][:100]}...")
        
        # Sauvegarder I1
        if isinstance(i1_response, dict) and 'paragraphs' in i1_response:
            i1_content = "\n\n".join(i1_response['paragraphs'])
            self.save_intermediate(i1_content, 'i1.txt')
            
            # Vérification de répétition au I1
            logging.info("Vérification de répétition au I1... ")
            if self._detect_content_repetition(i1_response['paragraphs']):
                logging.error("❌ RÉPÉTITION DE CONTENU DÉTECTÉE dans I1 !")
                logging.warning("🔄 Relance de la génération I1...")
                i1_response = self.call_gpt5(i1_messages)
                if isinstance(i1_response, dict) and 'paragraphs' in i1_response:
                    i1_content = "\n\n".join(i1_response['paragraphs'])
                    self.save_intermediate(i1_content, 'i1.txt')
                    logging.info("✅ I1 corrigé et sauvegardé")
                else:
                    raise ValueError("Format de réponse invalide pour I1 après correction")
            else:
                logging.info("✅ Aucune répétition détectée dans I1")
        else:
            raise ValueError("Format de réponse invalide pour I1")
        
        # Génération I2
        logging.info("Génération du livrable I2... (environ 3 minutes)")
        i2_messages = self.create_i2_prompt(i1_content)
        i2_response = self.call_gpt5(i2_messages)
        logging.info("call_gpt ok")
        i2_content = "\n\n".join(i2_response['paragraphs'])
        self.save_intermediate(i2_content, 'i2.txt')
        
        # Génération I3
        logging.info("Génération du livrable I3... (environ 4 minutes)")
        i3_messages = self.create_i3_prompt(i2_content)
        i3_response = self.call_gpt5(i3_messages)
        logging.info("call_gpt ok")
        
        # Traitement simple : toujours des paragraphes
        if 'paragraphs' in i3_response:
            i3_content = "\n\n".join(i3_response['paragraphs'])
            logging.info(f"Script I3 généré avec {len(i3_response['paragraphs'])} paragraphes")
        else:
            raise ValueError("Format de réponse invalide pour I3 (paragraphs manquants)")
        
        # Vérification finale des paragraphes
        max_retries_i3 = 3
        for attempt in range(max_retries_i3):
            if self.verify_paragraphs(i3_response['paragraphs']):
                logging.info("✅ Vérification des paragraphes réussie")
                break
            else:
                if attempt < max_retries_i3 - 1:
                    logging.warning(f"🔄 Relance de la génération I3 (tentative {attempt + 2}/{max_retries_i3})")
                    i3_messages.append({"role": "assistant", "content": json.dumps(i3_response)})
                    i3_messages.append({"role": "user", "content": f"Corrigez les problèmes détectés. Assurez-vous d'avoir exactement {self.config['script']['paragraphs']} paragraphes uniques de {self.config['script']['words_per_paragraph']} mots chacun, sans répétition de contenu."})
                    i3_response = self.call_gpt5(i3_messages)
                    i3_content = "\n\n".join(i3_response['paragraphs'])
                else:
                    logging.error("❌ Échec de la génération I3 après toutes les tentatives")
                    raise ValueError("Impossible de générer un script I3 valide sans répétitions")
        
        # Vérification finale de l'encodage d'i3
        is_corrupted, cleaned_i3_content = self.detect_encoding_corruption(i3_content)
        if is_corrupted:
            logging.error("❌ PROBLÈME D'ACCENTS DÉTECTÉ dans i3.txt final !")
            logging.info("🔄 Relance automatique de la génération i3...")
            
            # Relancer i3 avec un prompt plus explicite sur l'encodage
            i3_messages_fixed = self.create_i3_prompt(i2_content)
            i3_messages_fixed[0]["content"] += " IMPORTANT: Utilisez uniquement des caractères UTF-8 standard."
            i3_response_fixed = self.call_gpt5(i3_messages_fixed)
            i3_content = "\n\n".join(i3_response_fixed['paragraphs'])
            
            # Re-vérifier
            is_corrupted_2, cleaned_i3_content_2 = self.detect_encoding_corruption(i3_content)
            if is_corrupted_2:
                logging.warning("⚠️ Problème persistant, utilisation du contenu corrigé")
                i3_content = cleaned_i3_content_2
            else:
                logging.info("✅ Problème d'accents résolu !")
        
        self.save_intermediate(i3_content, 'i3.txt')
        
        # Vérification post-sauvegarde
        self.verify_i3_file_quality()
        
        fin_script()
        logging.info("Processus de paraphrase terminé avec succès") 
    
    def verify_i3_file_quality(self):
        """
        Vérifie la qualité du fichier i3.txt après sauvegarde.
        """
        i3_path = self.temp_path / 'i3.txt'
        
        try:
            with open(i3_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Vérifier les caractères corrompus
            is_corrupted, _ = self.detect_encoding_corruption(content)
            
            if is_corrupted:
                logging.error("❌ FICHIER i3.txt CORROMPU DÉTECTÉ après sauvegarde !")
                logging.error("Veuillez relancer 'python3 exponential_video.py -s'")
                raise ValueError("Fichier i3.txt contient des accents corrompus")
            else:
                logging.info("✅ Fichier i3.txt vérifié - encodage correct")
                
        except Exception as e:
            logging.error(f"Erreur lors de la vérification de i3.txt: {e}")
            raise 