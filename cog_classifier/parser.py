"""
Parser modules for FASTA files and COG data formats.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class FastaParser:
    """
    Parser for FASTA format files.
    """
    
    def __init__(self):
        """Initialize FASTA parser."""
        self.logger = logging.getLogger(__name__)
    
    def parse(self, fasta_file: str) -> Dict[str, str]:
        """
        Parse FASTA file and return sequences.
        
        Args:
            fasta_file: Path to FASTA file
            
        Returns:
            Dictionary mapping sequence IDs to sequences
        """
        sequences = {}
        current_id = None
        current_seq = []
        
        try:
            with open(fasta_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    if line.startswith('>'):
                        # Save previous sequence if exists
                        if current_id is not None:
                            sequences[current_id] = ''.join(current_seq)
                        
                        # Start new sequence
                        current_id = self._parse_header(line)
                        current_seq = []
                        
                    else:
                        # Validate sequence line
                        if current_id is None:
                            raise ValueError(f"Line {line_num}: Sequence data without header")
                        
                        # Clean and validate sequence
                        clean_seq = self._clean_sequence(line)
                        if clean_seq:
                            current_seq.append(clean_seq)
                
                # Save last sequence
                if current_id is not None:
                    sequences[current_id] = ''.join(current_seq)
            
            self.logger.info(f"Parsed {len(sequences)} sequences from {fasta_file}")
            return sequences
            
        except FileNotFoundError:
            self.logger.error(f"FASTA file not found: {fasta_file}")
            raise
        except Exception as e:
            self.logger.error(f"Error parsing FASTA file {fasta_file}: {e}")
            raise
    
    def _parse_header(self, header_line: str) -> str:
        """
        Parse FASTA header line to extract sequence ID.
        
        Args:
            header_line: Header line starting with '>'
            
        Returns:
            Sequence identifier
        """
        # Remove '>' and split on whitespace
        header = header_line[1:].strip()
        
        # Extract first part as ID (before first space)
        seq_id = header.split()[0] if header else "unknown"
        
        return seq_id
    
    def _clean_sequence(self, seq_line: str) -> str:
        """
        Clean and validate sequence line.
        
        Args:
            seq_line: Raw sequence line
            
        Returns:
            Cleaned sequence string
        """
        # Remove whitespace and convert to uppercase
        clean_seq = re.sub(r'\s+', '', seq_line.upper())
        
        # Validate protein sequence (allow standard amino acid codes)
        valid_chars = set('ACDEFGHIKLMNPQRSTVWYXBZJU*-')
        invalid_chars = set(clean_seq) - valid_chars
        
        if invalid_chars:
            self.logger.warning(f"Invalid characters in sequence: {invalid_chars}")
            # Remove invalid characters
            clean_seq = ''.join(c for c in clean_seq if c in valid_chars)
        
        return clean_seq
    
    def write_fasta(self, sequences: Dict[str, str], output_file: str, 
                   line_length: int = 80):
        """
        Write sequences to FASTA file.
        
        Args:
            sequences: Dictionary of sequence ID to sequence
            output_file: Output FASTA file path
            line_length: Maximum line length for sequences
        """
        try:
            with open(output_file, 'w') as f:
                for seq_id, sequence in sequences.items():
                    f.write(f">{seq_id}\n")
                    
                    # Write sequence with line breaks
                    for i in range(0, len(sequence), line_length):
                        f.write(sequence[i:i+line_length] + '\n')
            
            self.logger.info(f"Wrote {len(sequences)} sequences to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error writing FASTA file {output_file}: {e}")
            raise
    
    def validate_sequences(self, sequences: Dict[str, str]) -> Dict[str, List[str]]:
        """
        Validate protein sequences and return issues.
        
        Args:
            sequences: Dictionary of sequences to validate
            
        Returns:
            Dictionary mapping sequence IDs to list of issues
        """
        issues = {}
        
        for seq_id, sequence in sequences.items():
            seq_issues = []
            
            # Check sequence length
            if len(sequence) < 10:
                seq_issues.append("Sequence too short (< 10 amino acids)")
            elif len(sequence) > 10000:
                seq_issues.append("Sequence very long (> 10,000 amino acids)")
            
            # Check for unusual amino acid composition
            stop_codons = sequence.count('*')
            if stop_codons > 1:
                seq_issues.append(f"Multiple stop codons ({stop_codons})")
            
            # Check for excessive gaps or unknown residues
            gaps = sequence.count('-')
            unknowns = sequence.count('X')
            
            if gaps > len(sequence) * 0.1:
                seq_issues.append(f"High gap content ({gaps/len(sequence)*100:.1f}%)")
            
            if unknowns > len(sequence) * 0.1:
                seq_issues.append(f"High unknown residue content ({unknowns/len(sequence)*100:.1f}%)")
            
            if seq_issues:
                issues[seq_id] = seq_issues
        
        return issues


class COGParser:
    """
    Parser for COG database files and formats.
    """
    
    def __init__(self):
        """Initialize COG parser."""
        self.logger = logging.getLogger(__name__)
    
    def parse_cog_definitions(self, def_file: str) -> Dict[str, Dict]:
        """
        Parse COG definitions file.
        
        Args:
            def_file: Path to COG definitions file
            
        Returns:
            Dictionary mapping COG IDs to definition info
        """
        definitions = {}
        
        try:
            with open(def_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        cog_id = parts[0]
                        category = parts[1]
                        description = parts[2]
                        
                        definitions[cog_id] = {
                            'cog_id': cog_id,
                            'category': category,
                            'description': description
                        }
                    else:
                        self.logger.warning(f"Line {line_num}: Invalid format in COG definitions")
            
            self.logger.info(f"Parsed {len(definitions)} COG definitions")
            return definitions
            
        except Exception as e:
            self.logger.error(f"Error parsing COG definitions file {def_file}: {e}")
            raise
    
    def parse_functional_categories(self, fun_file: str) -> Dict[str, str]:
        """
        Parse functional categories file.
        
        Args:
            fun_file: Path to functional categories file
            
        Returns:
            Dictionary mapping category codes to names
        """
        categories = {}
        
        try:
            with open(fun_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        category_code = parts[0]
                        category_name = parts[1]
                        categories[category_code] = category_name
                    else:
                        self.logger.warning(f"Line {line_num}: Invalid format in functional categories")
            
            self.logger.info(f"Parsed {len(categories)} functional categories")
            return categories
            
        except Exception as e:
            self.logger.error(f"Error parsing functional categories file {fun_file}: {e}")
            raise
    
    def parse_cog_assignments(self, csv_file: str) -> Dict[str, str]:
        """
        Parse COG protein assignments file.
        
        Args:
            csv_file: Path to COG assignments CSV file
            
        Returns:
            Dictionary mapping protein IDs to COG IDs
        """
        assignments = {}
        
        try:
            with open(csv_file, 'r') as f:
                # Skip header if present
                first_line = f.readline().strip()
                if not first_line.startswith('#') and ',' in first_line:
                    # Check if it looks like a header
                    if 'protein_id' not in first_line.lower():
                        f.seek(0)  # Reset if not a header
                
                for line_num, line in enumerate(f, 2):  # Start from line 2
                    line = line.strip()
                    
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(',')
                    if len(parts) >= 7:
                        # Expected format: domain_id,genome_id,protein_id,protein_length,cog_id,membership_class,gene_name
                        protein_id = parts[2].strip()
                        cog_id = parts[4].strip()
                        
                        if protein_id and cog_id and cog_id != '-':
                            assignments[protein_id] = cog_id
                    else:
                        self.logger.warning(f"Line {line_num}: Invalid format in COG assignments")
            
            self.logger.info(f"Parsed {len(assignments)} COG assignments")
            return assignments
            
        except Exception as e:
            self.logger.error(f"Error parsing COG assignments file {csv_file}: {e}")
            raise
    
    def extract_protein_ids_from_fasta(self, fasta_file: str) -> List[str]:
        """
        Extract protein IDs from COG FASTA file headers.
        
        Args:
            fasta_file: Path to COG FASTA file
            
        Returns:
            List of protein IDs
        """
        protein_ids = []
        
        try:
            with open(fasta_file, 'r') as f:
                for line in f:
                    if line.startswith('>'):
                        # Parse COG FASTA header format
                        # Example: >gi|15604522|ref|NP_214052.1| [COG0001] glutamate-1-semialdehyde 2,1-aminomutase
                        header = line[1:].strip()
                        
                        # Extract protein ID (usually after ref| or similar)
                        protein_id = self._extract_protein_id_from_header(header)
                        if protein_id:
                            protein_ids.append(protein_id)
            
            self.logger.info(f"Extracted {len(protein_ids)} protein IDs from FASTA")
            return protein_ids
            
        except Exception as e:
            self.logger.error(f"Error extracting protein IDs from {fasta_file}: {e}")
            raise
    
    def _extract_protein_id_from_header(self, header: str) -> Optional[str]:
        """
        Extract protein ID from FASTA header.
        
        Args:
            header: FASTA header line (without >)
            
        Returns:
            Protein ID or None if not found
        """
        # Try different patterns for protein ID extraction
        patterns = [
            r'ref\|([^|]+)',  # RefSeq format
            r'gb\|([^|]+)',   # GenBank format
            r'emb\|([^|]+)',  # EMBL format
            r'dbj\|([^|]+)',  # DDBJ format
            r'pir\|([^|]+)',  # PIR format
            r'sp\|([^|]+)',   # SwissProt format
            r'tr\|([^|]+)',   # TrEMBL format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, header)
            if match:
                return match.group(1)
        
        # If no pattern matches, try to get first part before space
        parts = header.split()
        if parts:
            # Remove common prefixes
            protein_id = parts[0]
            for prefix in ['gi|', 'ref|', 'gb|', 'emb|', 'dbj|', 'pir|', 'sp|', 'tr|']:
                if protein_id.startswith(prefix):
                    protein_id = protein_id[len(prefix):]
                    break
            
            # Remove version number if present
            if '.' in protein_id:
                protein_id = protein_id.split('.')[0]
            
            return protein_id
        
        return None
    
    def validate_cog_data(self, definitions: Dict, categories: Dict, 
                         assignments: Dict) -> Dict[str, List[str]]:
        """
        Validate COG data consistency.
        
        Args:
            definitions: COG definitions
            categories: Functional categories
            assignments: Protein assignments
            
        Returns:
            Dictionary of validation issues
        """
        issues = {
            'missing_categories': [],
            'orphaned_assignments': [],
            'inconsistent_categories': []
        }
        
        # Check for missing categories in definitions
        used_categories = set()
        for cog_info in definitions.values():
            category = cog_info['category']
            used_categories.add(category)
            
            if category not in categories:
                issues['missing_categories'].append(category)
        
        # Check for orphaned assignments (COG IDs not in definitions)
        defined_cogs = set(definitions.keys())
        assigned_cogs = set(assignments.values())
        
        orphaned = assigned_cogs - defined_cogs
        issues['orphaned_assignments'] = list(orphaned)
        
        # Remove duplicates
        issues['missing_categories'] = list(set(issues['missing_categories']))
        
        return issues
