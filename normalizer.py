import argparse
import re
import json
from dateutil import parser as date_parser
from typing import Dict, Any
from extractor import extract_information
from preprocessor import preprocess_text
from parser import parse_eml

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
    Applies normalization rules to the extracted data dictionary.
    """
    normalized_record = {}
    NOT_FOUND = "Information not found"

    for key, value in raw_data.items():
        # Skip if value is already the standard not found string
        if value == NOT_FOUND:
            normalized_record[key] = NOT_FOUND
            continue

        # Apply normalization based on the field name (key)
        if key in ["Provider NPI", "Group NPI", "TIN", "Phone Number", "Fax Number"]:
            normalized_record[key] = _normalize_numeric_id(value)
        elif key in ["Effective Date", "Term Date"]:
            normalized_record[key] = _normalize_date(value)
        elif key in ["Provider Name", "Organization Name", "Provider Specialty"]:
            normalized_record[key] = _normalize_name(value)
        elif key in ["Line Of Business", "PPG ID"]:
            # Convert lists to a comma-separated string
            if isinstance(value, list):
                normalized_record[key] = ", ".join(map(str, value))
            else:
                normalized_record[key] = str(value)
        else:
            # For other fields, just convert to string
            normalized_record[key] = str(value)

    # Final check for any empty values that were not caught
    for key, value in normalized_record.items():
        if value is None or value == "":
            normalized_record[key] = NOT_FOUND

    if "Line Of Business" in normalized_record:
        normalized_record["Line Of Business (Medicare/Commercial/Medical)"] = normalized_record.pop("Line Of Business")
    if "Transaction Type" in normalized_record:
        normalized_record["Transaction Type (Add/Update/Term)"] = normalized_record.pop("Transaction Type")

    # Desired key order
    ordered_keys = [
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

    # Build ordered dict
    ordered_record = {key: normalized_record.get(key, NOT_FOUND) for key in ordered_keys}

    return ordered_record


if __name__ == "__main__":
    # This section demonstrates the module's effect
    # Set up the command-line argument parser to test this module
    parser = argparse.ArgumentParser(
        description="Module 4: Data Normalizer."
    )
    parser.add_argument(
        "--email_file",
        type=str,
        help="The path to the input .eml file to be parsed and preprocessed.",
    )

    args = parser.parse_args()

    # --- Pipeline Demonstration ---
    # Step 1: Call Module 1 to get the raw text
    print(f"--- Running Module 1: Parsing {args.email_file} ---")
    raw_email_text = parse_eml(args.email_file)
    print("\n--- Raw Text (Before Preprocessing) ---")
    print(raw_email_text)

    # Step 2: Call Module 2 to preprocess the raw text
    print("\n--- Running Module 2: Preprocessing Text ---")
    clean_text = preprocess_text(raw_email_text)
    print("\n--- Cleaned Text (After Preprocessing) ---")
    if clean_text:
        print(clean_text)
    else:
        print("No text was produced after cleaning.")

    # 3. Call Module 3 for information extraction
    raw_extracted_data = extract_information(clean_text)
    print("--- Raw Data from Extractor (Before Normalization) ---")
    print(json.dumps(raw_extracted_data, indent=2))

    # 4. Call Module 4 for data normalization
    normalized_data = normalize_data(raw_extracted_data)
    print("\n--- Cleaned Data (After Normalization) ---")
    print(json.dumps(normalized_data, indent=2))
