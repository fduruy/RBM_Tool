"""
main.py - Main entry point for the RBM_Tool

This module orchestrates the entire process:
1. Read input files using inputs.py (GT_Valo.csv, Rep_Sensi.csv, Offsetting.csv)
2. Process trades using calculations.py (identify, match, optimize)
3. Write output files using outputs.py (detailed tables and summary)
"""

import os
import sys
import logging
from typing import Optional

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inputs import read_and_validate_input
from calculations import process_all_trades
from outputs import write_all_outputs

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


def main(input_dir: str = 'data/input/', output_dir: str = 'data/output/',
         use_samples: bool = False) -> bool:
    """
    Main function to execute the entire RBM_Tool workflow.
    
    Args:
        input_dir (str): Directory containing input files
        output_dir (str): Directory to write output files
        use_samples (bool): If True, use sample data from data/samples/
        
    Returns:
        bool: True if the entire workflow completed successfully
    """
    logger.info("="*60)
    logger.info("RBM_TOOL - Starting processing")
    logger.info("="*60)
    
    try:
        # Step 1: Read and validate input
        logger.info(f"\nStep 1: Reading input files")
        
        if use_samples:
            data = read_and_validate_input(input_dir='data/samples/')
        else:
            data = read_and_validate_input(input_dir=input_dir)
        
        if data is None:
            logger.error("Failed to read or validate input files. Aborting.")
            return False
        
        logger.info(f"Successfully loaded input data:")
        logger.info(f"  - GT_Valo: {len(data['gt_valo'])} trades")
        logger.info(f"  - Rep_Sensi: {len(data['rep_sensi'])} sensitivity records")
        logger.info(f"  - Offsetting: {len(data['offsetting'])} PnL records")
        
        # Step 2: Process trades and perform matching
        logger.info(f"\nStep 2: Processing trades and performing matching...")
        results = process_all_trades(data)
        
        if not results:
            logger.error("No results generated. Aborting.")
            return False
        
        logger.info(f"Processing complete. Generated {len(results)} result tables:")
        for name, df in results.items():
            logger.info(f"  - {name}: {len(df)} rows")
        
        # Step 3: Write output
        logger.info(f"\nStep 3: Writing output files to {output_dir}")
        success = write_all_outputs(results, output_dir)
        
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
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return False


def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        dict: Dictionary containing parsed arguments
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='RBM_Tool - Process trade data, perform matching, and generate reports'
    )
    
    parser.add_argument(
        '--input-dir',
        type=str,
        default='data/input/',
        help='Directory containing input files (default: data/input/)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/output/',
        help='Directory to write output files (default: data/output/)'
    )
    
    parser.add_argument(
        '--samples',
        action='store_true',
        help='Use sample data from data/samples/ instead of input directory'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    return {
        'input_dir': args.input_dir,
        'output_dir': args.output_dir,
        'use_samples': args.samples,
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
    
    logger.info(f"Starting RBM_Tool with arguments: {args}")
    
    # Run main workflow
    success = main(
        input_dir=args['input_dir'],
        output_dir=args['output_dir'],
        use_samples=args.get('use_samples', False)
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
