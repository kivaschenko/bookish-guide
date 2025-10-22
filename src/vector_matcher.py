import os
import glob
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re
import requests

class VectorMatcher:
    """
    Classe pour la recherche de b-rolls par similarité sémantique (embeddings).
    Utilise SentenceTransformer pour encoder les descriptions des b-rolls et les phrases à illustrer.
    """
    def __init__(self, config=None, broll_folder="b-roll", embeddings_file="broll_vector_embeddings.json", model_name="all-mpnet-base-v2"):
        self.broll_folder = broll_folder
        self.embeddings_file = embeddings_file
        self.model_name = model_name
        self.model = SentenceTransformer(self.model_name)
        
        # Récupérer la clé API et le modèle depuis la config (comme dans b_roll_finder)
        if config and 'api' in config and 'openai' in config['api'] and 'api_key' in config['api']['openai']:
            self.api_key = config['api']['openai']['api_key']
            self.openai_model = config['api']['openai']['model']
        else:
            # Pas de fallback - config obligatoire
            raise ValueError("vector_matcher.py: Configuration OpenAI manquante dans config.yml (api.openai.api_key et api.openai.model)")
        
        self.brolls = self.load_broll_descriptions()
        self.brolls = self.compute_or_load_embeddings()

    def load_broll_descriptions(self):
        """
        Charge les descriptions des b-rolls à partir des fichiers .txt du dossier b-roll.
        Retourne une liste de dicts : {filename, description}
        """
        brolls = []
        for filepath in glob.glob(os.path.join(self.broll_folder, "*.txt")):
            with open(filepath, "r", encoding="utf-8") as f:
                description = f.read().strip()
                
                # Détecter l'extension vidéo réelle (.mp4 ou .mov)
                base_name = os.path.basename(filepath).replace(".txt", "")
                video_file = None
                
                # Chercher d'abord .mp4, puis .mov
                for ext in [".mp4", ".mov"]:
                    potential_path = os.path.join(self.broll_folder, base_name + ext)
                    if os.path.exists(potential_path):
                        video_file = base_name + ext
                        break
                
                if video_file:
                    brolls.append({
                        "filename": video_file,
                        "description": description
                    })
                else:
                    # Fallback: utiliser .mp4 par défaut (comportement original)
                    brolls.append({
                        "filename": base_name + ".mp4",
                        "description": description
                    })
        return brolls

    def compute_or_load_embeddings(self):
        """
        Calcule ou charge les embeddings des descriptions de b-rolls.
        Ajoute la clé 'embedding' à chaque b-roll.
        """
        if os.path.exists(self.embeddings_file):
            with open(self.embeddings_file, "r", encoding="utf-8") as f:
                brolls = json.load(f)
            # Vérifier que tous les fichiers sont présents
            broll_filenames = set(b["filename"] for b in self.brolls)
            loaded_filenames = set(b["filename"] for b in brolls)
            if broll_filenames == loaded_filenames:
                return brolls
            # Sinon, recalculer (nouveaux fichiers)
        # Calculer les embeddings
        texts = [b["description"] for b in self.brolls]
        vectors = self.model.encode(texts, show_progress_bar=True)
        for i, vec in enumerate(vectors):
            self.brolls[i]["embedding"] = vec.tolist()
        # Sauvegarder
        with open(self.embeddings_file, "w", encoding="utf-8") as f:
            json.dump(self.brolls, f)
        return self.brolls

    def split_paragraph_into_sentences(self, paragraph):
        """
        Découpe un paragraphe en phrases individuelles (regex compatible avec le reste du projet).
        """
        # Regex plus robuste pour capturer les phrases
        sentence_delimiters = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(sentence_delimiters, paragraph)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Debug: afficher les phrases détectées
        print(f"🔍 Phrases détectées ({len(sentences)}):")
        for i, sentence in enumerate(sentences, 1):
            print(f"  {i}. {sentence}")
        
        return sentences

    def analyze_characters_in_rush(self, paragraph_text):
        """
        Analyse tout le texte du rush pour identifier les personnages dans chaque phrase.
        Sauvegarde l'analyse dans temp/character_analysis.json
        Retourne le dictionnaire d'analyse des personnages.
        """
        sentences = self.split_paragraph_into_sentences(paragraph_text)
        
        # Construire le texte numéroté pour l'analyse
        numbered_text = ""
        for i, sentence in enumerate(sentences, 1):
            numbered_text += f"Phrase {i}: {sentence}\n"
        
        prompt = f"""Analyse ce texte phrase par phrase et identifie les personnages mentionnés (il, elle, cette femme, cet homme, etc.).
Pour chaque phrase, donne le genre, âge moyen précis, et ethnicité des personnes concernées.
Si tu ne sais pas ou si aucun personnage n'est mentionné, laisse un array vide pour cette phrase.
IMPORTANT: Si tu ne connais pas l'ethnicité, ne mets pas "inconnue", laisse le champ vide ou omets-le.

{numbered_text}

Réponds en JSON avec cette structure exacte (sois concis) :
{{
  "phrase_1": [{{"genre": "femme", "age": 35, "ethnicite": "caucasienne"}}],
  "phrase_2": [],
  "phrase_3": [{{"genre": "homme", "age": 28}}]
}}"""

        try:
            # Utiliser GPT-5 avec la nouvelle API
            if self.openai_model == 'gpt-5':
                input_text = f"USER: {prompt}"
                response = requests.post(
                    "https://api.openai.com/v1/responses",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
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
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    json={
                        "model": self.openai_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 2000,
                        "response_format": {"type": "json_object"}
                    }
                )
            
            if response.status_code == 200:
                response_json = response.json()
                if self.openai_model == 'gpt-5':
                    # GPT-5 retourne du JSON dans output_text, il faut le parser
                    import json
                    content = json.loads(response_json['output_text'].strip())
                else:
                    content = response_json['choices'][0]['message']['content'].strip()
                
                print(f"🤖 RÉPONSE BRUTE DE GPT-5 pour l'analyse des personnages :")
                print("-" * 60)
                print(content)
                print("-" * 60)
                
                try:
                    # Parser la réponse JSON
                    character_analysis = json.loads(content)
                    
                    # Sauvegarder dans le fichier temporaire
                    os.makedirs("temp", exist_ok=True)
                    with open("temp/character_analysis.json", "w", encoding="utf-8") as f:
                        json.dump(character_analysis, f, ensure_ascii=False, indent=2)
                    
                    print(f"✅ Analyse des personnages sauvegardée dans temp/character_analysis.json")
                    return character_analysis
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Erreur de parsing JSON de l'analyse des personnages: {e}")
                    print(f"Contenu problématique autour de la position {e.pos}:")
                    start = max(0, e.pos - 50)
                    end = min(len(content), e.pos + 50)
                    print(f"'{content[start:end]}'")
                    return {}
            else:
                print(f"Erreur API OpenAI pour l'analyse des personnages: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"Erreur lors de l'analyse des personnages: {e}")
            return {}

    def ask_gpt_to_choose_best_broll(self, sentence, top_brolls_with_scores, previous_sentences=None, characters_info=None):
        """
        Envoie les 10 meilleures options à GPT-4o pour qu'il choisisse le top 3.
        Retourne une liste de 3 index (0-9) selon GPT.
        """
        options_text = ""
        for i, (broll, score) in enumerate(top_brolls_with_scores):
            options_text += f"{i+1}. {broll['filename']}\n   Description: {broll['description']}\n\n"
        
        # Construire le contexte si des phrases précédentes sont fournies
        context_text = ""
        if previous_sentences:
            context_text = f"""Contexte des phrases précédentes :
{' '.join(previous_sentences)}

"""
        
        # Construire les informations sur les personnages
        characters_text = ""
        if characters_info:
            characters_text = "Personnage(s) concerné(s) :\n"
            for char in characters_info:
                characters_text += f"- {char.get('genre', 'inconnu').capitalize()}"
                if char.get('age'):
                    characters_text += f", {char['age']} ans"
                if char.get('ethnicite'):
                    characters_text += f", {char['ethnicite']}"
                characters_text += "\n"
            characters_text += "\n"
        
        prompt = f"""Tu dois choisir les 3 MEILLEURES vidéos b-roll pour illustrer cette phrase :
"{sentence}"

{context_text}{characters_text}Voici les 10 options disponibles :

{options_text}

Privilégie les b-roll positives et politiquement correctes, sauf si c'est parfaitement adapté à la situation, évite la sur-dramatisation et les b-roll sensibles ou négatives (covid, religions, mort, cynisme, violence). 

Réponds UNIQUEMENT les 3 numéros des meilleures vidéos, séparés par des virgules (ex: 2,5,8)."""

        # Log simple du prompt
        with open("log-openai-ask_gpt_to_choose_best_broll.txt", "a", encoding="utf-8") as f:
            f.write(f"\n--- Phrase: {sentence} ---\n{prompt}\n")

        try:
            # Utiliser GPT-5 avec la nouvelle API
            if self.openai_model == 'gpt-5':
                input_text = f"USER: {prompt}"
                response = requests.post(
                    "https://api.openai.com/v1/responses",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    json={
                        "model": "gpt-5",
                        "input": input_text,
                        "reasoning": {"effort": "low"},
                        "text": {"verbosity": "low"}
                    }
                )
            else:
                # Utiliser l'ancienne API pour les autres modèles
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 10,
                    }
                )
            
            if response.status_code == 200:
                response_json = response.json()
                if self.openai_model == 'gpt-5':
                    # GPT-5 retourne du JSON dans output_text, il faut le parser
                    import json
                    content = json.loads(response_json['output_text'].strip())
                else:
                    content = response_json['choices'][0]['message']['content'].strip()
                
                # Logger la réponse aussi
                with open("log-openai-ask_gpt_to_choose_best_broll.txt", "a", encoding="utf-8") as f:
                    f.write(f"RESPONSE: {content}\n")
                
                # Parser la réponse pour extraire le top 3
                try:
                    # Extraire les numéros séparés par des virgules
                    choice_nums = [int(x.strip()) for x in content.split(',')]
                    
                    # Valider que tous les choix sont valides (1-10)
                    valid_choices = []
                    for choice_num in choice_nums:
                        if 1 <= choice_num <= 10:
                            valid_choices.append(choice_num - 1)  # Convertir en index 0-9
                    
                    # S'assurer qu'on a au moins 3 choix valides
                    if len(valid_choices) >= 3:
                        top3_indices = valid_choices[:3]  # Prendre les 3 premiers
                    elif len(valid_choices) > 0:
                        # Compléter avec les premiers choix par score si pas assez
                        top3_indices = valid_choices[:]
                        while len(top3_indices) < 3:
                            for i in range(min(3, len(top_brolls_with_scores))):
                                if i not in top3_indices:
                                    top3_indices.append(i)
                                    break
                            break
                    else:
                        # Utiliser les 3 premiers par défaut
                        top3_indices = [0, 1, 2]
                    
                    # Logger dans le fichier HTML avec le premier choix
                    chosen_broll = top_brolls_with_scores[top3_indices[0]][0]
                    self._log_to_html(prompt, content, chosen_broll['filename'])
                    
                    return top3_indices[:3]  # Retourner exactement 3 index
                    
                except ValueError:
                    print(f"GPT a retourné un format invalide: {content}, utilisation des 3 premiers choix par défaut")
                    return [0, 1, 2]
            else:
                error_msg = f"Erreur API OpenAI: {response.status_code}"
                print(error_msg)
                # Logger l'erreur
                with open("log-openai-ask_gpt_to_choose_best_broll.txt", "a", encoding="utf-8") as f:
                    f.write(f"ERROR: {error_msg}\n")
                    f.write(f"ERROR_RESPONSE: {response.text}\n")
                return [0, 1, 2]
                
        except Exception as e:
            error_msg = f"Erreur lors de l'appel à GPT: {e}"
            print(error_msg)
            # Logger l'erreur
            with open("log-openai-ask_gpt_to_choose_best_broll.txt", "a", encoding="utf-8") as f:
                f.write(f"EXCEPTION: {error_msg}\n")
            return [0, 1, 2]

    def _log_to_html(self, prompt, response, broll_filename):
        """
        Ajoute une entrée au log HTML avec prompt, réponse et image de la b-roll
        """
        import os
        html_file = "log-openai-ask_gpt_to_choose_best_broll.html"
        
        # Extraire la phrase du prompt (première ligne après "Tu dois trier...")
        phrase = ""
        lines = prompt.split('\n')
        for line in lines:
            if line.startswith('"') and line.endswith('"'):
                phrase = line.strip('"')
                break
        
        # Chercher l'image correspondante (jpg ou png)
        broll_name = broll_filename.replace('.mp4', '')
        image_path = None
        for ext in ['.jpg', '.png']:
            potential_path = os.path.join(self.broll_folder, broll_name + ext)
            if os.path.exists(potential_path):
                image_path = potential_path
                break
        
        # Échapper le HTML dans le prompt
        import html
        prompt_escaped = html.escape(prompt).replace('\n', '<br>')
        
        # Créer une carte simple
        image_tag = f'<img src="{image_path}" style="max-width:300px; max-height:200px; border-radius:8px;">' if image_path else 'Image non trouvée'
        
        card = f"""
    <div style="border:1px solid #ddd; margin:20px 0; padding:15px; border-radius:8px; background-color:#f9f9f9;">
        <h3 style="margin-top:0; color:#333;">"{phrase}"</h3>
        <div style="text-align:center; margin:15px 0;">
            {image_tag}
            <p style="margin:5px 0; font-size:14px; color:#666;"><strong>Choix GPT:</strong> {response} | <strong>Fichier:</strong> {broll_filename}</p>
        </div>
        <details style="margin-top:15px;">
            <summary style="cursor:pointer; color:#0066cc;">Voir le prompt complet</summary>
            <div style="margin-top:10px; padding:10px; background-color:#fff; border:1px solid #eee; font-size:12px; max-height:200px; overflow-y:auto;">
                {prompt_escaped}
            </div>
        </details>
    </div>"""
        
        # Si le fichier n'existe pas, créer l'en-tête HTML
        if not os.path.exists(html_file):
            with open(html_file, "w", encoding="utf-8") as f:
                f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Log GPT B-roll Selection</title>
    <meta charset="UTF-8">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; max-width: 800px; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>🎬 Log des sélections de B-roll par GPT-4o</h1>
