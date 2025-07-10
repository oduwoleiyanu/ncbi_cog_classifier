"""
Main COG classifier module for protein sequence classification.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Union
from pathlib import Path

from .database import COGDatabase
from .parser import FastaParser, COGParser
from .utils import run_blast, parse_blast_output
from .reporter import COGReporter


class COGClassifier:
    """
    Main classifier for protein sequences using NCBI COG database.
    """
    
    def __init__(self, data_dir: str = "./data", config: Optional[Dict] = None):
        """
        Initialize COG classifier.
        
        Args:
            data_dir: Directory to store COG database files
            config: Configuration dictionary
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Default configuration
        self.config = {
            "blast": {
                "evalue": 1e-5,
                "max_targets": 10,
                "threads": 4,
                "word_size": 3
            },
            "output": {
                "default_format": "json",
                "include_all_hits": True
            }
        }
        
        if config:
            self.config.update(config)
            
        self.database = COGDatabase(self.data_dir)
        self.fasta_parser = FastaParser()
        self.cog_parser = COGParser()
        self.reporter = COGReporter()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def download_database(self, force: bool = False) -> bool:
        """
        Download and setup COG database.
        
        Args:
            force: Force re-download even if database exists
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Downloading COG database...")
            success = self.database.download(force=force)
            if success:
                self.logger.info("COG database downloaded successfully")
                return self.database.setup_blast_db()
            return False
        except Exception as e:
            self.logger.error(f"Error downloading database: {e}")
            return False
    
    def classify_sequence(self, sequence: str, sequence_id: str = "query") -> Dict:
        """
        Classify a single protein sequence.
        
        Args:
            sequence: Protein sequence string
            sequence_id: Identifier for the sequence
            
        Returns:
            Classification results dictionary
        """
        if not self.database.is_ready():
            raise RuntimeError("COG database not ready. Run download_database() first.")
            
        # Create temporary FASTA file
        temp_fasta = self.data_dir / "temp_query.fasta"
        with open(temp_fasta, 'w') as f:
            f.write(f">{sequence_id}\n{sequence}\n")
            
        try:
            # Run BLAST search
            blast_results = run_blast(
                query_file=str(temp_fasta),
                database=str(self.database.blast_db_path),
                evalue=self.config["blast"]["evalue"],
                max_targets=self.config["blast"]["max_targets"],
                threads=self.config["blast"]["threads"]
            )
            
            # Parse results
            parsed_results = parse_blast_output(blast_results)
            
            # Get COG annotations
            classified_results = self._annotate_with_cog(parsed_results, sequence_id, len(sequence))
            
            return classified_results
            
        finally:
            # Clean up temporary file
            if temp_fasta.exists():
                temp_fasta.unlink()
    
    def classify_fasta(self, fasta_file: str, output_file: Optional[str] = None, 
                      output_format: str = "json") -> List[Dict]:
        """
        Classify multiple sequences from a FASTA file.
        
        Args:
            fasta_file: Path to input FASTA file
            output_file: Path to output file (optional)
            output_format: Output format (json, csv, tsv)
            
        Returns:
            List of classification results
        """
        if not self.database.is_ready():
            raise RuntimeError("COG database not ready. Run download_database() first.")
            
        # Parse FASTA file
        sequences = self.fasta_parser.parse(fasta_file)
        results = []
        
        self.logger.info(f"Classifying {len(sequences)} sequences...")
        
        for i, (seq_id, sequence) in enumerate(sequences.items(), 1):
            self.logger.info(f"Processing sequence {i}/{len(sequences)}: {seq_id}")
            
            try:
                result = self.classify_sequence(sequence, seq_id)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error classifying {seq_id}: {e}")
                # Add error result
                results.append({
                    "sequence_id": seq_id,
                    "error": str(e),
                    "length": len(sequence)
                })
        
        # Save results if output file specified
        if output_file:
            self._save_results(results, output_file, output_format)
            
        return results
    
    def _annotate_with_cog(self, blast_results: List[Dict], sequence_id: str, 
                          sequence_length: int) -> Dict:
        """
        Annotate BLAST results with COG information.
        
        Args:
            blast_results: Parsed BLAST results
            sequence_id: Query sequence ID
            sequence_length: Length of query sequence
            
        Returns:
            Annotated classification result
        """
        if not blast_results:
            return {
                "sequence_id": sequence_id,
                "length": sequence_length,
                "best_hit": None,
                "all_hits": []
            }
        
        # Get COG annotations for all hits
        annotated_hits = []
        for hit in blast_results:
            cog_info = self.database.get_cog_annotation(hit["subject_id"])
            if cog_info:
                annotated_hit = {
                    **hit,
                    "cog_id": cog_info.get("cog_id"),
                    "cog_name": cog_info.get("description"),
                    "category": cog_info.get("category"),
                    "category_name": cog_info.get("category_name")
                }
                annotated_hits.append(annotated_hit)
        
        # Sort by e-value (best first)
        annotated_hits.sort(key=lambda x: float(x.get("evalue", 1)))
        
        result = {
            "sequence_id": sequence_id,
            "length": sequence_length,
            "best_hit": annotated_hits[0] if annotated_hits else None,
            "all_hits": annotated_hits if self.config["output"]["include_all_hits"] else []
        }
        
        return result
    
    def _save_results(self, results: List[Dict], output_file: str, format_type: str):
        """
        Save classification results to file.
        
        Args:
            results: Classification results
            output_file: Output file path
            format_type: Output format (json, csv, tsv)
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format_type.lower() == "json":
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
        elif format_type.lower() in ["csv", "tsv"]:
            self._save_tabular(results, output_path, format_type)
        else:
            raise ValueError(f"Unsupported output format: {format_type}")
    
    def _save_tabular(self, results: List[Dict], output_path: Path, format_type: str):
        """
        Save results in tabular format (CSV/TSV).
        
        Args:
            results: Classification results
            output_path: Output file path
            format_type: csv or tsv
        """
        import csv
        
        delimiter = "," if format_type.lower() == "csv" else "\t"
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter)
            
            # Write header
            header = [
                "sequence_id", "length", "cog_id", "cog_name", "category", 
                "category_name", "evalue", "bit_score", "identity", "coverage"
            ]
            writer.writerow(header)
            
            # Write data
            for result in results:
                if result.get("error"):
                    # Write error row
                    row = [result["sequence_id"], result["length"]] + ["ERROR"] * 8
                    writer.writerow(row)
                elif result.get("best_hit"):
                    hit = result["best_hit"]
                    row = [
                        result["sequence_id"],
                        result["length"],
                        hit.get("cog_id", ""),
                        hit.get("cog_name", ""),
                        hit.get("category", ""),
                        hit.get("category_name", ""),
                        hit.get("evalue", ""),
                        hit.get("bit_score", ""),
                        hit.get("identity", ""),
                        hit.get("coverage", "")
                    ]
                    writer.writerow(row)
                else:
                    # No hits
                    row = [result["sequence_id"], result["length"]] + ["NO_HIT"] * 8
                    writer.writerow(row)
    
    def generate_report(self, results: Union[List[Dict], str], output_file: str, 
                       format_type: str = "html"):
        """
        Generate a comprehensive classification report.
        
        Args:
            results: Classification results or path to results file
            output_file: Output report file path
            format_type: Report format (html, pdf, txt)
        """
        if isinstance(results, str):
            # Load results from file
            with open(results, 'r') as f:
                results = json.load(f)
        
        self.reporter.generate_report(results, output_file, format_type)
    
    def get_statistics(self, results: List[Dict]) -> Dict:
        """
        Get classification statistics.
        
        Args:
            results: Classification results
            
        Returns:
            Statistics dictionary
        """
        stats = {
            "total_sequences": len(results),
            "classified": 0,
            "unclassified": 0,
            "errors": 0,
            "category_distribution": {},
            "top_cogs": {}
        }
        
        for result in results:
            if result.get("error"):
                stats["errors"] += 1
            elif result.get("best_hit"):
                stats["classified"] += 1
                
                # Count categories
                category = result["best_hit"].get("category", "Unknown")
                stats["category_distribution"][category] = stats["category_distribution"].get(category, 0) + 1
                
                # Count COGs
                cog_id = result["best_hit"].get("cog_id", "Unknown")
                stats["top_cogs"][cog_id] = stats["top_cogs"].get(cog_id, 0) + 1
            else:
                stats["unclassified"] += 1
        
        # Sort top COGs
        stats["top_cogs"] = dict(sorted(stats["top_cogs"].items(), 
                                      key=lambda x: x[1], reverse=True)[:10])
        
        return stats
