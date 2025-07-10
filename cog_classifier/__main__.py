"""
Command-line interface for NCBI COG Classifier.
"""

import argparse
import sys
import logging
from pathlib import Path

from .classifier import COGClassifier
from .utils import check_blast_installation, validate_fasta_file


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def cmd_download(args):
    """Download COG database command."""
    classifier = COGClassifier(data_dir=args.data_dir)
    
    print("Downloading NCBI COG database...")
    success = classifier.download_database(force=args.force)
    
    if success:
        print("✓ COG database downloaded and setup successfully!")
        return 0
    else:
        print("✗ Failed to download COG database")
        return 1


def cmd_classify(args):
    """Classify sequences command."""
    # Validate input file
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found")
        return 1
    
    is_valid, issues = validate_fasta_file(args.input)
    if not is_valid:
        print("Error: Invalid FASTA file:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    
    # Initialize classifier
    config = {}
    if args.evalue:
        config['blast'] = {'evalue': args.evalue}
    if args.max_targets:
        config['blast'] = config.get('blast', {})
        config['blast']['max_targets'] = args.max_targets
    if args.threads:
        config['blast'] = config.get('blast', {})
        config['blast']['threads'] = args.threads
    
    classifier = COGClassifier(data_dir=args.data_dir, config=config)
    
    # Check if database is ready
    if not classifier.database.is_ready():
        print("Error: COG database not found. Please run 'download' command first.")
        return 1
    
    print(f"Classifying sequences from {args.input}...")
    
    try:
        results = classifier.classify_fasta(
            fasta_file=args.input,
            output_file=args.output,
            output_format=args.format
        )
        
        # Print summary
        stats = classifier.get_statistics(results)
        print(f"\nClassification Summary:")
        print(f"  Total sequences: {stats['total_sequences']}")
        print(f"  Classified: {stats['classified']}")
        print(f"  Unclassified: {stats['unclassified']}")
        print(f"  Errors: {stats['errors']}")
        print(f"  Success rate: {stats['classified']/stats['total_sequences']*100:.1f}%")
        
        if args.output:
            print(f"\nResults saved to: {args.output}")
        
        return 0
        
    except Exception as e:
        print(f"Error during classification: {e}")
        return 1


def cmd_report(args):
    """Generate report command."""
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found")
        return 1
    
    try:
        classifier = COGClassifier()
        classifier.generate_report(
            results=args.input,
            output_file=args.output,
            format_type=args.format
        )
        
        print(f"Report generated: {args.output}")
        return 0
        
    except Exception as e:
        print(f"Error generating report: {e}")
        return 1


def cmd_info(args):
    """Show system information command."""
    print("NCBI COG Classifier - System Information")
    print("=" * 40)
    
    # Check BLAST installation
    blast_installed, blast_info = check_blast_installation()
    print(f"BLAST+ installed: {'✓' if blast_installed else '✗'}")
    if blast_installed:
        print(f"BLAST+ version: {blast_info.split()[1] if len(blast_info.split()) > 1 else 'Unknown'}")
    else:
        print(f"BLAST+ issue: {blast_info}")
    
    # Check database status
    classifier = COGClassifier(data_dir=args.data_dir)
    db_ready = classifier.database.is_ready()
    print(f"COG database ready: {'✓' if db_ready else '✗'}")
    
    if db_ready:
        try:
            classifier.database.load_data()
            db_stats = classifier.database.get_statistics()
            print(f"COG definitions: {db_stats['total_cogs']}")
            print(f"Protein assignments: {db_stats['total_proteins']}")
            print(f"Functional categories: {db_stats['functional_categories']}")
        except Exception as e:
            print(f"Error loading database stats: {e}")
    else:
        print("Run 'download' command to setup the database")
    
    print(f"\nData directory: {Path(args.data_dir).absolute()}")
    
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="NCBI COG Classifier - Classify protein sequences using COG database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download COG database
  python -m cog_classifier download
  
  # Classify sequences
  python -m cog_classifier classify -i proteins.fasta -o results.json
  
  # Generate HTML report
  python -m cog_classifier report -i results.json -o report.html
  
  # Check system status
  python -m cog_classifier info
        """
    )
    
    parser.add_argument(
        '--data-dir', 
        default='./data',
        help='Directory to store COG database files (default: ./data)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Download command
    download_parser = subparsers.add_parser(
        'download',
        help='Download and setup COG database'
    )
    download_parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-download even if database exists'
    )
    
    # Classify command
    classify_parser = subparsers.add_parser(
        'classify',
        help='Classify protein sequences'
    )
    classify_parser.add_argument(
        '-i', '--input',
        required=True,
        help='Input FASTA file'
    )
    classify_parser.add_argument(
        '-o', '--output',
        help='Output file (optional)'
    )
    classify_parser.add_argument(
        '--format',
        choices=['json', 'csv', 'tsv'],
        default='json',
        help='Output format (default: json)'
    )
    classify_parser.add_argument(
        '--evalue',
        type=float,
        help='E-value threshold for BLAST (default: 1e-5)'
    )
    classify_parser.add_argument(
        '--max-targets',
        type=int,
        help='Maximum number of target sequences (default: 10)'
    )
    classify_parser.add_argument(
        '--threads',
        type=int,
        help='Number of threads for BLAST (default: 4)'
    )
    
    # Report command
    report_parser = subparsers.add_parser(
        'report',
        help='Generate classification report'
    )
    report_parser.add_argument(
        '-i', '--input',
        required=True,
        help='Input classification results file (JSON)'
    )
    report_parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output report file'
    )
    report_parser.add_argument(
        '--format',
        choices=['html', 'txt', 'json'],
        default='html',
        help='Report format (default: html)'
    )
    
    # Info command
    info_parser = subparsers.add_parser(
        'info',
        help='Show system information and database status'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Execute command
    if args.command == 'download':
        return cmd_download(args)
    elif args.command == 'classify':
        return cmd_classify(args)
    elif args.command == 'report':
        return cmd_report(args)
    elif args.command == 'info':
        return cmd_info(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
