"""
Utility functions for BLAST operations and other helper functions.
"""

import os
import re
import subprocess
import tempfile
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path


def run_blast(query_file: str, database: str, evalue: float = 1e-5,
              max_targets: int = 10, threads: int = 4, 
              word_size: int = 3) -> str:
    """
    Run BLASTP search against COG database.
    
    Args:
        query_file: Path to query FASTA file
        database: Path to BLAST database
        evalue: E-value threshold
        max_targets: Maximum number of target sequences
        threads: Number of threads to use
        word_size: Word size for BLAST
        
    Returns:
        BLAST output in tabular format
    """
    logger = logging.getLogger(__name__)
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.blast', delete=False) as tmp_file:
        output_file = tmp_file.name
    
    try:
        # Build BLASTP command
        cmd = [
            'blastp',
            '-query', query_file,
            '-db', database,
            '-out', output_file,
            '-evalue', str(evalue),
            '-max_target_seqs', str(max_targets),
            '-num_threads', str(threads),
            '-word_size', str(word_size),
            '-outfmt', '6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore qcovs'
        ]
        
        logger.debug(f"Running BLAST command: {' '.join(cmd)}")
        
        # Run BLAST
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        
        if result.returncode != 0:
            logger.error(f"BLAST failed with return code {result.returncode}")
            logger.error(f"BLAST stderr: {result.stderr}")
            raise RuntimeError(f"BLAST search failed: {result.stderr}")
        
        # Read output
        with open(output_file, 'r') as f:
            blast_output = f.read()
        
        logger.info(f"BLAST search completed successfully")
        return blast_output
        
    except subprocess.TimeoutExpired:
        logger.error("BLAST search timed out")
        raise RuntimeError("BLAST search timed out after 1 hour")
    except FileNotFoundError:
        logger.error("blastp command not found. Please install BLAST+")
        raise RuntimeError("blastp command not found. Please install BLAST+")
    except Exception as e:
        logger.error(f"Error running BLAST: {e}")
        raise
    finally:
        # Clean up temporary file
        if os.path.exists(output_file):
            os.unlink(output_file)


def parse_blast_output(blast_output: str) -> List[Dict]:
    """
    Parse BLAST tabular output into structured data.
    
    Args:
        blast_output: BLAST output in tabular format
        
    Returns:
        List of hit dictionaries
    """
    hits = []
    
    if not blast_output.strip():
        return hits
    
    # Column headers for outfmt 6 with custom fields
    headers = [
        'query_id', 'subject_id', 'identity', 'length', 'mismatches', 
        'gap_opens', 'query_start', 'query_end', 'subject_start', 
        'subject_end', 'evalue', 'bit_score', 'coverage'
    ]
    
    for line in blast_output.strip().split('\n'):
        if line.strip() and not line.startswith('#'):
            fields = line.strip().split('\t')
            
            if len(fields) >= len(headers):
                hit = {}
                for i, header in enumerate(headers):
                    value = fields[i]
                    
                    # Convert numeric fields
                    if header in ['identity', 'evalue', 'bit_score', 'coverage']:
                        try:
                            hit[header] = float(value)
                        except ValueError:
                            hit[header] = value
                    elif header in ['length', 'mismatches', 'gap_opens', 
                                  'query_start', 'query_end', 'subject_start', 'subject_end']:
                        try:
                            hit[header] = int(value)
                        except ValueError:
                            hit[header] = value
                    else:
                        hit[header] = value
                
                hits.append(hit)
    
    return hits


