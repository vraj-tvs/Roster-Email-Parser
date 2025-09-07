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
# Try transformer model first, fallback to smaller models if not available
try:
    nlp = spacy.load("en_core_web_trf")
except OSError:
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        try:
            nlp = spacy.load("en_core_web_md")
        except OSError:
            print("No spaCy model found. Please install one with:")
            print("python -m spacy download en_core_web_sm")
            nlp = None


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

    # Initialize dictionary to hold extracted data
    data = {}

    # --- Provider Specialty Extraction (robust for multi-provider lines) ---
    if "Provider Specialty" not in data:
        # Try to find all lines with 'Provider:' and extract specialty after NPI
        provider_lines = re.findall(r"Provider: [^\n]+", text)
        specialties = []
        for line in provider_lines:
            # e.g. Provider: Cyrus Hendricks, M.D / License: D66661 / NPI: 1164444443 / Internal Medicine 207R00000X
            parts = line.split("/")
            if len(parts) >= 4:
                specialty_part = parts[3].strip()
                # Remove taxonomy code if present
                specialty = re.sub(r" [0-9A-Z]{10}$", "", specialty_part)
                specialties.append(specialty)
        # Also check for 'Specialty:' lines
        spec_lines = re.findall(r"Specialty:?\s*([A-Za-z0-9 .,&/-]+)", text, re.IGNORECASE)
        specialties.extend([s.strip() for s in spec_lines])
        if specialties:
            data["Provider Specialty"] = ", ".join(sorted(set(specialties)))

    # --- Line Of Business Extraction (robust for multiple LOBs) ---
    # Handle both regular apostrophes and smart quotes (Unicode \u2019)
    lobs = re.findall(r"Network\(s\): PPG#[''\u2019]s / ([A-Za-z0-9 ,&/-]+)", text)
    lob_line = re.search(r"line of business:?\s*([A-Za-z0-9/\-, &]+)", text, re.IGNORECASE)
    if lob_line:
        lobs.append(lob_line.group(1).strip())
    # Also check for LOBs in bullet/numbered lists after 'Network(s):' lines
    for match in re.finditer(r"Network\(s\):[^\n]*\n((?:\s*[*-] [^\n]+\n?)+)", text):
        for lob_item in re.findall(r"[*-] ([A-Za-z0-9 ,&/-]+)", match.group(1)):
            lobs.append(lob_item.strip())
    if lobs:
        # Clean up extracted LOBs and remove duplicates
        cleaned_lobs = []
        for lob in lobs:
            # Remove HTML entities and extra text
            cleaned_lob = re.sub(r'&#\d+;', '', lob)  # Remove HTML entities
            cleaned_lob = re.sub(r'<[^>]+>', '', cleaned_lob)  # Remove HTML tags
            cleaned_lob = cleaned_lob.strip()
            if cleaned_lob and cleaned_lob not in cleaned_lobs:
                cleaned_lobs.append(cleaned_lob)
        data["Line Of Business"] = [', '.join(sorted(set(cleaned_lobs)))]

    # --- PPG ID Extraction (robust for all list and group formats) ---
    # Extract from "Medical Group - <ID>" and "Medical Group – <ID>" (different dash types)
    # Avoid false matches with "Medical Group affiliation"
    ppg_ids = []
    # More specific pattern for Mercian Medical Group
    for match in re.finditer(r"Mercian Medical Group[ \-–—]+([A-Za-z0-9]+)", text):
        ppg_ids.append(match.group(1))
    # General pattern but avoid "affiliation"
    for match in re.finditer(r"Medical Group[ \-–—]+([A-Za-z0-9]+)", text):
        candidate = match.group(1)
        if candidate.lower() != "affiliation":
            ppg_ids.append(candidate)
    # Also check for simple "- <ID>" patterns
    ppg_ids += re.findall(r"- ([A-Za-z0-9]+)(?:\s|$)", text)
    if ppg_ids:
        # Clean up extracted PPG IDs
        cleaned_ppg_ids = []
        for ppg_id in ppg_ids:
            # Remove HTML entities and tags
            cleaned_id = re.sub(r'&#\d+;', '', ppg_id)
            cleaned_id = re.sub(r'<[^>]+>', '', cleaned_id)
            cleaned_id = cleaned_id.strip()
            if cleaned_id and cleaned_id not in cleaned_ppg_ids and cleaned_id.lower() != "affiliation":
                cleaned_ppg_ids.append(cleaned_id)
        data["PPG ID"] = [', '.join(sorted(set(cleaned_ppg_ids)))]

    # --- Organization Name Extraction (improved for Sample-2) ---
    if "Organization Name" not in data:
        org_match = re.search(r'Medical Group affiliation "([^"]+)"', text)
        if org_match:
            data["Organization Name"] = org_match.group(1).strip()

    # --- Effective Date Extraction (improved for Sample-2) ---
    if data.get("Effective Date", "Information not found") == "Information not found":
        eff_match = re.search(r"Effective Date:?\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})", text, re.IGNORECASE)
        if eff_match:
            data["Effective Date"] = eff_match.group(1).strip()

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


    # --- Organization Name Extraction ---
    # Try to extract organization name from patterns like 'with <ORG> (TIN # ...)'
    if "Organization Name" not in data:
        org_match = re.search(r"with ([A-Za-z0-9 &]+) \(TIN", text)
        if org_match:
            data["Organization Name"] = org_match.group(1).strip()
        elif nlp:
            # Fallback to NER if spacy model is available
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ == "ORG" and "Organization Name" not in data:
                    data["Organization Name"] = ent.text
                    break

    # --- Part B: NLP (NER) as a Fallback for Provider Name ---
    if "Provider Name" not in data and nlp:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                data["Provider Name"] = ent.text
                break

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

    # Initialize any missing list fields
    if "Line Of Business" not in data:
        data["Line Of Business"] = []
    if "PPG ID" not in data:
        data["PPG ID"] = []

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
    # --- Address cleanup for Sample-3 ---
    if "Complete Address" in global_data and global_data["Complete Address"].startswith("s "):
        global_data["Complete Address"] = global_data["Complete Address"][2:]

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
