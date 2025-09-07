# Roster Email Parser

**Team Members:**

- Anvit Gupta (anvit_g@cs.iitr.ac.in)
- Raman Sharma (raman_s@cs.iitr.ac.in)
- Tamakuwala Vraj Shailesh (tamakuwala_vs@cs.iitr.ac.in)

**Repository:** [https://github.com/vraj-tvs/Roster-Email-Parser](https://github.com/vraj-tvs/Roster-Email-Parser)

---

## Overview

This project automates the extraction, normalization, and tabulation of provider roster information from `.eml` email files. The pipeline processes emails, extracts structured data, normalizes it, and generates Excel outputs for downstream use.
This project is part of **_HiLabs Hackathon 2025: Free-Text Roster Emails_**.

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

## Approach & Pipeline

The solution is modular, with each stage encapsulated in a dedicated Python module:

1. **Parsing:** Extracts the plain text body from `.eml` files using robust email parsing.

2. **Preprocessing:** Cleans and standardizes the extracted text, removing artifacts and normalizing whitespace.

3. **Extraction:** Uses regex and spaCy NLP to extract provider details (NPI, name, specialty, address, etc.) and business attributes.

4. **Normalization:** Applies rules to standardize formats (dates, names, IDs) and ensures consistent output.

5. **Excel Generation:** Outputs the normalized data to `.xlsx` files, matching a predefined template.

6. **Logging:** Logs pipeline progress and errors to `data/logs/pipeline.log`.

---

#### NLP Model: en_core_web_trf

This project leverages the **spaCy** transformer-based pretrained model, `en_core_web_trf`, for advanced Natural Language Processing (NLP) tasks. This model is built on top of transformer architectures (such as BERT or RoBERTa), providing state-of-the-art accuracy for Named Entity Recognition (NER) and other language understanding tasks.

##### Core Idea & Use Case in the Project

- **Purpose:** The `en_core_web_trf` model is used to extract structured information from unstructured email text, specifically when rule-based or regex extraction is insufficient or ambiguous.

- **How It Works:** After initial regex-based extraction, the model is applied to the email text to identify entities such as:

  - PERSON (for provider names)
  - ORG (for organization names, e.g., "Mercian Medical Group")

- **Why Use It:** Emails often contain provider and organization names in varied formats. The transformer model can robustly identify these entities even when the text is noisy or inconsistent, improving extraction accuracy and reducing manual intervention.

- **Integration:** The model is loaded once at the start of the pipeline (`spacy.load("en_core_web_trf")` in `extractor.py`).  
  It is used as a fallback in the extraction logic to ensure that critical fields like provider and organization names are reliably captured.

##### Benefits

- **High Accuracy:** Transformer models outperform traditional rule-based approaches for NER.
- **Robustness:** Handles diverse and messy email formats.
- **Scalability:** Enables automated extraction across large volumes of emails with minimal errors.

**Note:** To use this model, ensure you have run:

```
python -m spacy download en_core_web_trf
```

or installed via `requirements.txt`.

---

## Instructions to Run

1. **Create and Initialize virtual environment (Optional)**

   ```
   # On Windows
   python -m venv myenv
   myenv\Scripts\activate

   # On Linux/macOS
   python3 -m venv myenv
   source myenv/bin/activate
   ```

2. **Install Dependencies**

   ```
   # On Windows
   pip install -r requirements.txt

   # On Linux/macOS
   python3 -m pip install -r requirements.txt
   ```

   This will install all required packages, including:

   - `spacy`, `en-core-web-trf` (NLP)
   - `openpyxl`, `pandas`, `numpy`, `tqdm`, `python-dateutil`
   - `beautifulsoup4` and `lxml` (for email and HTML parsing)

   _NOTE:_ If you have multiple Python versions installed, use:

   ```
   # On Windows
   python -m pip install -r requirements.txt

   # On Linux/macOS
   python3 -m pip install -r requirements.txt
   ```

   If you see errors about missing `en_core_web_trf`, run:

   ```
   # On Windows
   python -m spacy download en_core_web_trf

   # On Linux/macOS
   python3 -m spacy download en_core_web_trf
   ```

3. **Prepare Input**

   - Place the `.eml` files in `data/input/` folder.

4. **Run the pipeline**

   - For single file:

   ```
   # On Windows
   python runner.py --input_file=data/input/Sample-1.eml

   # On Linux/macOS
   python3 runner.py --input_file=data/input/Sample-1.eml
   ```

   - For a folder of `.eml` files:

   ```
   # On Windows
   python runner.py --input_folder=data/input/

   # On Linux/macOS
   python3 runner.py --input_folder=data/input/
   ```

5. **Output**
   - Excel files are saved in `data/output` folder.
   - Logs are available in `data/logs/pipeline.log`.

---

## Turnaround Time (TAT) Analysis

- The pipeline logs TAT for each processed file and computes total and average TAT.
- See the summary at the end of `data/logs/pipeline.log` for detailed timing statistics.

  - TAT analysis for given 3 sample `.eml` files
    | File | TAT (seconds) | Output |
    |-----------------|---------------|------------------|
    | Sample-1.eml | 1.14 | Sample-1.xlsx |
    | Sample-2.eml | 0.51 | Sample-2.xlsx |
    | Sample-3.eml | 0.17 | Sample-3.xlsx |

    - Total files processed: 3
    - Total TAT: 1.82 seconds
    - Average TAT per file: 0.61 seconds

---