def check_blast_installation() -> Tuple[bool, str]:
    """
    Check if BLAST+ is properly installed.
    
    Returns:
        Tuple of (is_installed, version_info)
    """
    try:
        result = subprocess.run(['blastp', '-version'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            version_info = result.stdout.strip()
            return True, version_info
        else:
            return False, "BLAST+ not found or not working properly"
            
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, "BLAST+ not installed or not in PATH"
    except Exception as e:
        return False, f"Error checking BLAST+ installation: {e}"


def validate_fasta_file(fasta_file: str) -> Tuple[bool, List[str]]:
    """
    Validate FASTA file format and content.
    
    Args:
        fasta_file: Path to FASTA file
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    if not os.path.exists(fasta_file):
        return False, ["File does not exist"]
    
    try:
        with open(fasta_file, 'r') as f:
            content = f.read()
        
        if not content.strip():
            issues.append("File is empty")
            return False, issues
        
        lines = content.strip().split('\n')
        
        # Check if file starts with header
        if not lines[0].startswith('>'):
            issues.append("File does not start with FASTA header (>)")
        
        # Count sequences and validate format
        sequence_count = 0
        in_sequence = False
        current_seq_length = 0
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            if not line:
                continue
                
            if line.startswith('>'):
                if in_sequence and current_seq_length == 0:
                    issues.append(f"Line {i-1}: Empty sequence found")
                
                sequence_count += 1
                in_sequence = True
                current_seq_length = 0
                
                # Validate header
                if len(line) == 1:
                    issues.append(f"Line {i}: Empty FASTA header")
                    
            else:
                if not in_sequence:
                    issues.append(f"Line {i}: Sequence data without header")
                
                # Validate sequence characters
                invalid_chars = set(line.upper()) - set('ACDEFGHIKLMNPQRSTVWYXBZJU*-')
                if invalid_chars:
                    issues.append(f"Line {i}: Invalid characters in sequence: {invalid_chars}")
                
                current_seq_length += len(line)
        
        # Check final sequence
        if in_sequence and current_seq_length == 0:
            issues.append("Last sequence is empty")
        
        if sequence_count == 0:
            issues.append("No sequences found in file")
        
        return len(issues) == 0, issues
        
    except Exception as e:
        return False, [f"Error reading file: {e}"]


def format_evalue(evalue: float) -> str:
    """
    Format e-value for display.
    
    Args:
        evalue: E-value as float
        
    Returns:
        Formatted e-value string
    """
    if evalue == 0:
        return "0"
    elif evalue < 1e-100:
        return "< 1e-100"
    elif evalue < 1e-10:
        return f"{evalue:.0e}"
    elif evalue < 0.01:
        return f"{evalue:.1e}"
    else:
        return f"{evalue:.3f}"


def calculate_sequence_stats(sequence: str) -> Dict:
    """
    Calculate basic statistics for a protein sequence.
    
    Args:
        sequence: Protein sequence string
        
    Returns:
        Dictionary of sequence statistics
    """
    if not sequence:
        return {}
    
    # Clean sequence
    clean_seq = sequence.upper().replace('-', '').replace('*', '')
    
    # Basic stats
    stats = {
        'length': len(sequence),
        'clean_length': len(clean_seq),
        'gaps': sequence.count('-'),
        'stops': sequence.count('*'),
        'unknowns': sequence.count('X')
    }
    
    # Amino acid composition
    aa_counts = {}
    for aa in 'ACDEFGHIKLMNPQRSTVWY':
        count = clean_seq.count(aa)
        aa_counts[aa] = count
        stats[f'{aa}_count'] = count
        stats[f'{aa}_percent'] = (count / len(clean_seq) * 100) if clean_seq else 0
    
    # Molecular weight estimation (approximate)
    aa_weights = {
        'A': 89.1, 'C': 121.0, 'D': 133.1, 'E': 147.1, 'F': 165.2,
        'G': 75.1, 'H': 155.2, 'I': 131.2, 'K': 146.2, 'L': 131.2,
        'M': 149.2, 'N': 132.1, 'P': 115.1, 'Q': 146.2, 'R': 174.2,
        'S': 105.1, 'T': 119.1, 'V': 117.1, 'W': 204.2, 'Y': 181.2
    }
    
    molecular_weight = sum(aa_weights.get(aa, 0) for aa in clean_seq)
    stats['molecular_weight'] = molecular_weight
    
    # Hydrophobicity (Kyte-Doolittle scale)
    hydrophobicity_scale = {
        'A': 1.8, 'C': 2.5, 'D': -3.5, 'E': -3.5, 'F': 2.8,
        'G': -0.4, 'H': -3.2, 'I': 4.5, 'K': -3.9, 'L': 3.8,
        'M': 1.9, 'N': -3.5, 'P': -1.6, 'Q': -3.5, 'R': -4.5,
        'S': -0.8, 'T': -0.7, 'V': 4.2, 'W': -0.9, 'Y': -1.3
    }
    
    if clean_seq:
        hydrophobicity = sum(hydrophobicity_scale.get(aa, 0) for aa in clean_seq) / len(clean_seq)
        stats['hydrophobicity'] = hydrophobicity
    else:
        stats['hydrophobicity'] = 0
    
    return stats


def create_blast_database(fasta_file: str, db_name: str, db_type: str = 'prot') -> bool:
    """
    Create BLAST database from FASTA file.
    
    Args:
        fasta_file: Input FASTA file
        db_name: Output database name
        db_type: Database type ('prot' or 'nucl')
        
    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        cmd = [
            'makeblastdb',
            '-in', fasta_file,
            '-dbtype', db_type,
            '-out', db_name,
            '-parse_seqids'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"BLAST database created successfully: {db_name}")
            return True
        else:
            logger.error(f"Failed to create BLAST database: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating BLAST database: {e}")
        return False


def download_file(url: str, output_path: str, chunk_size: int = 8192) -> bool:
    """
    Download file from URL with progress tracking.
    
    Args:
        url: URL to download from
        output_path: Local file path to save to
        chunk_size: Download chunk size in bytes
        
    Returns:
        True if successful, False otherwise
    """
    import urllib.request
    import urllib.error
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Downloading {url} to {output_path}")
        
        with urllib.request.urlopen(url) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        logger.debug(f"Downloaded {percent:.1f}% ({downloaded}/{total_size} bytes)")
        
        logger.info(f"Download completed: {output_path}")
        return True
        
    except urllib.error.URLError as e:
        logger.error(f"URL error downloading {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        return False


def get_file_hash(file_path: str, algorithm: str = 'md5') -> str:
    """
    Calculate hash of a file.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
        
    Returns:
        Hex digest of file hash
    """
    import hashlib
    
    hash_func = getattr(hashlib, algorithm)()
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def ensure_directory(directory: str) -> Path:
    """
    Ensure directory exists, create if necessary.
    
    Args:
        directory: Directory path
        
    Returns:
        Path object for the directory
    """
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_filename(filename: str) -> str:
    """
    Clean filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename
    """
    # Remove invalid characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove multiple underscores
    cleaned = re.sub(r'_+', '_', cleaned)
    
    # Remove leading/trailing underscores and dots
    cleaned = cleaned.strip('_.')
    
    return cleaned or 'unnamed'