""")
                f.flush()  # Forcer l'écriture immédiate
        
        # Ajouter la carte au fichier existant
        with open(html_file, "a", encoding="utf-8") as f:
            f.write(card)
            f.flush()  # Forcer l'écriture immédiate

    def select_brolls_for_rush(self, paragraph_text, used_brolls_global_set=None):
        """
        Pour chaque phrase du rush, sélectionne la b-roll la plus pertinente (non déjà utilisée globalement).
        Analyse d'abord les personnages du rush, puis affiche le top 5 des b-rolls candidates, 
        demande à GPT-4o de choisir avec contexte et infos personnages, puis attend une validation utilisateur.
        Retourne un dict {phrase_id: filename}
        """
        if used_brolls_global_set is None:
            used_brolls_global_set = set()
        
        # Analyser les personnages dans tout le rush
        # print("🔍 Analyse des personnages dans le rush...")
        # character_analysis = self.analyze_characters_in_rush(paragraph_text)
        
        sentences = self.split_paragraph_into_sentences(paragraph_text)
        selections = {}
        used_brolls_local = set()
        for i, sentence in enumerate(sentences):
            # Exclure les b-rolls déjà utilisées (global + local)
            available_brolls = [b for b in self.brolls if b["filename"] not in used_brolls_global_set and b["filename"] not in used_brolls_local]
            if not available_brolls:
                break
            # Encoder la phrase avec contexte de la phrase précédente
            query_text = sentence if i == 0 else f"{sentences[i-1]} {sentence}"
            query_vec = self.model.encode([query_text])[0]
            broll_embeddings = np.array([b["embedding"] for b in available_brolls])
            similarities = cosine_similarity([query_vec], broll_embeddings)[0]
            # Top 10
            top_indices = similarities.argsort()[-10:][::-1]
            top_brolls_with_scores = [(available_brolls[idx], similarities[idx]) for idx in top_indices]
            
            print("\n--- Phrase {} : {}".format(i+1, sentence))
            print("Top 10 b-rolls candidates :")
            for rank, (b, score) in enumerate(top_brolls_with_scores, 1):
                print(f"{rank}. {b['filename']} | Score: {score:.4f}\n   → {b['description'][:120]}{'...' if len(b['description'])>120 else ''}")
            
            # Préparer le contexte des 2 phrases précédentes
            previous_sentences = []
            if i > 0:  # Au moins une phrase précédente
                previous_sentences.append(sentences[i-1])
            if i > 1:  # Au moins deux phrases précédentes
                previous_sentences.insert(0, sentences[i-2])  # Insérer au début pour garder l'ordre chronologique
            
            # Récupérer les infos sur les personnages pour cette phrase
            # phrase_key = f"phrase_{i+1}"
            # characters_info = character_analysis.get(phrase_key, [])
            
            # Demander à GPT de choisir avec contexte et infos personnages
            print("\n🤖 GPT-4o analyse les options...")
            gpt_choice_indices = self.ask_gpt_to_choose_best_broll(
                sentence, 
                top_brolls_with_scores, 
                previous_sentences if previous_sentences else None,
                None  # characters_info if characters_info else None
            )
            
            # Récupérer les 3 b-rolls choisies par GPT
            chosen_brolls = []
            for idx in gpt_choice_indices:
                if idx < len(top_brolls_with_scores):
                    chosen_brolls.append(top_brolls_with_scores[idx][0])
            
            # Afficher les choix
            for j, broll in enumerate(chosen_brolls):
                if j == 0:
                    print(f"✅ GPT-4o a choisi (broll) : {broll['filename']} (option {gpt_choice_indices[j] + 1})")
                    print(f"📄 Description : {broll['description'][:150]}{'...' if len(broll['description'])>150 else ''}")
                elif j == 1:
                    print(f"🔄 B-roll 2 : {broll['filename']} (option {gpt_choice_indices[j] + 1})")
                    print(f"📄 Description broll2 : {broll['description'][:150]}{'...' if len(broll['description'])>150 else ''}")
                elif j == 2:
                    print(f"🔄 B-roll 3 : {broll['filename']} (option {gpt_choice_indices[j] + 1})")
                    print(f"📄 Description broll3 : {broll['description'][:150]}{'...' if len(broll['description'])>150 else ''}")
            
            # Stocker les 3 b-rolls dans le JSON
            selections[str(i+1)] = {
                "broll": chosen_brolls[0]["filename"] if len(chosen_brolls) > 0 else None,
                "broll2": chosen_brolls[1]["filename"] if len(chosen_brolls) > 1 else None,
                "broll3": chosen_brolls[2]["filename"] if len(chosen_brolls) > 2 else None
            }
            used_brolls_local.add(chosen_brolls[0]["filename"])
        return selections 