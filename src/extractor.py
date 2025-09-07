"""
This project is part of HiLabs Hackathon 2025: Free-Text Roster Emails.
"""
"""
Team Members:
    - Anvit Gupta (anvit_g@cs.iitr.ac.in)
    - Raman Sharma (raman_s@cs.iitr.ac.in)
    - Tamakuwala Vraj Shailesh (tamakuwala_vs@cs.iitr.ac.in)
"""
import argparse
import re
import spacy
import json
from typing import Dict, List, Any

# from parser import parse_eml
# from preprocessor import preprocess_text

NOT_FOUND = "Information not found"

# --- NLP Model Loading ---
# Load the spaCy model once when the script starts. This is efficient.
# 'en_core_web_trf' is a transformer-based model, highly accurate for NER.
try:
    nlp = spacy.load("en_core_web_trf")
except OSError:
    print(
        "Please run 'python -m spacy download en_core_web_trf' to download the model."
    )


def extract_table_data(table_lines: List[str]) -> List[Dict[str, str]]:
    """
    Parses a list of pipe-delimited strings into a list of dictionaries.
    """
    if not table_lines:
        return []

    # Extract headers from the first line, stripping whitespace and filtering empty strings
    header = [h.strip() for h in table_lines[0].split("|") if h.strip()]

    records = []
    # Process the data rows (all lines after the header)
    for line in table_lines[1:]:
        if "---" in line:  # Skip separator lines
            continue

        values = [v.strip() for v in line.split("|") if v.strip()]

        if len(values) == len(header):
            # Zip the headers and values together to create a dictionary for the row
            record = dict(zip(header, values))
            records.append(record)

    return records


