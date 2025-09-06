import argparse
import re
import spacy
import json

# Import functions from previous modules
from parser import parse_eml
from preprocessor import preprocess_text

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


def extract_information(text: str) -> dict:
    """
    Extracts provider information using an improved hybrid and rule-based approach.

    Args:
        text: The preprocessed text from an email.

    Returns:
        A dictionary containing the extracted raw information.
    """
    # Standard string for missing information, as requested
    NOT_FOUND = "Information not found"

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
        "TIN": r"(?:Tax ID|TIN|Taxation Id|Tax ID Number):?\s*([\d-]+)",
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
            if "Provider Name" not in data and ent.label_ == "PERSON" and "Provider Name" not in data:
                data["Provider Name"] = ent.text
            elif "Organization Name" not in data and ent.label_ == "ORG" and "Organization Name" not in data:
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
        lob_match = re.search(r"PPG#\'s\s*/\s*(.*)", block.group(1))
        if lob_match:
            lob = lob_match.group(1).strip()
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
                if data.get("Organization Name", "Mercian Medical Group") in line:
                    ppg_match = re.search(r"(\w+)$", line)
                    if ppg_match:
                        data["PPG ID"].append(ppg_match.group(1).strip())
                        break

    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Module 3: Advanced Information Extractor."
    )
    parser.add_argument(
        "--email_file", type=str, help="The path to the input .eml file."
    )
    args = parser.parse_args()

    # --- Full Pipeline Demonstration ---
    raw_text = parse_eml(args.email_file)
    clean_text = preprocess_text(raw_text)
    print("--- Cleaned Text Fed to Extractor ---")
    print(clean_text)

    extracted_data = extract_information(clean_text)

    print("\n--- Extracted Data ---")
    print(json.dumps(extracted_data, indent=2))
    print("\n--- End of a process ---")
