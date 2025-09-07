# Roster Email Parser

**Repository:** [https://github.com/vraj-tvs/Roster-Email-Parser](https://github.com/vraj-tvs/Roster-Email-Parser)

---

## Overview

This project automates the extraction, normalization, and tabulation of provider roster information from `.eml` email files. The pipeline processes emails, extracts structured data, normalizes it, and generates Excel outputs for downstream use.
This project is part of **_HiLabs Hackathon 2025: Free-Text Roster Emails_**.

---

## Approach & Pipeline

The solution is modular, with each stage encapsulated in a dedicated Python module:

1. **Parsing:** Extracts the plain text body from `.eml` files using robust email parsing.

2. **Preprocessing:** Cleans and standardizes the extracted text, removing artifacts and normalizing whitespace.

3. **Extraction:** Uses regex and spaCy NLP to extract provider details (NPI, name, specialty, address, etc.) and business attributes.

4. **Normalization:** Applies rules to standardize formats (dates, names, IDs) and ensures consistent output.

5. **Excel Generation:** Outputs the normalized data to `.xlsx` files, matching a predefined template.

6. **Logging:** Logs pipeline progress and errors to `data/logs/pipeline.log`.

**_NOTE:_** Current version doesn't supports tabular data in `.eml` files well.

---

## Directory Structure

    Roster-Email-Parser/
    ├── data/
    │   ├── input/           # Place .eml files here
    │   ├── output/          # Excel output files
    │   └── logs/            # Pipeline logs
    ├── src/
    │   ├── parser.py
    │   ├── preprocessor.py
    │   ├── extractor.py
    │   ├── normalizer.py
    │   └── excel_generator.py
    ├── utils/
    │   └── logger.py
    ├── runner.py
    ├── requirements.txt
    └── README.md

---

## Instructions to Run

1. **Create and Initialize virtual environment (Optional)**
    ```
   python -m venv myenv
   myenv\Scripts\activate  # On Windows
   source myenv/bin/activate  # On Linux
   ```

2. **Install Dependencies**
   ```
   pip install -r requirements.txt
   python -m spacy download en_core_web_trf  # if not installed from `requirements.txt`
   ```
   **_NOTE:_** if you have multiple Python versions installed, then use:
   ```
   python -m pip install -r requirements.txt
   ```

3. **Prepare Input**
   - Place the `.eml` files in `data/input/` folder.

4. **Run the pipeline**
   - For single file:
   ```
   python runner.py --input_file=data/input/Sample-1.eml
   ```
   - For a folder of `.eml` files:
    ```
    python runner.py --input_folder=data/input/
    ```

5. **Output**
    - Excel files are saved in `data/output` folder.
    - Logs are available in `data/logs/pipeline.log`.

---

## Turnaround Time (TAT) Analysis

- The pipeline logs TAT for each processed file and computes total and average TAT.
- See the summary at the end of `data/logs/pipeline.log` for detailed timing statistics.

    - TAT analysis for given 3 sample `.eml` files
        | File            | TAT (seconds) | Output           |
        |-----------------|---------------|------------------|
        | Sample-2.eml    | 0.41          | Sample-2.xlsx    |
        | Sample-1.eml    | 0.77          | Sample-1.xlsx    |
        | Sample-3.eml    | 0.14          | Sample-3.xlsx    |

        - Total files processed: 3
        - Total TAT: 1.32 seconds
        - Average TAT per file: 0.44 seconds 

---