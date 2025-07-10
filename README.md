# NCBI COG Classifier

A Python tool for classifying protein sequences using the NCBI COG (Clusters of Orthologous Groups) database.

## Overview

The COG database is a phylogenetic classification of proteins encoded in complete genomes. This tool allows you to:
- Download and process NCBI COG database files
- Classify protein sequences against COG categories
- Generate functional annotations and reports
- Export results in multiple formats

## Features

- **Automated Database Download**: Fetches the latest NCBI COG database
- **BLAST-based Classification**: Uses BLAST for sequence similarity searches
- **Multiple Output Formats**: JSON, CSV, and TSV output options
- **Batch Processing**: Handle multiple sequences efficiently
- **Detailed Reports**: Generate comprehensive classification reports
- **Command Line Interface**: Easy-to-use CLI for all operations

## Installation

### Prerequisites
- Python 3.8+
- BLAST+ (for sequence alignment)

### Install BLAST+
```bash
# On macOS with Homebrew
brew install blast

# On Ubuntu/Debian
sudo apt-get install ncbi-blast+

# On CentOS/RHEL
sudo yum install ncbi-blast+
```

### Install COG Classifier
```bash
# Clone the repository
git clone https://github.com/oduwoleiyanu/ncbi_cog_classifier.git
cd ncbi_cog_classifier

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

## Quick Start

### 1. Download COG Database
```bash
python -m cog_classifier download
```

### 2. Classify a single protein sequence
```bash
python -m cog_classifier classify --input protein.fasta --output results.json
```

### 3. Batch classify multiple sequences
```bash
python -m cog_classifier classify --input proteins_batch.fasta --output batch_results.csv --format csv
```

## Usage

### Command Line Interface

#### Download COG Database
```bash
python -m cog_classifier download [--data-dir DATA_DIR] [--force]
```

#### Classify Sequences
```bash
python -m cog_classifier classify \
    --input INPUT_FILE \
    --output OUTPUT_FILE \
    [--format {json,csv,tsv}] \
    [--evalue EVALUE] \
    [--max-targets MAX_TARGETS] \
    [--threads THREADS]
```

#### Generate Report
```bash
python -m cog_classifier report \
    --input CLASSIFICATION_RESULTS \
    --output REPORT_FILE \
    [--format {html,pdf,txt}]
```

### Python API

```python
from cog_classifier import COGClassifier

# Initialize classifier
classifier = COGClassifier()

# Download database (if not already present)
classifier.download_database()

# Classify a single sequence
result = classifier.classify_sequence("MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQTLGQHDFSAGEGLYTHMKALRPDEDRLSLEVGN")

# Classify sequences from FASTA file
results = classifier.classify_fasta("proteins.fasta")

# Generate report
classifier.generate_report(results, "classification_report.html")
```

## Output Format

### JSON Output
```json
{
  "sequence_id": "protein_001",
  "length": 245,
  "best_hit": {
    "cog_id": "COG0001",
    "cog_name": "Glutamate-1-semialdehyde 2,1-aminomutase",
    "category": "E",
    "category_name": "Amino acid transport and metabolism",
    "evalue": 1e-50,
    "bit_score": 185.2,
    "identity": 85.5,
    "coverage": 92.3
  },
  "all_hits": [...]
}
```

### CSV Output
```csv
sequence_id,length,cog_id,cog_name,category,category_name,evalue,bit_score,identity,coverage
protein_001,245,COG0001,Glutamate-1-semialdehyde 2,1-aminomutase,E,Amino acid transport and metabolism,1e-50,185.2,85.5,92.3
```

## COG Categories

| Code | Category |
|------|----------|
| A | RNA processing and modification |
| B | Chromatin structure and dynamics |
| C | Energy production and conversion |
| D | Cell cycle control and mitosis |
| E | Amino acid transport and metabolism |
| F | Nucleotide transport and metabolism |
| G | Carbohydrate transport and metabolism |
| H | Coenzyme transport and metabolism |
| I | Lipid transport and metabolism |
| J | Translation |
| K | Transcription |
| L | Replication, recombination and repair |
| M | Cell wall/membrane biogenesis |
| N | Cell motility |
| O | Posttranslational modification, protein turnover, chaperones |
| P | Inorganic ion transport and metabolism |
| Q | Secondary metabolites biosynthesis, transport and catabolism |
| R | General function prediction only |
| S | Function unknown |
| T | Signal transduction mechanisms |
| U | Intracellular trafficking and secretion |
| V | Defense mechanisms |
| W | Extracellular structures |
| Y | Nuclear structure |
| Z | Cytoskeleton |

## Configuration

Create a `config.yaml` file to customize settings:

```yaml
database:
  data_dir: "./data"
  cog_url: "https://ftp.ncbi.nlm.nih.gov/pub/COG/COG2020/data/"
  
blast:
  evalue: 1e-5
  max_targets: 10
  threads: 4
  
output:
  default_format: "json"
  include_all_hits: true
```

## Development

### Setup Development Environment
```bash
git clone https://github.com/oduwoleiyanu/ncbi_cog_classifier.git
cd ncbi_cog_classifier

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8 cog_classifier/
black cog_classifier/
```

### Project Structure
```
ncbi_cog_classifier/
├── cog_classifier/
│   ├── __init__.py
│   ├── __main__.py
│   ├── classifier.py
│   ├── database.py
│   ├── parser.py
│   ├── reporter.py
│   └── utils.py
├── tests/
│   ├── test_classifier.py
│   ├── test_database.py
│   └── test_parser.py
├── data/
├── examples/
├── docs/
├── requirements.txt
├── setup.py
├── pyproject.toml
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this tool in your research, please cite:

```
COG Classifier: A Python tool for NCBI COG-based protein classification
GitHub: https://github.com/oduwoleiyanu/ncbi_cog_classifier
```

## Acknowledgments

- NCBI for maintaining the COG database
- BLAST+ developers for the alignment tools
- The bioinformatics community for feedback and contributions
