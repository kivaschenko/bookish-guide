#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module utilitaire contenant les fonctions de configuration communes.
"""

import logging
import sys

def setup_logging():
    """
    Configure le système de logging avec un format détaillé
    et un niveau WARNING.
    """
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

    # Définir notre logger au niveau INFO pour avoir plus de détails
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # S'assurer que les logs sont bien envoyés vers stdout
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logging.info("Logging configuré avec succès")