import argparse
import re
import json
from dateutil import parser as date_parser
from typing import Dict, Any
# from extractor import extract_information
# from preprocessor import preprocess_text
# from parser import parse_eml

NOT_FOUND = "Information not found"

# The official, ordered list of headers. This is our single source of truth.
ORDERED_HEADERS = [
    "Transaction Type (Add/Update/Term)",
    "Transaction Attribute",
    "Effective Date",
    "Term Date",
    "Term Reason",
    "Provider Name",
    "Provider NPI",
    "Provider Specialty",
    "State License",
    "Organization Name",
    "TIN",
    "Group NPI",
    "Complete Address",
    "Phone Number",
    "Fax Number",
    "PPG ID",
    "Line Of Business (Medicare/Commercial/Medical)",
]

# Maps all possible raw key variations to their official, canonical name.
KEY_ALIAS_MAP = {
    "Transaction Type": "Transaction Type (Add/Update/Term)",
    "Transaction Type:": "Transaction Type (Add/Update/Term)",
    "Transaction Attribute": "Transaction Attribute",
    "Effective Date": "Effective Date",
    "Effective Date:": "Effective Date",
    "Term Date": "Term Date",
    "Term Date:": "Term Date",
    "Term Reason": "Term Reason",
    "Term Reason:": "Term Reason",
    "Reason": "Term Reason",
    "Reason:": "Term Reason",
    "Provider Name": "Provider Name",
    "Provider Name:": "Provider Name",
    "Provider NPI": "Provider NPI",
    "Provider NPI:": "Provider NPI",
    "NPI": "Provider NPI",
    "NPI:": "Provider NPI",
    "NPI#": "Provider NPI",
    "NPI#:": "Provider NPI",
    "Provider Specialty": "Provider Specialty",
    "Specialty": "Provider Specialty",
    "Specialty:": "Provider Specialty",
    "State License": "State License",
    "License": "State License",
    "License:": "State License",
    "Organization Name": "Organization Name",
    "TIN": "TIN",
    "TIN:": "TIN",
    "Tax ID": "TIN",
    "Tax ID:": "TIN",
    "Group NPI": "Group NPI",
    "Complete Address": "Complete Address",
    "Address": "Complete Address",
    "Phone Number": "Phone Number",
    "Phone Number:": "Phone Number",
    "Fax Number": "Fax Number",
    "Fax Number:": "Fax Number",
    "PPG ID": "PPG ID",
    "PPG ID:": "PPG ID",
    "Line Of Business": "Line Of Business (Medicare/Commercial/Medical)",
    "Line Of Business:": "Line Of Business (Medicare/Commercial/Medical)",
}


def _normalize_numeric_id(value: Any) -> str:
    """Strips non-numeric characters."""
    if isinstance(value, str):
        return re.sub(r"\D", "", value)
    return str(value)


def _normalize_date(value: Any) -> str:
    """Parses date and formats to MM/DD/YYYY."""
    if isinstance(value, str) and value not in ["", "Information not found"]:
        try:
            return date_parser.parse(value).strftime("%m/%d/%Y")
        except (date_parser.ParserError, TypeError):
            return "Information not found"  # Return standard string if parsing fails
    return "Information not found"


def _normalize_name(value: Any) -> str:
    """Trims, collapses whitespace, and converts to Title Case."""
    if isinstance(value, str):
        return " ".join(value.strip().split()).title()
    return str(value)


def normalize_data(raw_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Normalizes both keys and values from a raw data dictionary to produce a clean,
    standardized record that is complete and correctly ordered.
    """
    interim_record = {}

    # 1. First pass: Normalize all available data into an interim dictionary
    for raw_key, value in raw_data.items():
        canonical_key = KEY_ALIAS_MAP.get(raw_key.strip())
        if not canonical_key or value == NOT_FOUND:
            continue

        if canonical_key in [
            "Provider NPI",
            "Group NPI",
            "TIN",
            "Phone Number",
            "Fax Number",
        ]:
            interim_record[canonical_key] = _normalize_numeric_id(value)
        elif canonical_key in ["Effective Date", "Term Date"]:
            interim_record[canonical_key] = _normalize_date(value)
        elif canonical_key in [
            "Provider Name",
            "Organization Name",
            "Provider Specialty",
        ]:
            interim_record[canonical_key] = _normalize_name(value)
        elif canonical_key in [
            "Line Of Business (Medicare/Commercial/Medical)",
            "PPG ID",
        ]:
            if isinstance(value, list):
                interim_record[canonical_key] = ", ".join(map(str, value))
            else:
                interim_record[canonical_key] = str(value)
        else:
            interim_record[canonical_key] = str(value)

    # 2. Final pass: Build the final record to guarantee order and completeness
    final_ordered_record = {}
    for header in ORDERED_HEADERS:
        # Get the value from our interim record.
        # If the value is missing, empty, or None, it will default to NOT_FOUND.
        value = interim_record.get(header)
        if value:
            final_ordered_record[header] = value
        else:
            final_ordered_record[header] = NOT_FOUND

    return final_ordered_record


# For independent testing only
# if __name__ == "__main__":
#     # This section demonstrates the module's effect
#     # Set up the command-line argument parser to test this module
#     parser = argparse.ArgumentParser(description="Module 4: Data Normalizer.")
#     parser.add_argument(
#         "--email_file",
#         type=str,
#         help="The path to the input .eml file to be parsed and preprocessed.",
#     )

#     args = parser.parse_args()

#     # --- Pipeline Demonstration ---
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
#     print("--- Raw Data from Extractor (Before Normalization) ---")
#     print(json.dumps(raw_extracted_data, indent=2))

#     # 4. Call Module 4 for data normalization
#     normalized_data = normalize_data(raw_extracted_data[0])
#     print("\n--- Cleaned Data (After Normalization) ---")
#     print(json.dumps(normalized_data, indent=2))