def extract_text_data(text: str) -> dict:
    """
    Extracts provider information using an improved hybrid and rule-based approach.

    Args:
        text: The preprocessed text from an email.

    Returns:
        A dictionary containing the extracted raw information.
    """

    # Initialize dictionary to hold extracted data
    data = {}

    # --- Part A: Flexible, Context-Aware Regex Extraction ---
    # Added patterns for the new attributes.
    patterns = {
        "Date": r"(?:Effective|Effective Date|Date):?\s*(\d{1,2}/\d{1,2}/\d{4})",
        "Term Reason": r"(?:Term Reason|Reason for Termination|Reason)(is)?:?\s*([^\n]+)",
        # "Provider Name": r"(?:Provider|Physician):?\s*([^/\n]+)",
        "Provider NPI": r"(?:NPI|Provider NPI|NPI#|NPI Number):?\s*(\d{10})",
        "Provider Specialty": r"NPI:\s*\d{10}\s*([A-Za-z\s]+?)\s*\d{2}[A-Z0-9]",
        "State License": r"(?:License|State License):?\s*([A-Za-z0-9]+)",
        "TIN": r"(?:Tax ID|TIN|Taxation Id|Tax ID Number)\s*#?:?\s*([\d-]+)",
        "Group NPI": r"(?:Group NPI|Organization NPI|Org NPI):?\s*(\d{10})",
        "Complete Address": r"(?:Address|Location|Practice Address):?\s*([^\n]+)",
        "Phone Number": r"(?:Phone|Tel|Contact|Phone Number):?\s*((?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4})",
        "Fax Number": r"(?:Fax|Fax Number):?\s*((?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{4})",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Find the first non-empty group to handle complex regexes
            value = next((g for g in match.groups() if g is not None), None)
            if value:
                data[key] = value.strip().replace('"', "").replace(".", "")

    # --- Part B: NLP (NER) as a Fallback ---
    # If regex fails to find a name, use NER to find PERSON and ORG entities.
    if "Provider Name" not in data or "Organization Name" not in data:
        doc = nlp(text)
        for ent in doc.ents:
            if (
                "Provider Name" not in data
                and ent.label_ == "PERSON"
                and "Provider Name" not in data
            ):
                data["Provider Name"] = ent.text
            elif (
                "Organization Name" not in data
                and ent.label_ == "ORG"
                and "Organization Name" not in data
            ):
                if "Medical Group" in ent.text:
                    data["Organization Name"] = ent.text

    # --- Part C: Business Logic ---
    # 1. Transaction Type Logic
    if "terminate" in text.lower():
        data["Transaction Type"] = "Term"
    elif "add" in text.lower():
        data["Transaction Type"] = "Add"
    else:
        # Defaulting to Update if no other keyword is found
        data["Transaction Type"] = "Update"

    # 2. Transaction Attribute Logic (dependent on Transaction Type)
    if data["Transaction Type"] == "Update":
        if "specialty" in text.lower():
            data["Transaction Attribute"] = "Specialty"
        elif "address" or "move" in text.lower():
            data["Transaction Attribute"] = "Address"
        elif "ppg" in text.lower():
            data["Transaction Attribute"] = "PPG"
        elif "phone number" in text.lower():
            data["Transaction Attribute"] = "Phone Number"
        elif "lob" in text.lower():
            data["Transaction Attribute"] = "LOB"
        else:
            # Default for Update if no other attribute is mentioned
            data["Transaction Attribute"] = "Provider"
    else:
        # For Add/Term, it's typically not a single attribute change
        data["Transaction Attribute"] = "Provider"

    # 3. Date Assignment Logic
    if data.get("Date"):
        if data["Transaction Type"] == "Term":
            data["Term Date"] = data["Date"]
            data["Effective Date"] = NOT_FOUND
        else:
            data["Effective Date"] = data["Date"]
            data["Term Date"] = NOT_FOUND
        del data["Date"]  # Remove the temporary generic 'Date' key
    else:
        data["Effective Date"] = NOT_FOUND
        data["Term Date"] = NOT_FOUND

    # --- Part D: Complex Structural Parsing (for LOB and PPG) ---
    data["Line Of Business"] = []
    data["PPG ID"] = []
    network_blocks = re.finditer(
        r"Network\(s\):(.*?)(\n|$)", text, re.DOTALL | re.IGNORECASE
    )
    text_lines = text.split("\n")

    for block in network_blocks:
        if block:
            lob = block.group(1).strip()
            if "commercial" in lob.lower():
                data["Line Of Business"].append("Commercial")
            elif "medicaid" in lob.lower() or "medical" in lob.lower():
                data["Line Of Business"].append("Medical")
            elif "medicare" in lob.lower():
                data["Line Of Business"].append("Medicare")
            # data["Line Of Business"].append(lob)

        block_start_line = text.count("\n", 0, block.start())
        for i in range(
            block_start_line + 1, min(block_start_line + 4, len(text_lines))
        ):
            line = text_lines[i]
            if "Group" in line or "PPG#" in line:
                ppg_match = re.search(r"(\S+)$", line)
                if ppg_match:
                    data["PPG ID"].append(ppg_match.group(1).strip())
                    break

    return data


def extract_information(text: str) -> List[Dict[str, Any]]:
    """
    Main dispatcher function. Segregates text, parses zones, and merges results.
    """
    table_lines = []
    free_text_lines = []

    # 1. Segregate the text into table zones and free-text zones
    for line in text.split("\n"):
        if line.strip().startswith("|"):
            table_lines.append(line)
        else:
            free_text_lines.append(line)

    non_tabular_text = "\n".join(free_text_lines)

    # 2. Parse the free-text zone to get "global" data
    global_data = extract_text_data(non_tabular_text)

    # 3. Parse the table zone to get record-specific data
    table_records = extract_table_data(table_lines)

    if not table_records:
        # If no table was found, the global data is the only record
        return [global_data] if global_data else []

    # 4. Merge global data into each record from the table
    final_records = []
    for record in table_records:
        # Start with a copy of the global data
        merged_record = global_data.copy()
        # Update/overwrite with the more specific data from the table row
        merged_record.update(record)
        final_records.append(merged_record)

    return final_records


# For independent testing only
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(
#         description="Module 3: Advanced Information Extractor."
#     )
#     parser.add_argument(
#         "--email_file", type=str, help="The path to the input .eml file."
#     )
#     args = parser.parse_args()

#     # --- Full Pipeline Demonstration ---
#     raw_text = parse_eml(args.email_file)
#     clean_text = preprocess_text(raw_text)
#     print("--- Cleaned Text Fed to Extractor ---")
#     print(clean_text)

#     extracted_data = extract_information(clean_text)

#     print("\n--- Extracted Data ---")
#     print(json.dumps(extracted_data, indent=2))
#     print("\n--- End of a process ---")
