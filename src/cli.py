import argparse
import sys
from processor import BatchProcessor

def main():
    parser = argparse.ArgumentParser(description="Batch process PubChem annotations.")
    parser.add_argument(
        '--file', type=str, required=True,
        help='Path to the input CSV file containing CIDs and SMILES.'
    )
    parser.add_argument(
        '--cid_name', type=str, required=True,
        help='Column name for PubChem CID in the input file.'
    )
    parser.add_argument(
        '--smiles_name', type=str, required=True,
        help='Column name for SMILES in the input file.'
    )
    parser.add_argument(
        '--delay', type=float, default=0.2,
        help='Delay between API requests to avoid rate limiting.'
    )
    parser.add_argument(
        '--max_rows', type=int, default=None,
        help='Maximum number of rows to process. If not specified, all rows will be processed.'
    )
    parser.add_argument(
        '--sample', action='store_true',
        help='If set, randomly sample rows from the input file.'
    )
    parser.add_argument(
        '--resume', action='store_true',
        help='If set, resume from the last checkpoint.'
    )
    parser.add_argument(
        '--verbose', action='store_true',
        help='If set, print detailed logs during processing.'
    )

    args = parser.parse_args()

    processor = BatchProcessor(
        file=args.file,
        cid_name=args.cid_name,
        smiles_name=args.smiles_name,
        delay=args.delay,
        max_rows=args.max_rows,
        sample=args.sample,
        resume=args.resume,
        verbose=args.verbose
    )

    try:
        processor.run()
    except KeyboardInterrupt:
        print("Process interrupted. Saving current state...")
        processor.save_state()
        sys.exit(0)

if __name__ == "__main__":
    main()