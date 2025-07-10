"""
NCBI COG Classifier

A Python tool for classifying protein sequences using the NCBI COG database.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .classifier import COGClassifier
from .database import COGDatabase
from .parser import FastaParser, COGParser
from .reporter import COGReporter

__all__ = [
    "COGClassifier",
    "COGDatabase", 
    "FastaParser",
    "COGParser",
    "COGReporter"
]
