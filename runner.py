import argparse
import json
import os
import time

# Import the primary function from each of our modules
from src.parser import parse_eml
from src.preprocessor import preprocess_text
from src.extractor import extract_information
from src.normalizer import normalize_data
from src.excel_generator import generate_excel
from utils.logger import init_logger

OUTPUT_DIR = "data/output"


def process_file(input_file, logger):
    logger.info(f"\n{'='*100}")
    logger.info(f"🚀 Starting pipeline for: {input_file}")
    start_time = time.time()

    # --- Module 1: Parse Email ---
    if not os.path.exists(input_file):
        logger.error(f"Input file not found at '{input_file}'")
        return None, None
    raw_text = parse_eml(input_file)
    if not raw_text:
        logger.error("Could not extract text from email. Skipping.")
        return None, None
    logger.info("Module 1: Parsing complete.")

    # --- Module 2: Preprocess Text ---
    clean_text = preprocess_text(raw_text)
    logger.info("Module 2: Preprocessing complete.")

    # --- Module 3: Extract Information ---
    extracted_records = extract_information(clean_text)
    if not extracted_records:
        logger.error("No records were extracted from the email. Skipping.")
        return None, None
    logger.info(f"Module 3: Extraction complete.")
    # Uncomment the following line to log raw extracted data
    # logger.info(
    #     "--- Raw Extracted Data ---\n" + json.dumps(extracted_records, indent=2)
    # )

    # --- Module 4: Normalize Data ---
    normalized_records = normalize_data(extracted_records[0])
    logger.info("Module 4: Normalization complete.")
    # Uncomment the following line to log normalized data
    # logger.info(
    #     "--- Final Normalized Data ---\n" + json.dumps(normalized_records, indent=2)
    # )

    # --- Module 5: Generate Excel ---
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    output_file = os.path.join(
        OUTPUT_DIR, f"{os.path.splitext(os.path.basename(input_file))[0]}.xlsx"
    )
    generate_excel([normalized_records], output_file)
    logger.info("Module 5: .xlsx creation complete.")
    logger.info(f"Pipeline finished successfully for {input_file}!\n")

    end_time = time.time()
    tat_seconds = end_time - start_time
    return tat_seconds, output_file


def main():
    """
    Executes the full data extraction and normalization pipeline for single or multiple files.
    """
    parser = argparse.ArgumentParser(
        description="HiLabs Roster Email Parsing Pipeline."
    )
    parser.add_argument("--input_file", type=str, help="Path to the input .eml file.")
    parser.add_argument(
        "--input_folder", type=str, help="Path to a folder containing .eml files."
    )
    args = parser.parse_args()

    tat_results = []
    logger = init_logger()

    if args.input_file:
        tat, output_file = process_file(args.input_file, logger)
        if tat is not None:
            tat_results.append(
                {"file": args.input_file, "output": output_file, "tat_seconds": tat}
            )
    elif args.input_folder:
        if not os.path.exists(args.input_folder):
            logger.error(f"Input folder not found at '{args.input_folder}'")
            return
        eml_files = [
            os.path.join(args.input_folder, f)
            for f in os.listdir(args.input_folder)
            if f.lower().endswith(".eml")
        ]
        if not eml_files:
            logger.error(f"No .eml files found in '{args.input_folder}'")
            return
        logger.info(f"Found {len(eml_files)} .eml files in '{args.input_folder}'")
        for eml_file in eml_files:
            tat, output_file = process_file(eml_file, logger)
            if tat is not None:
                tat_results.append(
                    {"file": eml_file, "output": output_file, "tat_seconds": tat}
                )
    else:
        logger.error("Please provide either --input_file or --input_folder.")
        return

    logger.info(f"\n{'='*100}")
    logger.info(f".xlsx file(s) saved in '{OUTPUT_DIR}'")
    logger.info(f"\n{'='*100}")

    # --- TAT Analysis ---
    logger.info("=== Turnaround Time (TAT) Analysis ===")
    total_tat = sum(r["tat_seconds"] for r in tat_results)
    for r in tat_results:
        logger.info(
            f"File: {os.path.basename(r['file'])} | TAT: {r['tat_seconds']:.2f} seconds | Output: {os.path.basename(r['output'])}"
        )
    logger.info(f"Total files processed: {len(tat_results)}")
    logger.info(f"Total TAT: {total_tat:.2f} seconds")
    if tat_results:
        logger.info(f"Average TAT per file: {total_tat / len(tat_results):.2f} seconds")


if __name__ == "__main__":
    main()
