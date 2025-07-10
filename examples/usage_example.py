#!/usr/bin/env python3
"""
Example usage of the NCBI COG Classifier.

This script demonstrates how to use the COG classifier programmatically.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import cog_classifier
sys.path.insert(0, str(Path(__file__).parent.parent))

from cog_classifier import COGClassifier


def main():
    """Main example function."""
    print("NCBI COG Classifier - Usage Example")
    print("=" * 40)
    
    # Initialize classifier
    classifier = COGClassifier(data_dir="./data")
    
    # Check if database is ready
    if not classifier.database.is_ready():
        print("COG database not found. Downloading...")
        success = classifier.download_database()
        if not success:
            print("Failed to download database. Exiting.")
            return 1
    
    # Example FASTA file
    fasta_file = Path(__file__).parent / "sample_proteins.fasta"
    
    if not fasta_file.exists():
        print(f"Sample FASTA file not found: {fasta_file}")
        return 1
    
    print(f"Classifying sequences from: {fasta_file}")
    
    try:
        # Classify sequences
        results = classifier.classify_fasta(
            fasta_file=str(fasta_file),
            output_file="results.json"
        )
        
        # Print summary
        stats = classifier.get_statistics(results)
        print(f"\nClassification Results:")
        print(f"  Total sequences: {stats['total_sequences']}")
        print(f"  Classified: {stats['classified']}")
        print(f"  Unclassified: {stats['unclassified']}")
        print(f"  Errors: {stats['errors']}")
        print(f"  Success rate: {stats['classified']/stats['total_sequences']*100:.1f}%")
        
        # Show first few results
        print(f"\nFirst few results:")
        for i, result in enumerate(results[:3]):
            seq_id = result.get('sequence_id', 'Unknown')
            if result.get('best_hit'):
                hit = result['best_hit']
                cog_id = hit.get('cog_id', 'N/A')
                category = hit.get('category', 'N/A')
                evalue = hit.get('evalue', 0)
                print(f"  {seq_id}: {cog_id} (Category {category}, E-value: {evalue:.1e})")
            else:
                print(f"  {seq_id}: No significant hits")
        
        # Generate HTML report
        print(f"\nGenerating HTML report...")
        classifier.generate_report(
            results=results,
            output_file="classification_report.html",
            format_type="html"
        )
        print("Report saved to: classification_report.html")
        
        return 0
        
    except Exception as e:
        print(f"Error during classification: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
