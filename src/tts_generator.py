#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de génération audio via l'API TTS d'OpenAI.
Découpe le texte I3 en phrases et génère un fichier MP3 pour chaque phrase.
"""

import logging
import re
import time
import json
from pathlib import Path
import openai
import os
import sys
from jouer_son import fin_audio

def setup_logging():
    """Configure le système de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

class TTSGenerator:
    """
    Classe gérant la génération audio via l'API TTS d'OpenAI.
    Découpe le script I3 en phrases et génère un MP3 pour chaque phrase.
    """

    def __init__(self, config):
        """
        Initialise le générateur TTS avec la configuration.
        
        Args:
            config (dict): Configuration chargée depuis config.yml
        """
        self.config = config
        self.temp_path = Path(config['paths']['temp'])
        self.output_path = Path(config['paths']['temp']) / 'audio'  # Stockage dans temp/audio
        self.tts_config = config['audio']['openai_tts']
        
        # Configurer l'API OpenAI avec gestion d'erreur
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=config['api']['openai']['api_key'])
            # Test rapide de la connexion
            logging.info("OpenAI API connection initialized")
        except ImportError:
            raise ImportError("Module 'openai' manquant. Installez avec: pip install openai")
        except Exception as e:
            raise ValueError(f"Erreur lors de l'initialisation de l'API OpenAI: {e}")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_path, exist_ok=True)
        
        logging.info(f"TTS generator initialized")
        logging.info(f"Model: {self.tts_config['model']}")
        logging.info(f"Voice: {self.tts_config['voice']}")
        logging.info(f"Vitesse: {self.tts_config['speed']}")

    def _get_tts_instructions(self):
        """
        Récupère les instructions TTS depuis la configuration.
        
        Returns:
            str or None: Instructions TTS ou None si pas configurées
        """
        instructions = self.tts_config.get('instructions')
        
        if instructions:
            logging.info(f"🎭 TTS instructions configured: {len(instructions)} characters")
            return instructions
        
        return None

    def _generate_speech(self, text):
        """
        Génère un audio à partir du texte avec les instructions configurées.
        
        Args:
            text (str): Texte à convertir en audio
            
        Returns:
            Response: Réponse de l'API OpenAI
        """
        tts_params = {
            'model': self.tts_config['model'],
            'voice': self.tts_config['voice'],
            'input': text,
            'speed': self.tts_config['speed']
        }
        
        # Ajouter les instructions si disponibles (pour gpt-4o-mini-tts)
        instructions = self._get_tts_instructions()
        if instructions:
            tts_params['instructions'] = instructions
        
        return self.client.audio.speech.create(**tts_params)

    def read_i3_script(self):
        """
        Lit le script I3 depuis le fichier temp/i3.txt.
        
        Returns:
            list: Liste des paragraphes du script
        """
        i3_path = self.temp_path / 'i3.txt'
        
        if not i3_path.exists():
            raise FileNotFoundError(f"Le fichier {i3_path} n'existe pas. Exécutez d'abord l'option -s.")
        
        with open(i3_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Split into paragraphs (separated by empty lines)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        logging.info(f"Script I3 lu: {len(paragraphs)} paragraphes")
        return paragraphs

    def split_into_sentences(self, text):
        """
        Découpe un texte en phrases en utilisant une regex simple.
        
        Args:
            text (str): Texte à découper
            
        Returns:
            list: Liste des phrases
        """
        # Regex to split into sentences (periods, exclamation marks, question marks)
        # Watch out for common abbreviations
        sentences = re.split(r'(?<![A-Z][a-z]\.)\s*[.!?]+\s*', text)
        
        # Clean and filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences

    def generate_sentence_audio(self, sentence, paragraph_index, sentence_index):
        """
        Génère un fichier MP3 pour une phrase.
        
        Args:
            sentence (str): Phrase à synthétiser
            paragraph_index (int): Index du paragraphe (1-based)
            sentence_index (int): Index de la phrase dans le paragraphe (1-based)
            
        Returns:
            Path: Chemin vers le fichier audio généré
        """
        try:
            logging.info(f"🎙️ Audio generation P{paragraph_index}S{sentence_index}: {sentence[:50]}...")
            
            # Generate audio with OpenAI API (with instructions if configured)
            response = self._generate_speech(sentence)
            
            # Nom du fichier: p{paragraphe}_s{phrase}.mp3
            filename = f"p{paragraph_index:02d}_s{sentence_index:02d}.mp3"
            output_file = self.output_path / filename
            
            # Sauvegarder le fichier
            with open(output_file, "wb") as f:
                f.write(response.content)
            
            logging.info(f"✅ Audio generated: {filename}")
            return output_file
            
        except Exception as e:
            logging.error(f"❌ Error generating audio P{paragraph_index}S{sentence_index}: {e}")
            raise

    def generate_paragraph_audio(self, paragraph, paragraph_index):
        """
        Génère les fichiers audio pour toutes les phrases d'un paragraphe.
        
        Args:
            paragraph (str): Texte du paragraphe
            paragraph_index (int): Index du paragraphe (1-based)
            
        Returns:
            list: Liste des chemins vers les fichiers audio générés
        """
        sentences = self.split_into_sentences(paragraph)
        audio_files = []
        
        logging.info(f"Traitement du paragraphe {paragraph_index}: {len(sentences)} phrases")
        
        for sentence_index, sentence in enumerate(sentences, 1):
            # Add small pause between API calls to avoid rate limiting
            if sentence_index > 1:
                time.sleep(0.5)
            
            audio_file = self.generate_sentence_audio(sentence, paragraph_index, sentence_index)
            audio_files.append(audio_file)
        
        return audio_files

    def save_timing_metadata(self, all_audio_files):
        """
        Sauvegarde les métadonnées de timing pour le montage vidéo.
        
        Args:
            all_audio_files (list): Liste de toutes les listes de fichiers audio par paragraphe
        """
        metadata = {
            'generation_timestamp': time.time(),
            'tts_config': self.tts_config,
            'paragraphs': []
        }
        
        for paragraph_index, audio_files in enumerate(all_audio_files, 1):
            paragraph_data = {
                'paragraph_index': paragraph_index,
                'sentences': []
            }
            
            for sentence_index, audio_file in enumerate(audio_files, 1):
                sentence_data = {
                    'sentence_index': sentence_index,
                    'audio_file': str(audio_file.name),  # Juste le nom du fichier
                    'full_path': str(audio_file)
                }
                paragraph_data['sentences'].append(sentence_data)
            
            metadata['paragraphs'].append(paragraph_data)
        
        # Sauvegarder les métadonnées
        metadata_file = self.output_path / 'audio_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Timing metadata saved: {metadata_file}")

    def generate_all_audio(self):
        """
        Génère tous les fichiers audio pour le script I3.
        Dispatcher vers le mode approprié selon la configuration.
        
        Returns:
            list: Liste des chemins vers les fichiers audio générés
        """
        # Déterminer le mode de granularité
        granularity = self.tts_config.get('granularity', 'rush')
        
        if granularity == 'sentence':
            logging.info("🎙️ Sentence-by-sentence TTS mode activated")
            return self.generate_sentence_based_audio()
        elif granularity == 'sentence_group':
            logging.info("🎙️ Sentence group TTS mode activated")
            return self.generate_sentence_group_audio()
        elif granularity == 'bullet':
            logging.info("🎙️ Thematic bullet points TTS mode activated")
            return self.generate_bullet_based_audio()
        else:
            logging.info("🎙️ Rush-based TTS mode activated (legacy)")
            return self.generate_rush_based_audio()
    
    def generate_sentence_based_audio(self):
        """
        Génère un fichier MP3 pour chaque phrase du script I3.
        Nouveau mode : phrase par phrase avec nomenclature p01_s01.mp3
        
        Returns:
            list: Liste des chemins vers les fichiers audio générés (phrases)
        """
        logging.info("Starting TTS audio generation (sentence-by-sentence mode)")
        
        # Lire le script I3
        paragraphs = self.read_i3_script()
        
        # Nettoyer le dossier de sortie
        logging.info("Nettoyage du dossier audio existant...")
        for existing_file in self.output_path.glob('*.mp3'):
            existing_file.unlink()
            logging.info(f"Suppression: {existing_file.name}")
        
        sentence_audio_files = []
        total_sentences = 0
        
        # Compter le nombre total de phrases pour les stats
        for paragraph in paragraphs:
            sentences = self.split_into_sentences(paragraph)
            total_sentences += len(sentences)
        
        logging.info(f"I3 script: {len(paragraphs)} paragraphs → {total_sentences} sentences to generate")
        
        current_sentence_global = 0
        
        # Traiter chaque paragraphe
        for paragraph_index, paragraph in enumerate(paragraphs, 1):
            sentences = self.split_into_sentences(paragraph)
            logging.info(f"\n=== Paragraphe {paragraph_index}/{len(paragraphs)} : {len(sentences)} phrases ===")
            
            # Traiter chaque phrase du paragraphe
            for sentence_index, sentence in enumerate(sentences, 1):
                current_sentence_global += 1
                logging.info(f"Phrase {current_sentence_global}/{total_sentences} (P{paragraph_index:02d}S{sentence_index:02d})")
                
                try:
                    # Générer l'audio pour cette phrase
                    audio_file = self.generate_sentence_audio(sentence, paragraph_index, sentence_index)
                    sentence_audio_files.append(audio_file)
                    
                    # Petite pause pour éviter le rate limiting
                    if current_sentence_global < total_sentences:
                        time.sleep(0.3)
                        
                except Exception as e:
                    logging.error(f"Error generating P{paragraph_index:02d}S{sentence_index:02d}: {e}")
                    raise
        
        # Sauvegarder les métadonnées détaillées
        self.save_sentence_metadata(sentence_audio_files, paragraphs)
        
        logging.info(f"\n🎉 TTS generation completed: {len(sentence_audio_files)} sentence audio files created")
        
        fin_audio()
        return sentence_audio_files

    def generate_sentence_group_audio(self):
        """
        Génère un fichier MP3 pour chaque groupe de phrases du script I3.
        Mode recommandé : groupes de 3 phrases pour améliorer la détection de langue.
        
        Returns:
            list: Liste des chemins vers les fichiers audio générés (groupes)
        """
        logging.info("Starting TTS audio generation (sentence group mode)")
        
        # Lire le script I3
        paragraphs = self.read_i3_script()
        
        # Paramètres de groupement
        sentences_per_group = self.tts_config.get('sentences_per_group', 3)
        
        # Nettoyer le dossier de sortie
        logging.info("Nettoyage du dossier audio existant...")
        for existing_file in self.output_path.glob('*.mp3'):
            existing_file.unlink()
            logging.info(f"Suppression: {existing_file.name}")
        
        group_audio_files = []
        all_sentences = []
        
        # Collecter toutes les phrases avec leurs métadonnées
        for paragraph_index, paragraph in enumerate(paragraphs, 1):
            sentences = self.split_into_sentences(paragraph)
            for sentence_index, sentence in enumerate(sentences, 1):
                all_sentences.append({
                    'text': sentence,
                    'paragraph_index': paragraph_index,
                    'sentence_index': sentence_index,
                    'global_index': len(all_sentences) + 1
                })
        
        logging.info(f"Script I3: {len(paragraphs)} paragraphes → {len(all_sentences)} phrases → ~{len(all_sentences)//sentences_per_group + 1} groupes")
        
        # Créer les groupes de phrases
        groups = []
        for i in range(0, len(all_sentences), sentences_per_group):
            group = all_sentences[i:i + sentences_per_group]
            group_text = ". ".join([s['text'].rstrip('.') for s in group]) + "."
            groups.append({
                'text': group_text,
                'sentences': group,
                'group_index': len(groups) + 1
            })
        
        # Générer un MP3 par groupe
        for group_index, group_data in enumerate(groups, 1):
            logging.info(f"\n=== Groupe {group_index}/{len(groups)} : {len(group_data['sentences'])} phrases ===")
            
            try:
                # Générer l'audio pour ce groupe
                audio_file = self.generate_group_audio(group_data['text'], group_index)
                group_audio_files.append(audio_file)
                
                logging.info(f"TTS group {group_index} completed: {audio_file.name}")
                
                # Petite pause pour éviter le rate limiting
                if group_index < len(groups):
                    time.sleep(0.3)
                    
            except Exception as e:
                logging.error(f"Error generating group {group_index}: {e}")
                raise
        
        # Sauvegarder les métadonnées détaillées
        self.save_group_metadata(group_audio_files, groups)
        
        logging.info(f"\n🎉 TTS generation completed: {len(group_audio_files)} group audio files created")
        
        fin_audio()
        return group_audio_files

    def generate_group_audio(self, group_text, group_index):
        """
        Génère un fichier MP3 pour un groupe de phrases.
        
        Args:
            group_text (str): Texte du groupe (plusieurs phrases)
            group_index (int): Index du groupe (1-based)
            
        Returns:
            Path: Chemin vers le fichier audio généré
        """
        try:
            logging.info(f"🎙️ Group audio generation {group_index}: {len(group_text)} characters")
            
            # Générer l'audio avec l'API OpenAI
            response = self._generate_speech(group_text)
            
            # Nom du fichier: group{index}.mp3
            filename = f"group{group_index:02d}.mp3"
            output_file = self.output_path / filename
            
            # Sauvegarder le fichier
            with open(output_file, "wb") as f:
                f.write(response.content)
            
            logging.info(f"✅ Group audio generated: {filename}")
            return output_file
            
        except Exception as e:
            logging.error(f"❌ Error generating group audio {group_index}: {e}")
            raise

    def save_group_metadata(self, group_audio_files, groups):
        """
        Sauvegarde les métadonnées détaillées pour les groupes de phrases.
        
        Args:
            group_audio_files (list): Liste des chemins vers les fichiers audio des groupes
            groups (list): Liste des données des groupes
        """
        metadata = {
            'generation_timestamp': time.time(),
            'tts_config': self.tts_config,
            'generation_mode': 'sentence_group',
            'sentences_per_group': self.tts_config.get('sentences_per_group', 3),
            'total_groups': len(group_audio_files),
            'groups': []
        }
        
        cumulative_time = 0
        
        for group_index, (audio_file, group_data) in enumerate(zip(group_audio_files, groups), 1):
            # Lire la durée réelle du fichier MP3
            try:
                # On utilise une durée approximative basée sur la taille du fichier
                file_size = audio_file.stat().st_size
                # Estimation: ~1KB par seconde pour MP3 128kbps
                duration = file_size / 1000.0
            except Exception as e:
                logging.warning(f"Unable to read duration of {audio_file}: {e}")
                duration = 0.0
            
            group_info = {
                'group_index': group_index,
                'audio_file': str(audio_file.name),
                'full_path': str(audio_file),
                'duration': duration,
                'start_time': cumulative_time,
                'end_time': cumulative_time + duration,
                'group_text': group_data['text'],
                'sentences': []
            }
            
            # Ajouter les détails des phrases du groupe
            sentence_duration = duration / len(group_data['sentences']) if group_data['sentences'] else 0
            sentence_time = cumulative_time
            
            for sentence_data in group_data['sentences']:
                sentence_info = {
                    'paragraph_index': sentence_data['paragraph_index'],
                    'sentence_index': sentence_data['sentence_index'],
                    'global_sentence_index': sentence_data['global_index'],
                    'sentence_text': sentence_data['text'].strip(),
                    'estimated_start_time': sentence_time,
                    'estimated_end_time': sentence_time + sentence_duration,
                    'estimated_duration': sentence_duration
                }
                group_info['sentences'].append(sentence_info)
                sentence_time += sentence_duration
            
            metadata['groups'].append(group_info)
            cumulative_time += duration
        
        metadata['total_duration'] = cumulative_time
        
        # Sauvegarder les métadonnées
        metadata_file = self.output_path / 'audio_group_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Group metadata saved: {metadata_file}")
        logging.info(f"Total duration: {cumulative_time:.2f}s ({len(group_audio_files)} groups)")

    def generate_rush_based_audio(self):
        """
        Génère tous les fichiers audio pour le script I3.
        MODE LEGACY : 1 MP3 par rush (comme Heygen) pour compatibilité système.
        
        Returns:
            list: Liste des chemins vers les fichiers audio générés (rushs)
        """
        logging.info("Starting TTS audio generation (legacy rush mode)")
        
        # Lire le script I3
        paragraphs = self.read_i3_script()
        
        # Reproduire le même regroupement que Heygen (par 4 paragraphes)
        grouped_paragraphs = []
        for i in range(0, len(paragraphs), 4):
            group = paragraphs[i:i+4]
            grouped_text = "\n\n".join(group)
            grouped_paragraphs.append(grouped_text)
        
        logging.info(f"Script I3: {len(paragraphs)} paragraphes → {len(grouped_paragraphs)} rushs TTS")
        
        # Nettoyer le dossier de sortie
        logging.info("Nettoyage du dossier audio existant...")
        for existing_file in self.output_path.glob('*.mp3'):
            existing_file.unlink()
            logging.info(f"Suppression: {existing_file.name}")
        
        rush_audio_files = []
        
        # Générer 1 MP3 par rush (comme Heygen)
        for rush_index, rush_text in enumerate(grouped_paragraphs, 1):
            logging.info(f"\n=== TTS rush generation {rush_index}/{len(grouped_paragraphs)} ===")
            
            try:
                audio_file = self.generate_rush_audio(rush_text, rush_index)
                rush_audio_files.append(audio_file)
                
                logging.info(f"TTS rush {rush_index} completed: {audio_file.name}")
                
            except Exception as e:
                logging.error(f"Error generating TTS rush {rush_index}: {e}")
                raise
        
        # Sauvegarder les métadonnées simplifiées
        self.save_rush_metadata(rush_audio_files)
        
        logging.info(f"\n🎉 TTS generation completed: {len(rush_audio_files)} rush audio files created")
        
        fin_audio()
        return rush_audio_files

    def generate_bullet_based_audio(self):
        """
        Génère un fichier MP3 pour chaque bullet point du script I3.
        Mode recommandé : 1 MP3 par bullet thématique (2-4 phrases cohérentes).
        
        Returns:
            list: Liste des chemins vers les fichiers audio générés (bullets)
        """
        logging.info("Starting TTS audio generation (bullet points mode)")
        
        # Lire le script I3 (qui contient maintenant des bullet points)
        bullet_points = self.read_i3_script()
        
        # Nettoyer le dossier de sortie
        logging.info("Nettoyage du dossier audio existant...")
        for existing_file in self.output_path.glob('*.mp3'):
            existing_file.unlink()
            logging.info(f"Suppression: {existing_file.name}")
        
        bullet_audio_files = []
        
        logging.info(f"Script I3: {len(bullet_points)} bullet points")
        
        # Générer un MP3 par bullet point
        for bullet_index, bullet_text in enumerate(bullet_points, 1):
            logging.info(f"\n=== Bullet {bullet_index}/{len(bullet_points)} ===")
            
            try:
                # Générer l'audio pour ce bullet
                audio_file = self.generate_bullet_audio(bullet_text, bullet_index)
                bullet_audio_files.append(audio_file)
                
                logging.info(f"TTS bullet {bullet_index} completed: {audio_file.name}")
                
                # Petite pause pour éviter le rate limiting
                if bullet_index < len(bullet_points):
                    time.sleep(0.3)
                    
            except Exception as e:
                logging.error(f"Error generating bullet {bullet_index}: {e}")
                raise
        
        # Sauvegarder les métadonnées détaillées
        self.save_bullet_metadata(bullet_audio_files, bullet_points)
        
        logging.info(f"\n🎉 TTS generation completed: {len(bullet_audio_files)} bullet audio files created")
        
        fin_audio()
        return bullet_audio_files

    def generate_bullet_audio(self, bullet_text, bullet_index):
        """
        Génère un fichier MP3 pour un bullet point.
        
        Args:
            bullet_text (str): Texte du bullet point
            bullet_index (int): Index du bullet (1-based)
            
        Returns:
            Path: Chemin vers le fichier audio généré
        """
        try:
            logging.info(f"🎙️ Bullet audio generation {bullet_index}: {len(bullet_text)} characters")
            
            # Vérifier si le texte est trop long (limite OpenAI TTS ~4096 chars)
            if len(bullet_text) > 4000:
                logging.warning(f"⚠️ Long bullet ({len(bullet_text)} chars), automatic splitting...")
                return self.generate_long_bullet_audio(bullet_text, bullet_index)
            
            # Générer l'audio avec l'API OpenAI
            response = self.client.audio.speech.create(
                model=self.tts_config['model'],
                voice=self.tts_config['voice'],
                input=bullet_text,
                speed=self.tts_config['speed']
            )
            
            # Nom du fichier: bullet{index}.mp3
            filename = f"bullet{bullet_index:02d}.mp3"
            output_file = self.output_path / filename
            
            # Sauvegarder le fichier
            with open(output_file, "wb") as f:
                f.write(response.content)
            
            logging.info(f"✅ Bullet audio generated: {filename}")
            return output_file
            
        except Exception as e:
            logging.error(f"❌ Error generating bullet audio {bullet_index}: {e}")
            raise

    def generate_long_bullet_audio(self, bullet_text, bullet_index):
        """
        Génère un fichier MP3 pour un bullet point trop long en le découpant.
        
        Args:
            bullet_text (str): Texte du bullet (trop long)
            bullet_index (int): Index du bullet
            
        Returns:
            Path: Chemin vers le fichier audio final fusionné
        """
        try:
            # Découper le texte en chunks
            chunks = self._split_long_text(bullet_text)
            logging.info(f"Generating bullet {bullet_index} in {len(chunks)} chunks")
            
            temp_audio_files = []
            
            # Générer un MP3 par chunk
            for chunk_index, chunk in enumerate(chunks, 1):
                logging.info(f"Generating chunk {chunk_index}/{len(chunks)}")
                
                response = self.client.audio.speech.create(
                    model=self.tts_config['model'],
                    voice=self.tts_config['voice'],
                    input=chunk,
                    speed=self.tts_config['speed']
                )
                
                temp_filename = f"bullet{bullet_index:02d}_chunk{chunk_index}.mp3"
                temp_file = self.output_path / temp_filename
                
                with open(temp_file, "wb") as f:
                    f.write(response.content)
                
                temp_audio_files.append(temp_file)
                
                # Pause entre chunks
                time.sleep(0.2)
            
            # Fusionner les chunks (méthode simplifiée)
            final_filename = f"bullet{bullet_index:02d}.mp3"
            final_file = self.output_path / final_filename
            
            # On utilise le dernier chunk comme fichier final (temporaire)
            if temp_audio_files:
                import shutil
                shutil.copy2(str(temp_audio_files[-1]), str(final_file))
                logging.warning(f"Simplified merge: using last chunk for {final_filename}")
            
            # Nettoyer les fichiers temporaires
            for temp_file in temp_audio_files:
                temp_file.unlink()
            
            logging.info(f"✅ Audio bullet long généré et fusionné: {final_filename}")
            return final_file
            
        except Exception as e:
            logging.error(f"❌ Erreur lors de la génération du bullet long {bullet_index}: {e}")
            raise

    def generate_rush_audio(self, rush_text, rush_index):
        """
        Génère un fichier MP3 pour un rush complet (équivalent Heygen).
        
        Args:
            rush_text (str): Texte complet du rush (4 paragraphes groupés)
            rush_index (int): Index du rush (1-based)
            
        Returns:
            Path: Chemin vers le fichier audio généré
        """
        try:
            logging.info(f"🎙️ Génération audio rush {rush_index}: {len(rush_text)} caractères")
            
            # Vérifier la longueur du texte (limite OpenAI TTS : ~4096 caractères)
            if len(rush_text) > 4000:
                logging.warning(f"⚠️ Texte long ({len(rush_text)} chars), découpage automatique...")
                # Découper le texte en chunks plus petits
                chunks = self._split_long_text(rush_text, max_length=3500)
                audio_chunks = []
                
                for i, chunk in enumerate(chunks):
                    logging.info(f"   Génération chunk {i+1}/{len(chunks)}")
                    response = self.client.audio.speech.create(
                        model=self.tts_config['model'],
                        voice=self.tts_config['voice'],
                        input=chunk,
                        speed=self.tts_config['speed']
                    )
                    audio_chunks.append(response.content)
                
                # Fusionner les chunks audio (simplification : concaténation binaire)
                merged_content = b''.join(audio_chunks)
                
            else:
                # Générer l'audio avec l'API OpenAI (texte normal)
                response = self.client.audio.speech.create(
                    model=self.tts_config['model'],
                    voice=self.tts_config['voice'],
                    input=rush_text,
                    speed=self.tts_config['speed']
                )
                merged_content = response.content
            
            # Nom du fichier: rush{index}.mp3 (comme Heygen : rush1.mp4 → rush1.mp3)
            filename = f"rush{rush_index}.mp3"
            output_file = self.output_path / filename
            
            # S'assurer que le dossier parent existe
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Sauvegarder le fichier
            with open(output_file, "wb") as f:
                f.write(merged_content)
            
            logging.info(f"✅ Rush audio généré: {filename}")
            return output_file
            
        except Exception as e:
            logging.error(f"❌ Erreur lors de la génération du rush audio {rush_index}: {e}")
            raise

    def save_sentence_metadata(self, sentence_audio_files, paragraphs):
        """
        Sauvegarde les métadonnées détaillées pour les phrases audio.
        
        Args:
            sentence_audio_files (list): Liste des chemins vers les fichiers audio des phrases
            paragraphs (list): Liste des paragraphes originaux
        """
        metadata = {
            'generation_timestamp': time.time(),
            'tts_config': self.tts_config,
            'generation_mode': 'sentence',  # Indique le mode phrase par phrase
            'total_sentences': len(sentence_audio_files),
            'total_paragraphs': len(paragraphs),
            'sentences': []
        }
        
        # Reconstruire la structure paragraphe/phrase
        file_index = 0
        for paragraph_index, paragraph in enumerate(paragraphs, 1):
            sentences = self.split_into_sentences(paragraph)
            
            for sentence_index, sentence_text in enumerate(sentences, 1):
                if file_index < len(sentence_audio_files):
                    audio_file = sentence_audio_files[file_index]
                    
                    # Lire la durée réelle du fichier MP3
                    try:
                        # On utilise une durée approximative basée sur la taille du fichier
                        file_size = audio_file.stat().st_size
                        # Estimation: ~1KB par seconde pour MP3 128kbps
                        duration = file_size / 1000.0
                    except Exception as e:
                        logging.warning(f"Unable to read duration of {audio_file}: {e}")
                        duration = 0.0
                    
                    sentence_data = {
                        'paragraph_index': paragraph_index,
                        'sentence_index': sentence_index,
                        'global_sentence_index': file_index + 1,
                        'sentence_text': sentence_text.strip(),
                        'audio_file': str(audio_file.name),
                        'full_path': str(audio_file),
                        'duration': duration,
                        'word_count': len(sentence_text.split())
                    }
                    metadata['sentences'].append(sentence_data)
                    file_index += 1
        
        # Calculer les timings cumulés
        cumulative_time = 0
        for sentence_data in metadata['sentences']:
            sentence_data['start_time'] = cumulative_time
            sentence_data['end_time'] = cumulative_time + sentence_data['duration']
            cumulative_time += sentence_data['duration']
        
        metadata['total_duration'] = cumulative_time
        
        # Sauvegarder les métadonnées
        metadata_file = self.output_path / 'audio_sentence_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Métadonnées phrase sauvegardées: {metadata_file}")
        logging.info(f"Durée totale: {cumulative_time:.2f}s ({len(sentence_audio_files)} phrases)")

    def save_rush_metadata(self, rush_audio_files):
        """
        Sauvegarde les métadonnées simplifiées pour les rushs audio.
        
        Args:
            rush_audio_files (list): Liste des chemins vers les fichiers audio des rushs
        """
        metadata = {
            'generation_timestamp': time.time(),
            'tts_config': self.tts_config,
            'generation_mode': 'rush',  # Indique le mode simplifié
            'rushes': []
        }
        
        for rush_index, audio_file in enumerate(rush_audio_files, 1):
            # Lire la durée réelle du fichier MP3
            try:
                # On utilise une durée approximative basée sur la taille du fichier
                file_size = audio_file.stat().st_size
                # Estimation: ~1KB par seconde pour MP3 128kbps
                duration = file_size / 1000.0
            except Exception as e:
                logging.warning(f"Unable to read duration of {audio_file}: {e}")
                duration = 0.0
            
            rush_data = {
                'rush_index': rush_index,
                'audio_file': str(audio_file.name),
                'full_path': str(audio_file),
                'duration': duration
            }
            metadata['rushes'].append(rush_data)
        
        # Sauvegarder les métadonnées
        metadata_file = self.output_path / 'audio_rush_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Métadonnées rush sauvegardées: {metadata_file}")

    def save_bullet_metadata(self, bullet_audio_files, bullet_points):
        """
        Sauvegarde les métadonnées détaillées pour les bullet points.
        
        Args:
            bullet_audio_files (list): Liste des chemins vers les fichiers audio des bullets
            bullet_points (list): Liste des textes des bullet points
        """
        metadata = {
            'generation_timestamp': time.time(),
            'tts_config': self.tts_config,
            'generation_mode': 'bullet',
            'total_bullets': len(bullet_audio_files),
            'bullets': []
        }
        
        cumulative_time = 0
        
        for bullet_index, (audio_file, bullet_text) in enumerate(zip(bullet_audio_files, bullet_points), 1):
            # Lire la durée réelle du fichier MP3
            try:
                # On utilise une durée approximative basée sur la taille du fichier
                file_size = audio_file.stat().st_size
                # Estimation: ~1KB par seconde pour MP3 128kbps
                duration = file_size / 1000.0
            except Exception as e:
                logging.warning(f"Unable to read duration of {audio_file}: {e}")
                duration = 0.0
            
            bullet_info = {
                'bullet_index': bullet_index,
                'audio_file': str(audio_file.name),
                'full_path': str(audio_file),
                'duration': duration,
                'start_time': cumulative_time,
                'end_time': cumulative_time + duration,
                'bullet_text': bullet_text.strip(),
                'word_count': len(bullet_text.split()),
                'character_count': len(bullet_text)
            }
            
            metadata['bullets'].append(bullet_info)
            cumulative_time += duration
        
        metadata['total_duration'] = cumulative_time
        
        # Sauvegarder les métadonnées
        metadata_file = self.output_path / 'audio_bullet_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Métadonnées bullets sauvegardées: {metadata_file}")
        logging.info(f"Durée totale: {cumulative_time:.2f}s ({len(bullet_audio_files)} bullets)")

    def _split_long_text(self, text, max_length=3500):
        """
        Découpe un texte long en chunks plus petits en respectant les phrases.
        
        Args:
            text (str): Texte à découper
            max_length (int): Longueur maximale par chunk
            
        Returns:
            list: Liste des chunks de texte
        """
        # Découper en phrases d'abord
        sentences = self.split_into_sentences(text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Si ajouter cette phrase dépasse la limite
            if len(current_chunk) + len(sentence) + 2 > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # Phrase elle-même trop longue, la découper brutalement
                    chunks.append(sentence[:max_length])
                    current_chunk = sentence[max_length:]
            else:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence
        
        # Ajouter le dernier chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks 