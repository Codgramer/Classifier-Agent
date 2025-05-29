# DocumentProcessor

A Python-based system for processing and classifying documents (emails, PDFs, JSON invoices) to identify their intent (e.g., Request for Quote, Invoice, Complaint) and extract relevant information. The system uses heuristic-based classification and regex-based extraction, storing results in a JSON log file (`memory_log.json`) for persistence.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Input Files](#input-files)
- [Usage](#usage)
- [Output](#output)
- [Extending the Project](#extending-the-project)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Overview

DocumentProcessor is designed to automate the analysis of business documents. It processes input files in email (`.txt`), PDF (`.pdf`), and JSON (`.json`) formats, classifies their intent (e.g., RFQ, Invoice, Complaint, Regulation, Other), and extracts key information based on the intent. The system uses a modular architecture with three agents:
- **ClassifierAgent**: Determines the file format and intent, routing to appropriate processing agents.
- **EmailAgent**: Handles text-based inputs (emails, PDFs) and extracts intent-specific fields using regex.
- **JSONAgent**: Processes JSON invoices, extracting structured data (e.g., invoice number, total).

Results are stored in an in-memory dictionary (`memory`) and persisted to `memory_log.json`. The system is built with Python and uses `pdfplumber` for PDF text extraction and standard libraries for other operations.

## Features
- Supports multiple file formats: email (`.txt`), PDF (`.pdf`), JSON (`.json`).
- Intent classification: RFQ, Invoice, Complaint, Regulation, Other.
- Extracts intent-specific fields:
  - **RFQ**: Quantity, product.
  - **Invoice**: Invoice number, date, total, currency.
  - **Complaint**: Order ID, issue description.
  - **Other**: Name, email, phone, summary.
- Logs processing steps and errors for debugging.
- Persists results to `memory_log.json` for analysis.
- Handles errors gracefully with fallback classification (`Other`).

## Requirements
- **Python**: 3.7 or higher.
- **Dependencies**:
  - `pdfplumber`: For PDF text extraction.
- **Operating System**: Tested on Windows (paths use `C:\Users\Himanshu\Downloads\`).

## Installation

1. **Clone or Download the Project**:
   - Save `agent.py` to `C:\Users\Himanshu\Downloads\`.
   - Ensure input files (see [Input Files](#input-files)) are in the same directory.

2. **Install Python**:
   - Download and install Python from [python.org](https://www.python.org/downloads/).
   - Verify installation:
     ```bash
     python --version
     ```

3. **Install Dependencies**:
   - Install `pdfplumber`:
     ```bash
     pip install pdfplumber
     ```

4. **Verify Setup**:
   - Ensure `agent.py` and input files are in `C:\Users\Himanshu\Downloads\`.
   - Check that Python and `pdfplumber` are installed.

## Project Structure

```
C:\Users\Himanshu\Downloads\
├── agent.py                # Main script with processing logic
├── email_rfq.txt           # Sample email input (RFQ)
├── email_complaint.txt     # Sample email input (Complaint)
├── sales_invoice.json      # Sample JSON invoice
├── service_invoice.json    # Sample JSON invoice
├── complaint1.pdf          # Sample PDF complaint
├── complaint2.pdf          # Sample PDF complaint
├── equipment_invoice.json  # Optional JSON invoice
├── memory_log.json         # Output log file (generated)
└── README.md               # This file
```

## Input Files

The script processes the following input files (place in `C:\Users\Himanshu\Downloads\`):

1. **email_rfq.txt**:
   - Format: Plain text.
   - Content: Request for Quote (e.g., "Urgent RFQ...250 units of Product Widget").
   - Expected Intent: RFQ.

2. **email_complaint.txt**:
   - Format: Plain text.
   - Content: Complaint (e.g., "Complaint - Damaged Order #98765...").
   - Expected Intent: Complaint.

3. **sales_invoice.json**:
   - Format: JSON.
   - Content: Invoice with `DocDtls.Typ: "INV"`, `DocDtls.No`, `ValDtls.TotInvVal`, etc.
   - Expected Intent: Invoice.

4. **service_invoice.json**:
   - Format: JSON.
   - Content: Similar to `sales_invoice.json` (e.g., invoice number `SERV2025-007`).
   - Expected Intent: Invoice.

5. **complaint1.pdf**:
   - Format: PDF (or `.txt` for testing).
   - Content: Complaint (e.g., "Order #45678...damaged during shipping").
   - Expected Intent: Complaint.

6. **complaint2.pdf**:
   - Format: PDF (or `.txt` for testing).
   - Content: Complaint (e.g., "Order #12345...defective").
   - Expected Intent: Complaint.

7. **equipment_invoice.json** (Optional):
   - Format: JSON.
   - Content: Invoice (e.g., `EQUIP-2025-009`, total 1770 INR).
   - Expected Intent: Invoice.

### JSON File Schema
JSON invoices must include:
```json
{
  "DocDtls": {
    "Typ": "INV",
    "No": "<invoice_number>",
    "Dt": "<date>"
  },
  "ValDtls": {
    "TotInvVal": <total_amount>,
    "CgstVal": <cgst_amount>
  },
  "ItemList": [
    {
      "PrdDesc": "<product_description>",
      "Qty": <quantity>,
      "UnitPrice": <price>,
      "TotAmt": <total>
    }
  ]
}
```

## Usage

1. **Prepare Input Files**:
   - Ensure all input files are in `C:\Users\Himanshu\Downloads\`.
   - Verify JSON files match the required schema.
   - Convert PDFs to `.txt` if `pdfplumber` is not installed (for testing).

2. **Run the Script**:
   - Open Command Prompt.
   - Navigate to the project directory:
     ```bash
     cd C:\Users\Himanshu\Downloads
     ```
   - Execute:
     ```bash
     python agent.py
     ```

3. **Add New Files** (e.g., `equipment_invoice.json`):
   - Save the new file in `C:\Users\Himanshu\Downloads\`.
   - Update the `inputs` list in `agent.py`:
     ```python
     {
         'format': 'json',
         'file_path': r"C:\Users\Himanshu\Downloads\equipment_invoice.json",
         'sender': 'system@example.com',
         'thread_id': 'thread_901',
         'timestamp': datetime.datetime.now().isoformat()
     }
     ```

4. **Check Output**:
   - **Console Logs**: Display processing steps, intent classification, and extracted values.
   - **memory_log.json**: Contains processed data for each thread (e.g., `thread_123`, `thread_456`).
     ```json
     {
       "thread_123": {
         "extracted_values": {
           "product": "Widget",
           "quantity": 250,
           "sender": "john.doe@example.com",
           "urgency": "high"
         },
         "intent": "RFQ",
         ...
       },
       ...
     }
     ```

## Output

The script generates `memory_log.json` with entries for each processed file, including:
- **source**: Sender (e.g., `john.doe@example.com`).
- **type**: Format (`email`, `pdf`, `json`).
- **timestamp**: Processing time.
- **file_path**: Input file path.
- **intent**: Classified intent (RFQ, Invoice, Complaint, etc.).
- **extracted_values**: Intent-specific fields.
- **logs**: Processing steps and errors.

Example entry for `service_invoice.json`:
```json
{
  "thread_457": {
    "extracted_values": {
      "invoice_number": "SERV2025-007",
      "date": "2025-05-28",
      "total": 1180,
      "currency": "INR"
    },
    "intent": "Invoice",
    "logs": [
      "Classifier: Detected json from C:\\Users\\Himanshu\\Downloads\\service_invoice.json",
      "Classifier: Classified intent as Invoice",
      "JSON Agent: Extracted values; Anomalies: []"
    ],
    ...
  }
}
```

## Extending the Project

1. **Add New Intents**:
   - Modify `classify_intent` to detect new keywords (e.g., `'order' in content_lower` for Orders).
   - Update `extract_from_text` and `JSONAgent.process_json` to extract relevant fields.

2. **Support New Formats**:
   - Extend `read_file_content` to handle formats like XML or CSV.
   - Update `ClassifierAgent.process_input` to route to new agents.

3. **Improve Extraction**:
   - Enhance regex patterns in `extract_from_text` for better accuracy.
   - Use NLP libraries (e.g., `spacy`) for advanced text analysis.

4. **Add Database Storage**:
   - Replace `memory_log.json` with a database (e.g., SQLite) for scalability.

5. **Error Handling**:
   - Add validation for input file formats and content.
   - Implement retry mechanisms for failed extractions.

## Troubleshooting

- **File Not Found**:
  - Ensure input files are in `C:\Users\Himanshu\Downloads\`.
  - Check file paths in `agent.py` `inputs` list.

- **JSON Extraction Issues** (e.g., `N/A` values):
  - Verify JSON files match the required schema.
  - Check `sales_invoice.json` content (see [Input Files](#input-files)).
  - Enable debug logging in `agent.py`:
    ```python
    logging.basicConfig(level=logging.DEBUG, ...)
    ```

- **PDF Errors**:
  - Install `pdfplumber` (`pip install pdfplumber`).
  - Use `.txt` files for testing if PDFs fail.

- **No Output in `memory_log.json`**:
  - Check console logs for errors.
  - Ensure `save_memory_to_file` is called (verify `agent.py`).

For further assistance, share console output or file contents.

## License

This project is unlicensed and provided as-is for educational purposes. Feel free to modify and distribute.

---

**Last Updated**: May 29, 2025