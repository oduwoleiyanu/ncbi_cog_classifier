"""
Setup script for NCBI COG Classifier.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read version from __init__.py
version = "1.0.0"
init_file = Path(__file__).parent / "cog_classifier" / "__init__.py"
if init_file.exists():
    for line in init_file.read_text().splitlines():
        if line.startswith("__version__"):
            version = line.split('"')[1]
            break

setup(
    name="ncbi-cog-classifier",
    version=version,
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python tool for classifying protein sequences using the NCBI COG database",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ncbi_cog_classifier",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "urllib3>=1.26.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cog-classifier=cog_classifier.__main__:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="bioinformatics, protein, classification, COG, NCBI, BLAST",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/ncbi_cog_classifier/issues",
        "Source": "https://github.com/yourusername/ncbi_cog_classifier",
        "Documentation": "https://ncbi-cog-classifier.readthedocs.io/",
    },
)
