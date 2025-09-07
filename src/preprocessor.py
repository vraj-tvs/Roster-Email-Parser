import argparse
import re

# from parser import parse_eml  # Assuming module_1_parser.py is in the same directory


def preprocess_text(raw_text: str) -> str:
    """
    Cleans and standardizes the raw text extracted from an email.
    """
    if not raw_text:
        return ""

    # 1. Start with initial character replacements for known artifacts
    # For example, removing the double asterisks from the sample email
    cleaned_text = raw_text.replace("**", "")

    # 2. Split the text into individual lines
    lines = cleaned_text.splitlines()

    processed_lines = []
    for line in lines:
        # 3. For each line, strip leading/trailing whitespace
        stripped_line = line.strip()

        # 4. Collapse multiple spaces within the line to a single space
        normalized_line = re.sub(r"\s+", " ", stripped_line)

        # 5. Only keep lines that are not empty after cleaning
        if normalized_line:
            processed_lines.append(normalized_line)

    # 6. Join the cleaned lines back together with a single newline character
    return "\n".join(processed_lines)


# For independent testing only
# if __name__ == "__main__":
#     # Set up the command-line argument parser to test this module
#     parser = argparse.ArgumentParser(
#         description="Module 2: Text Preprocessor for HiLabs Hackathon."
#     )
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

#     # Print the final preprocessed text
#     print("\n--- Cleaned Text (After Preprocessing) ---")
#     if clean_text:
#         print(clean_text)
#     else:
#         print("No text was produced after cleaning.")
#     print("\n--- End of a process ---")
