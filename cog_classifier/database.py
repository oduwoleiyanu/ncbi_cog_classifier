"""
COG database management module.
"""

import os
import gzip
import shutil
import logging
import subprocess
from typing import Dict, Optional
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError


class COGDatabase:
    """
    Manages NCBI COG database download, setup, and queries.
    """
    
    # NCBI COG database URLs
    COG_BASE_URL = "https://ftp.ncbi.nlm.nih.gov/pub/COG/COG2020/data/"
    COG_FILES = {
        "cog-20.def.tab": "COG definitions",
        "cog-20.cog.csv": "COG assignments", 
        "cog-20.fa.gz": "COG protein sequences",
        "fun-20.tab": "Functional categories"
    }
    
    def __init__(self, data_dir: Path):
        """
        Initialize COG database manager.
        
        Args:
            data_dir: Directory to store database files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Database file paths
        self.cog_def_file = self.data_dir / "cog-20.def.tab"
        self.cog_csv_file = self.data_dir / "cog-20.cog.csv"
        self.cog_fasta_file = self.data_dir / "cog-20.fa"
        self.cog_fasta_gz = self.data_dir / "cog-20.fa.gz"
        self.fun_file = self.data_dir / "fun-20.tab"
        
        # BLAST database path
        self.blast_db_path = self.data_dir / "cog_blast_db"
        
        # In-memory data structures
        self._cog_definitions = {}
        self._cog_assignments = {}
        self._functional_categories = {}
        self._loaded = False
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def download(self, force: bool = False) -> bool:
        """
        Download COG database files from NCBI.
        
        Args:
            force: Force re-download even if files exist
            
        Returns:
            True if successful, False otherwise
        """
        try:
            for filename, description in self.COG_FILES.items():
                local_path = self.data_dir / filename
                
                if local_path.exists() and not force:
                    self.logger.info(f"File {filename} already exists, skipping download")
                    continue
                
                url = self.COG_BASE_URL + filename
                self.logger.info(f"Downloading {description} from {url}")
                
                try:
                    urlretrieve(url, local_path)
                    self.logger.info(f"Downloaded {filename} successfully")
                except URLError as e:
                    self.logger.error(f"Failed to download {filename}: {e}")
                    return False
            
            # Extract gzipped FASTA file
            if self.cog_fasta_gz.exists() and not self.cog_fasta_file.exists():
                self.logger.info("Extracting COG FASTA file...")
                with gzip.open(self.cog_fasta_gz, 'rb') as f_in:
                    with open(self.cog_fasta_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                self.logger.info("FASTA file extracted successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading COG database: {e}")
            return False
    
    def setup_blast_db(self) -> bool:
        """
        Create BLAST database from COG FASTA file.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.cog_fasta_file.exists():
            self.logger.error("COG FASTA file not found. Run download() first.")
            return False
        
        try:
            # Check if BLAST+ is installed
            result = subprocess.run(['makeblastdb', '-version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error("makeblastdb not found. Please install BLAST+")
                return False
            
            # Create BLAST database
            cmd = [
                'makeblastdb',
                '-in', str(self.cog_fasta_file),
                '-dbtype', 'prot',
                '-out', str(self.blast_db_path),
                '-title', 'COG_Database',
                '-parse_seqids'
            ]
            
            self.logger.info("Creating BLAST database...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("BLAST database created successfully")
                return True
            else:
                self.logger.error(f"Failed to create BLAST database: {result.stderr}")
                return False
                
        except FileNotFoundError:
            self.logger.error("makeblastdb command not found. Please install BLAST+")
            return False
        except Exception as e:
            self.logger.error(f"Error creating BLAST database: {e}")
            return False
    
    def is_ready(self) -> bool:
        """
        Check if database is ready for use.
        
        Returns:
            True if database is ready, False otherwise
        """
        # Check if all required files exist
        required_files = [
            self.cog_def_file,
            self.cog_csv_file,
            self.cog_fasta_file,
            self.fun_file
        ]
        
        files_exist = all(f.exists() for f in required_files)
        
        # Check if BLAST database exists
        blast_db_exists = any(
            (self.data_dir / f"{self.blast_db_path.name}.{ext}").exists()
            for ext in ['phr', 'pin', 'psq']
        )
        
        return files_exist and blast_db_exists
    
    def load_data(self) -> bool:
        """
        Load COG data into memory for fast access.
        
        Returns:
            True if successful, False otherwise
        """
        if self._loaded:
            return True
            
        try:
            # Load functional categories
            self._load_functional_categories()
            
            # Load COG definitions
            self._load_cog_definitions()
            
            # Load COG assignments
            self._load_cog_assignments()
            
            self._loaded = True
            self.logger.info("COG data loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading COG data: {e}")
            return False
    
    def _load_functional_categories(self):
        """Load functional category definitions."""
        if not self.fun_file.exists():
            raise FileNotFoundError(f"Functional categories file not found: {self.fun_file}")
        
        with open(self.fun_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        category_code = parts[0]
                        category_name = parts[1]
                        self._functional_categories[category_code] = category_name
    
    def _load_cog_definitions(self):
        """Load COG definitions."""
        if not self.cog_def_file.exists():
            raise FileNotFoundError(f"COG definitions file not found: {self.cog_def_file}")
        
        with open(self.cog_def_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    parts = line.strip().split('\t')
                    if len(parts) >= 3:
                        cog_id = parts[0]
                        category = parts[1]
                        description = parts[2]
                        
                        self._cog_definitions[cog_id] = {
                            'cog_id': cog_id,
                            'category': category,
                            'description': description,
                            'category_name': self._functional_categories.get(category, 'Unknown')
                        }
    
    def _load_cog_assignments(self):
        """Load COG protein assignments."""
        if not self.cog_csv_file.exists():
            raise FileNotFoundError(f"COG assignments file not found: {self.cog_csv_file}")
        
        with open(self.cog_csv_file, 'r') as f:
            # Skip header if present
            first_line = f.readline().strip()
            if not first_line.startswith('#') and ',' in first_line:
                f.seek(0)  # Reset to beginning if no header
            
            for line in f:
                if line.strip() and not line.startswith('#'):
                    parts = line.strip().split(',')
                    if len(parts) >= 7:
                        # Format: domain_id,genome_id,protein_id,protein_length,cog_id,membership_class,gene_name
                        protein_id = parts[2]
                        cog_id = parts[4]
                        
                        if cog_id and cog_id != '-':
                            self._cog_assignments[protein_id] = cog_id
    
    def get_cog_annotation(self, protein_id: str) -> Optional[Dict]:
        """
        Get COG annotation for a protein ID.
        
        Args:
            protein_id: Protein identifier
            
        Returns:
            COG annotation dictionary or None if not found
        """
        if not self._loaded:
            self.load_data()
        
        # Clean protein ID (remove version numbers, etc.)
        clean_id = protein_id.split('.')[0].split('|')[-1]
        
        # Look up COG assignment
        cog_id = self._cog_assignments.get(clean_id)
        if not cog_id:
            # Try with original ID
            cog_id = self._cog_assignments.get(protein_id)
        
        if cog_id and cog_id in self._cog_definitions:
            return self._cog_definitions[cog_id]
        
        return None
    
    def get_cog_definition(self, cog_id: str) -> Optional[Dict]:
        """
        Get COG definition by COG ID.
        
        Args:
            cog_id: COG identifier
            
        Returns:
            COG definition dictionary or None if not found
        """
        if not self._loaded:
            self.load_data()
        
        return self._cog_definitions.get(cog_id)
    
    def get_functional_categories(self) -> Dict[str, str]:
        """
        Get all functional categories.
        
        Returns:
            Dictionary mapping category codes to names
        """
        if not self._loaded:
            self.load_data()
        
        return self._functional_categories.copy()
    
    def search_cogs(self, query: str, field: str = "description") -> List[Dict]:
        """
        Search COGs by description or other fields.
        
        Args:
            query: Search query
            field: Field to search in (description, category, cog_id)
            
        Returns:
            List of matching COG definitions
        """
        if not self._loaded:
            self.load_data()
        
        results = []
        query_lower = query.lower()
        
        for cog_id, cog_info in self._cog_definitions.items():
            if field == "description" and query_lower in cog_info["description"].lower():
                results.append(cog_info)
            elif field == "category" and query_lower in cog_info["category"].lower():
                results.append(cog_info)
            elif field == "cog_id" and query_lower in cog_id.lower():
                results.append(cog_info)
        
        return results
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Statistics dictionary
        """
        if not self._loaded:
            self.load_data()
        
        category_counts = {}
        for cog_info in self._cog_definitions.values():
            category = cog_info["category"]
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "total_cogs": len(self._cog_definitions),
            "total_proteins": len(self._cog_assignments),
            "functional_categories": len(self._functional_categories),
            "category_distribution": category_counts
        }
