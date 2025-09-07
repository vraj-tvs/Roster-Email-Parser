import argparse
import email
from email import policy
from email.parser import BytesParser


def parse_eml(file_path: str) -> str:
    """
    Parses an .eml file and extracts its plain text body.

    This function reads the specified .eml file, walks through its parts to find
    the 'text/plain' content, and returns it as a string. It's designed to
    handle standard email structures.

    Args:
        file_path: The absolute or relative path to the .eml file.

    Returns:
        A string containing the plain text body of the email.
        Returns an empty string if no 'text/plain' part is found or if the
        file cannot be read.
    """
    try:
        with open(file_path, "rb") as fp:
            # Use BytesParser with a policy to handle modern email formats
            msg = BytesParser(policy=policy.default).parse(fp)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return ""
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return ""

    plain_text_body = ""

    # The .walk() method iterates through all parts of the email message
    for part in msg.walk():
        # Check if the part is 'text/plain' and not an attachment
        if (
            part.get_content_type() == "text/plain"
            and part.get("Content-Disposition") is None
        ):
            # Get the payload, decode it from bytes to string
            try:
                # The charset is often specified, get_payload will use it
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                plain_text_body += payload.decode(charset)
            except (UnicodeDecodeError, AttributeError) as e:
                print(f"Could not decode part of the email body: {e}")
                # Fallback to a raw string representation if decoding fails
                if isinstance(part.get_payload(), str):
                    plain_text_body += part.get_payload()

    return plain_text_body.strip()


# For independent testing only
if __name__ == "__main__":
    # Set up the command-line argument parser
    parser = argparse.ArgumentParser(
        description="Module 1: Email Parser for HiLabs Hackathon."
    )
    parser.add_argument(
        "--email_file", type=str, help="The path to the input .eml file to be parsed."
    )

    args = parser.parse_args()

    # Call the parsing function with the provided file path
    print(f"--- Parsing Email File: {args.email_file} ---")
    extracted_text = parse_eml(args.email_file)

    # Print the final extracted text
    print("\n--- Extracted Plain Text Body ---")
    if extracted_text:
        print(extracted_text)
    else:
        print("No plain text body could be extracted.")
    print("\n--- End of a process ---")
