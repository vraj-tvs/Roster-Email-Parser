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
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup


def parse_eml(file_path: str) -> str:
    """
    Parses an .eml file, intelligently handling both plain text and HTML.
    If an HTML table is found, it's converted to a pipe-delimited text format.
    """
    try:
        with open(file_path, "rb") as fp:
            msg = BytesParser(policy=policy.default).parse(fp)
    except FileNotFoundError:
        return ""

    # Prioritize HTML body if it exists, as it's more structured
    html_body = ""
    plain_text_body = ""

    for part in msg.walk():
        content_type = part.get_content_type()
        if content_type == "text/html":
            html_body = part.get_payload(decode=True)
        elif content_type == "text/plain":
            plain_text_body = part.get_payload(decode=True)

    if html_body:
        # If we have an HTML body, parse it intelligently
        soup = BeautifulSoup(html_body, "lxml")

        # Find all tables in the HTML
        for table in soup.find_all("table"):
            reconstructed_table = []
            # Iterate through each row (tr) in the table
            for row in table.find_all("tr"):
                # Get all cells (td or th) in the row, get their text, and strip whitespace
                cells = [
                    cell.get_text(strip=True) for cell in row.find_all(["td", "th"])
                ]
                # Join the cells with a pipe delimiter to reconstruct the table row
                reconstructed_table.append("| " + " | ".join(cells) + " |")

            # Replace the original <table> tag with our clean, pipe-delimited text version
            table.replace_with("\n".join(reconstructed_table) + "\n")

        # Return the text from the modified HTML, which now contains clean tables
        return soup.get_text()

    # If no HTML body, fall back to the plain text version
    return (
        plain_text_body.decode()
        if isinstance(plain_text_body, bytes)
        else plain_text_body
    )


# For independent testing only
# if __name__ == "__main__":
#     # Set up the command-line argument parser
#     parser = argparse.ArgumentParser(
#         description="Module 1: Email Parser for HiLabs Hackathon."
#     )
#     parser.add_argument(
#         "--email_file", type=str, help="The path to the input .eml file to be parsed."
#     )

#     args = parser.parse_args()

#     # Call the parsing function with the provided file path
#     print(f"--- Parsing Email File: {args.email_file} ---")
#     extracted_text = parse_eml(args.email_file)

#     # Print the final extracted text
#     print("\n--- Extracted Plain Text Body ---")
#     if extracted_text:
#         print(extracted_text)
#     else:
#         print("No plain text body could be extracted.")
#     print("\n--- End of a process ---")
