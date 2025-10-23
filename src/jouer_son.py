#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module simple pour jouer les sons d'interface.
"""

import subprocess
from pathlib import Path


def jouer_son(nom_son):
    """
    Joue un son d'interface.

    Args:
        nom_son (str): Nom du son ('script', 'audio', 'vector_broll', 'premontage', 'montage')
    """
    sounds_dir = Path("sons-interface")

    mapping = {
        "script": "fin_script.mp3",
        "audio": "fin_audio.mp3",
        "vector_broll": "fin_vector_broll.mp3",
        "premontage": "lancement_premontage.mp3",
        "montage": "fin_montage.mp3",
    }

    if nom_son not in mapping:
        print(f"❌ Son '{nom_son}' non reconnu. Options: {list(mapping.keys())}")
        return False

    filename = mapping[nom_son]
    filepath = sounds_dir / filename

    if not filepath.exists():
        print(f"❌ Fichier son non trouvé: {filepath}")
        return False

    try:
        subprocess.run(["afplay", str(filepath)], check=True)
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la lecture: {e}")
        return False


def fin_script():
    """Joue le son de fin d'étape script"""
    return jouer_son("script")


def fin_audio():
    """Joue le son de fin d'étape audio"""
    return jouer_son("audio")


def fin_vector_broll():
    """Joue le son de fin d'étape vector b-roll"""
    return jouer_son("vector_broll")


def lancement_premontage():
    """Joue le son de lancement de l'étape premontage"""
    return jouer_son("premontage")


def fin_montage():
    """Joue le son de fin d'étape montage vidéo"""
    return jouer_son("montage")


if __name__ == "__main__":
    print("🔊 Test de tous les sons d'interface...")

    sons = [
        ("script", "Fin de l'étape SCRIPT"),
        ("audio", "Fin de l'étape AUDIO"),
        ("vector_broll", "Fin de l'étape VECTOR B ROLL"),
        ("premontage", "Lancement de l'étape PREMONTAGE"),
        ("montage", "Fin de l'étape montage vidéo"),
    ]

    for nom, description in sons:
        print(f"\n🎵 {description}...")
        if jouer_son(nom):
            print("✅ Son joué avec succès")
        else:
            print("❌ Échec de la lecture")
