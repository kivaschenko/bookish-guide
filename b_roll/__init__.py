#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
B-roll Intelligence Module

AI-powered B-roll selection system for automated video production.
This module provides intelligent B-roll selection using vector similarity
matching and AI-powered ranking to create professional video content.

Main Components:
- MetaExtractor: Extract metadata from B-roll videos using AI vision
- VectorMatcher: Semantic similarity matching using embeddings
- BRollFinder: Main orchestration engine for B-roll selection
- CLI: Command-line interface for all operations

Usage:
    python -m b_roll.cli --help
"""

from .meta_extractor import MetaExtractor
from .vector_matcher import VectorMatcher
from .broll_finder import BRollFinder, prepare_brolls_vector
from .utils import clean_broll_selections
from . import utils

__version__ = "1.0.0"
__author__ = "StoryForge Team"

__all__ = [
    "MetaExtractor",
    "VectorMatcher",
    "BRollFinder",
    "prepare_brolls_vector",
    "clean_broll_selections",
    "utils",
]
