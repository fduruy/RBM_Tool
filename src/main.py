"""
main.py - Main entry point for the RBM_Tool

This module orchestrates the entire process:
1. Read input files using inputs.py
2. Process trades using calculations.py
3. Write output files using outputs.py
"""

import os
import sys
import logging
from typing import Optional

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inputs import read_and_validate_input
from calculations import process_all_trades
from outputs import write_results, write_detailed_outputs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('RBM_Tool.log')
    ]
)
logger = logging.getLogger(__name__)


def main(input_dir: str = 'data/input/', filename: str = 'GT_Valo.csv',
         output_dir: str = 'data/output/', detailed: bool = False) -> bool:
    """
    Main function to execute the entire RBM_Tool workflow.
    
    Args:
        input_dir (str): Directory containing input files
        filename (str): Name of the input file to process
        output_dir (str): Directory to write output files
        detailed (bool): If True, write detailed output files (internal, external, summary)
                       If False, write only the summary file
    
    Returns:
        bool: True if the entire workflow completed successfully
    """
    logger.info("="*60)
    logger.info("RBM_TOOL - Starting processing")
    logger.info("="*60)
    
    try:
        # Step 1: Read and validate input
        logger.info(f"\nStep 1: Reading input file '{filename}' from {input_dir}")
        df = read_and_validate_input(input_dir, filename)
        
        if df is None:
            logger.error("Failed to read or validate input file. Aborting.")
            return False
        
        logger.info(f"Successfully loaded {len(df)} trades from input file")
        
        # Step 2: Process trades
        logger.info("\nStep 2: Processing trades...")
        internal_trades, external_trades, combined_summary = process_all_trades(df)
        
        if combined_summary.empty:
            logger.error("No summary data generated. Aborting.")
            return False
        
        logger.info(f"Processing complete:")
        logger.info(f"  - Internal trades: {len(internal_trades)}")
        logger.info(f"  - External trades: {len(external_trades)}")
        logger.info(f"  - Summary rows: {len(combined_summary)}")
        
        # Step 3: Write output
        logger.info(f"\nStep 3: Writing output to {output_dir}")
        
        if detailed:
            success = write_detailed_outputs(internal_trades, external_trades, 
                                            combined_summary, output_dir)
        else:
            success = write_results(internal_trades, external_trades, 
                                   combined_summary, output_dir)
        
        if success:
            logger.info("\n" + "="*60)
            logger.info("RBM_TOOL - Processing completed successfully!")
            logger.info("="*60)
        else:
            logger.error("Failed to write output files")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in main workflow: {str(e)}")
        logger.error("\n" + "="*60)
        logger.error("RBM_TOOL - Processing failed!")
        logger.error("="*60)
        return False


def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        dict: Dictionary containing parsed arguments
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='RBM_Tool - Process trade data and generate reports'
    )
    
    parser.add_argument(
        '--input-dir',
        type=str,
        default='data/input/',
        help='Directory containing input files (default: data/input/)'
    )
    
    parser.add_argument(
        '--filename',
        type=str,
        default='GT_Valo.csv',
        help='Name of the input file (default: GT_Valo.csv)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/output/',
        help='Directory to write output files (default: data/output/)'
    )
    
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Write detailed output files (internal, external, summary)'
    )
    
    parser.add_argument(
        '--sample',
        action='store_true',
        help='Use sample data from data/samples/GT_Valo.csv'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    return {
        'input_dir': args.input_dir,
        'filename': args.filename,
        'output_dir': args.output_dir,
        'detailed': args.detailed,
        'sample': args.sample,
        'verbose': args.verbose
    }


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    # Set logging level
    if args['verbose']:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    
    # Use sample data if requested
    if args['sample']:
        args['input_dir'] = 'data/samples/'
        args['filename'] = 'GT_Valo.csv'
    
    logger.info(f"Starting RBM_Tool with arguments: {args}")
    
    # Run main workflow
    success = main(
        input_dir=args['input_dir'],
        filename=args['filename'],
        output_dir=args['output_dir'],
        detailed=args['detailed']
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
