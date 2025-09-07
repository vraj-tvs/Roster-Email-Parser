import argparse
import json
import os
import pandas as pd
from typing import List, Dict, Any
# from parser import parse_eml
# from preprocessor import preprocess_text
# from extractor import extract_information
# from normalizer import normalize_data


OUTPUT_DIR = "data/output"


def generate_excel(records: List[Dict[str, Any]], output_path: str):
    """
    Generates an Excel file from a list of normalized data records.
    """
    if not records:
        print("⚠️ Warning: No data records to write to Excel.")
        return

    for record in records:
        if "Line Of Business" in record:
            record["Line Of Business (Medicare/Commercial/Medical)"] = record.pop(
                "Line Of Business"
            )
        elif "Transaction Type" in record:
            record["Transaction Type (Add/Update/Term)"] = record.pop(
                "Transaction Type"
            )

    # Create a pandas DataFrame from our list of records
    df = pd.DataFrame(records)

    try:
        # Write the DataFrame to an Excel file
        # `index=False` is critical to avoid writing the DataFrame's row numbers
        df.to_excel(output_path, index=False, header=True)
        print(f"\n✅ Excel file '{output_path}' generated successfully.")
    except Exception as e:
        print(f"\n❌ Error generating Excel file: {e}")


# For independent testing only
# if __name__ == "__main__":
#     # This section demonstrates the module's effect
#     # Set up the command-line argument parser to test this module
#     parser = argparse.ArgumentParser(
#         description="Module 5: Excel Generator for HiLabs Hackathon."
#     )
#     parser.add_argument(
#         "--email_file",
#         type=str,
#         help="The path to the input .eml file to be parsed and preprocessed.",
#     )

#     args = parser.parse_args()

#     # Step 1: Call Module 1 to get the raw text
#     print(f"--- Running Module 1: Parsing {args.email_file} ---")
#     raw_email_text = parse_eml(args.email_file)
#     print("\n--- Raw Text (Before Preprocessing) ---")
#     print(raw_email_text)

#     # Step 2: Call Module 2 to preprocess the raw text
#     print("\n--- Running Module 2: Preprocessing Text ---")
#     clean_text = preprocess_text(raw_email_text)
#     print("\n--- Cleaned Text (After Preprocessing) ---")
#     if clean_text:
#         print(clean_text)
#     else:
#         print("No text was produced after cleaning.")

#     # 3. Call Module 3 for information extraction
#     raw_extracted_data = extract_information(clean_text)
#     print("\n--- Raw Data from Extractor (Before Normalization) ---")
#     print(json.dumps(raw_extracted_data, indent=2))

#     # 4. Call Module 4 for data normalization
#     normalized_data = normalize_data(raw_extracted_data[0])
#     print("\n--- Cleaned Data (After Normalization) ---")
#     print(json.dumps(normalized_data, indent=2))

#     #  5. Call the Excel generator with the data
#     if not os.path.exists(OUTPUT_DIR):
#         os.makedirs(OUTPUT_DIR)
#     output_file = os.path.join(
#         OUTPUT_DIR, f"{os.path.splitext(os.path.basename(args.email_file))[0]}.xlsx"
#     )
#     generate_excel([normalized_data], output_file)
#     print("\n--- End of  process ---")
