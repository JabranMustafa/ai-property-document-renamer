# AI-Assisted Property Document Renamer

## Overview

This project is a prototype for automatically identifying, validating, and renaming property-related documents according to a standardized naming convention.

Property documents can arrive with:

- inconsistent filenames;
- unclear or meaningless names;
- scanned PDFs;
- image files;
- duplicated documents;
- conflicting document information;
- missing metadata such as year or document type.

The application analyzes both the filename and the document content and proposes a standardized filename.

Example:

```text
Wirtschaftsplan_2024.pdf
```

becomes:

```text
MUC900 - Wirtschaftsplan 2024.pdf
```

The system follows a **safety-first approach**.

Clear classifications are marked as:

```text
READY
```

Uncertain, ambiguous, unsupported, or conflicting documents are marked as:

```text
REVIEW
```

This prevents the system from forcing a potentially incorrect rename.

---

## Main Features

- Automatically discovers multiple MUC property folders.
- Processes documents directly from existing property folders.
- Searches recursively through subfolders.
- Supports PDF, JPG, JPEG, and PNG files.
- Extracts text from searchable PDFs using PyMuPDF.
- Uses local Tesseract OCR for scanned PDFs and image files.
- Uses a configurable document taxonomy.
- Analyzes filenames and document contents.
- Uses first-page content as stronger classification evidence.
- Detects document type.
- Extracts relevant years.
- Extracts selected document details.
- Detects duplicate files using SHA-256.
- Reuses classification results for identical duplicate files.
- Detects ambiguous classifications.
- Detects filename/content conflicts.
- Detects multiple possible document types.
- Detects proposed filename collisions.
- Prevents accidental overwriting.
- Supports dry-run mode.
- Supports actual renaming mode.
- Creates separate reports for every property project.
- Supports automatic folder monitoring with `watchdog`.

---

## Example Naming Convention

The general naming convention is:

```text
PROJECT - Document Type [Year / Detail]
```

Examples:

```text
MUC900 - Wirtschaftsplan 2024.pdf
MUC900 - Jahresabrechnung 2023.pdf
MUC900 - ETV-Protokoll 2024.pdf
MUC900 - Energieausweis bis 2028.pdf
MUC900 - GBA Blatt 3502.pdf
MUC900 - Grundriss ALT.pdf
MUC900 - Zertifikat WoFlV.pdf
```

The project identifier is detected automatically from the folder name.

For example:

```text
MUC900/
```

results in filenames beginning with:

```text
MUC900 -
```

---

## Project Structure

```text
DocumentRename/
│
├── config/
│   └── document_types.json
│
├── output/
│   └── generated CSV reports
│
├── src/
│   ├── main.py
│   ├── classifier.py
│   └── watcher.py
│
├── README.md
├── SKILL.md
├── requirements.txt
└── .gitignore
```

The application does not require a separate `input/` folder.

The runtime classifier also does not require local reference-document folders.

Documents are processed directly from the configured property-project directory.

---

## Synthetic Demo Dataset

For demonstration and testing, the project can be used with a completely synthetic dataset.

Example:

```text
_Task Example AI-Student/
│
├── MUC900/
└── MUC901/
```

The synthetic dataset contains fictional:

- project identifiers;
- addresses;
- filenames;
- PDF contents;
- image contents;
- metadata;
- document scenarios.

It is designed to test the same engineering problems as a real document workflow without publishing confidential property data.

The test dataset includes examples of:

- normal documents;
- scanned PDFs;
- image documents;
- duplicates;
- ambiguous classifications;
- filename/content conflicts;
- unsupported document types;
- proposed filename collisions.

---

## Requirements

Python 3.11 or newer is recommended.

### Python Dependencies

The main dependencies are:

```text
PyMuPDF
pytesseract
Pillow
watchdog
```

Install them using:

```bash
pip install -r requirements.txt
```

---

## Tesseract OCR

Tesseract OCR must also be installed locally.

The current Windows prototype uses:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

German OCR language support should also be installed.

The classifier currently uses:

```text
deu+eng
```

This allows OCR to recognize both German and English text.

---

## Configuration

The project root containing the property folders is configured in:

```text
src/main.py
```

Example:

```python
PROJECTS_ROOT = Path(
    r"C:\Users\YourName\Documents\PropertyProjects"
)
```

A possible project structure is:

```text
PropertyProjects/
│
├── MUC900/
├── MUC901/
└── MUC902/
```

The current prototype automatically discovers folders whose names contain a valid MUC project identifier.

---

## Document Taxonomy

The runtime document taxonomy is stored in:

```text
config/document_types.json
```

It defines supported document categories and associated terminology.

Examples include:

```text
Wirtschaftsplan
Jahresabrechnung
Einzelwirtschaftsplan
Gesamtwirtschaftsplan
ETV-Protokoll
Energieausweis
Teilungserklärung
Grundriss
Aufteilungsplan
Baubeschreibung
Flurkarte
GBA
Hausordnung
Versicherungspolice
Wohngebäudeversicherung
Beschlusssammlung
WEG-Beschlüsse
Vermögensbericht
Rücklagenentwicklung
WoFlV
```

The taxonomy can be extended without changing the main processing pipeline.

Additional document types or terminology can be added to the configuration as the system evolves.

---

## Supported File Types

The current prototype supports:

```text
.pdf
.jpg
.jpeg
.png
```

Searchable PDFs are processed directly.

Scanned PDFs automatically use OCR when too little readable text can be extracted.

JPG, JPEG, and PNG documents are processed using OCR.

---

## How Classification Works

The application combines multiple sources of evidence instead of trusting only the filename.

The general flow is:

```text
Document
   ↓
Detect file type
   ↓
Extract text
   ↓
Is enough readable text available?
   │
   ├── Yes → use extracted text
   │
   └── No  → local OCR
   ↓
Analyze filename
   +
Analyze first-page content
   +
Analyze full document content
   ↓
Calculate document-type scores
   ↓
Extract year/details
   ↓
Run safety checks
   ↓
READY or REVIEW
```

Different sources of evidence receive different weights.

Filename matches are useful because filenames often contain important terminology.

First-page content receives strong weight because document titles frequently appear near the beginning.

Mentions elsewhere in the document receive lower weight because property documents may reference other document types.

For example, an ETV protocol may mention a Teilungserklärung without actually being a Teilungserklärung.

This is why classification is based on combined evidence rather than a simple keyword search.

---

## OCR Workflow

### Searchable PDF

```text
PDF
 ↓
PyMuPDF text extraction
 ↓
Classification
```

### Scanned PDF

```text
Scanned PDF
 ↓
Render PDF page as image
 ↓
Tesseract OCR
 ↓
Classification
```

### Image Document

```text
JPG / PNG
 ↓
Tesseract OCR
 ↓
Classification
```

OCR is used only when necessary.

For scanned PDFs, the current prototype processes only the first few pages because document titles and identifying information usually appear near the beginning.

This keeps processing time reasonable.

---

## Safety-First Design

The application prefers manual review over an unsafe automatic rename.

A document can be sent to `REVIEW` when:

- the document type cannot be identified confidently;
- multiple document types are detected;
- the strongest classification scores are too close;
- the filename and document content disagree;
- the type is not confidently represented in the configured taxonomy;
- multiple files would receive the same target filename;
- processing produces an error.

This means that a lower automatic rename rate can be acceptable when the alternative would be making incorrect changes to documents.

---

## READY vs REVIEW

### READY

Example:

```text
Original:
Wirtschaftsplan_2024.pdf

Detected:
Wirtschaftsplan

Year:
2024

Proposed:
MUC900 - Wirtschaftsplan 2024.pdf

Status:
READY
```

### REVIEW

Example:

```text
Original:
Abrechnung_2021.pdf

Scores:
Jahresabrechnung = 17
Einzelwirtschaftsplan = 17

Status:
REVIEW

Reason:
Ambiguous classification.
```

The application does not automatically rename uncertain documents.

---

## Dry-Run Mode

The safest way to test the application is with:

```python
APPLY_RENAMES = False
```

In this mode, files are not changed.

Instead, the application displays the proposed actions.

Example:

```text
WOULD RENAME:

Wirtschaftsplan_2024.pdf

->

MUC900 - Wirtschaftsplan 2024.pdf
```

This allows results to be reviewed before enabling actual file operations.

---

## Applying Renames

After reviewing the results, actual renaming can be enabled using:

```python
APPLY_RENAMES = True
```

Only documents that pass the safety checks are automatically renamed.

Files marked as `REVIEW` remain unchanged.

The application also checks whether the target filename already exists before performing the rename.

---

## Already Correct Files

The application can safely be executed multiple times.

If a document already has the standardized filename, it is detected as already correct.

Example:

```text
ALREADY CORRECT
```

The file is left unchanged.

This allows new documents to be added later without repeatedly modifying previously processed documents.

---

## Duplicate Detection

Every supported document receives a SHA-256 hash.

The hash represents the actual file contents rather than the filename.

For example:

```text
document1.pdf
copy_of_document.pdf
```

can still be recognized as duplicates when their contents are identical.

When an identical document has already been classified, the system can reuse the existing classification instead of repeating OCR and classification work.

Duplicate information is written to:

```text
MUCXXX_duplicates.csv
```

---

## Collision Protection

Before files are renamed, the system checks whether multiple documents would receive the same target filename.

Example:

```text
Document A
→ MUC901 - GBA 2018.pdf

Document B
→ MUC901 - GBA 2018.pdf
```

Because both documents would receive the same target filename, neither is automatically renamed.

Instead, both are sent to the review queue.

The application also refuses to overwrite an existing target file.

---

## Output Reports

Three project-specific reports are generated.

### Rename Manifest

Example:

```text
MUC900_rename_manifest.csv
```

This contains documents that passed the automatic safety checks.

Typical fields include:

```text
original_file
document_type
year
proposed_filename
ocr_used
```

---

### Problem Cases

Example:

```text
MUC901_problem_cases.csv
```

This contains documents requiring manual review.

The report includes the reason why the document was not accepted automatically.

Example reasons:

```text
Could not identify document confidently.

Filename and document content suggest different document types.

Ambiguous classification:
Jahresabrechnung=17,
Einzelwirtschaftsplan=17.

Multiple files would be renamed to the same target filename inside the same folder.
```

---

### Duplicate Report

Example:

```text
MUC900_duplicates.csv
```

This records duplicate documents together with the path of the matching file.

---

## Multi-Project Processing

The application does not require a project to be selected manually for each execution.

It scans the configured parent directory and discovers available MUC property projects.

Example:

```text
PROJECT ROOT
│
├── MUC900/
├── MUC901/
└── MUC902/
```

One execution can therefore process all discovered projects and generate independent reports for each.

This makes the architecture more suitable for a larger document-management workflow rather than being hardcoded to one property.

---

## Automatic Folder Monitoring

The project also includes a folder watcher:

```text
src/watcher.py
```

The watcher uses the Python `watchdog` package.

It monitors the configured project root for:

- newly created MUC folders;
- new PDF files;
- new JPG files;
- new JPEG files;
- new PNG files;
- files moved into the monitored directory.

The watcher uses a short debounce period so that several files copied at approximately the same time can trigger a single processing run instead of repeatedly starting the workflow.

Run the watcher with:

```bash
cd src
python watcher.py
```

The watcher can then remain active and react when new documents are added.

For the current prototype, the watcher triggers the existing processing workflow.

A future production version could send only the newly added files into a queue instead of rescanning all projects.

---

## Running the Application

Because the current configuration path is relative to the `src` directory, run the application from `src`.

From the project root:

```bash
cd src
```

Then run:

```bash
python main.py
```

The application will:

```text
1. Locate the configured project root.
2. Discover MUC property folders.
3. Search for supported documents recursively.
4. Calculate file hashes.
5. Detect duplicates.
6. Extract document text.
7. Apply OCR when necessary.
8. Classify documents.
9. Extract year and relevant details.
10. Perform safety checks.
11. Detect target filename collisions.
12. Generate project-specific reports.
13. Display dry-run or actual rename actions.
```

---

## Synthetic Validation

The public/demo version can be validated using two synthetic projects:

```text
MUC900
MUC901
```

### MUC900

This project contains relatively clear examples together with:

- normal PDFs;
- scanned PDFs;
- JPG and PNG files;
- duplicate documents;
- unsupported document examples;
- a multi-type ambiguous document.

It demonstrates the normal classification and duplicate-detection workflow.

### MUC901

This project intentionally contains more difficult cases, including:

- ambiguous classifications;
- filename/content conflicts;
- unknown document types;
- collision cases;
- image documents;
- scanned documents.

The purpose of this project is to validate that the safety layer correctly sends uncertain documents to `REVIEW`.

The goal is not to achieve a 100% automatic rename rate.

The goal is to automate clear cases while preventing unsafe renames.

---

## Why Python Is Used for the Core Logic

The prototype separates document intelligence from workflow orchestration.

Python handles:

```text
text extraction
OCR
classification
year extraction
detail extraction
naming logic
duplicate detection
validation
collision detection
report generation
filesystem operations
```

This keeps the core logic testable and independent from a specific automation platform.

A workflow platform can later handle orchestration.

Examples include:

```text
Power Automate
n8n
```

A future flow could look like:

```text
New document arrives
        ↓
Workflow trigger
        ↓
Python classification service
        ↓
Structured result
        ↓
Rename or Review
```

---

## Why an LLM Does Not Directly Rename Files

An LLM could be useful for understanding difficult or previously unseen documents.

However, deterministic logic is better suited for operations such as:

```text
validating project codes
enforcing filename formats
detecting duplicates
preventing overwrites
checking target collisions
performing filesystem operations
```

For this reason, a future LLM component would act as an additional semantic-classification layer.

It would not receive unrestricted control over document renaming.

All LLM-generated classifications should still pass through deterministic validation before any file operation occurs.

---

## Possible Claude Integration

Claude could be added as a second-stage classifier for difficult documents.

A possible workflow is:

```text
Document
   ↓
Python classifier
   ↓
High confidence?
   │
   ├── Yes
   │    ↓
   │  Validation
   │    ↓
   │  Rename
   │
   └── No
        ↓
Company-approved Claude
        ↓
Structured classification
        ↓
Deterministic validation
        ↓
Rename or Human Review
```

Claude could receive:

- the approved document taxonomy;
- extracted document text;
- expected naming rules;
- permitted output fields.

A structured output could look like:

```json
{
  "project": "MUC900",
  "document_type": "Wirtschaftsplan",
  "year": "2024"
}
```

Python would then validate the response before permitting a rename.

---

## Microsoft 365 / SharePoint Integration

The same classification engine could later be integrated into a Microsoft 365 environment.

A possible production architecture is:

```text
SharePoint Document Library
          ↓
Power Automate Trigger
          ↓
Python Classification Service
          ↓
Optional LLM Fallback
          ↓
Deterministic Validation
          ↓
   ┌───────────────┐
   │               │
High Confidence   Uncertain
   │               │
   ↓               ↓
Rename         Review Queue
   │
   ↓
Audit Log
```

Power Automate would be a natural orchestration layer in an environment already using Microsoft 365 and SharePoint.

The Python classification engine could run as:

- an internal API;
- an Azure Function;
- a containerized service;
- another approved backend service.

Microsoft Graph or SharePoint APIs could perform the final filename update.

---

## Future Improvements

Possible future improvements include:

- company-approved LLM fallback for difficult documents;
- broader configurable document taxonomy;
- improved semantic classification;
- more advanced OCR quality checks;
- SharePoint event-based processing;
- Microsoft Graph integration;
- a SharePoint review queue;
- approval workflow for uncertain documents;
- document completeness checks;
- missing-document detection;
- structured audit logging;
- classification accuracy metrics;
- precision and review-rate measurement;
- evaluation against a manually labeled dataset;
- feedback from approved manual corrections;
- queued event processing;
- controlled parallel OCR processing;
- containerized deployment;
- configurable project categories beyond MUC;
- environment-based configuration;
- removal of machine-specific paths.

---

## Privacy and Confidentiality

The public/demo version of this project does **not** contain original property documents, personal information, real property addresses, or confidential source data.

Testing can be performed using a fully synthetic dataset containing fictional:

- project identifiers;
- addresses;
- document contents;
- filenames;
- metadata.

OCR runs locally using Tesseract.

The current implementation therefore does not require an external OCR provider.

Any future cloud or LLM integration should use only approved services and follow the applicable organizational and data-protection requirements.

Confidential production documents should never be committed to the source-code repository.

---

## Recommended `.gitignore`

Sensitive, generated, and environment-specific files should not be committed.

Example:

```gitignore
# Virtual environment
.venv/

# Python cache
__pycache__/
*.pyc

# Generated reports
output/

# Local document folders
input/
reference/

# Property documents
*.pdf
*.jpg
*.jpeg
*.png

# Environment variables
.env
```

---

## Design Philosophy

The goal of this project is not to automatically rename every possible document.

The priority is:

```text
Automate clear cases
        +
Identify uncertain cases
        +
Prevent incorrect changes
```

A wrong filename can create downstream problems in document search, due diligence, auditing, and property operations.

For that reason, uncertainty is explicitly represented instead of being hidden.

---

## Development Scope

The prototype covers:

- understanding the property-document workflow;
- creating a configurable document taxonomy;
- PDF text extraction;
- OCR fallback;
- image support;
- document classification;
- year and detail extraction;
- duplicate detection;
- ambiguity detection;
- filename/content conflict detection;
- filename collision protection;
- dry-run mode;
- actual rename functionality;
- multi-project processing;
- CSV reporting;
- automatic folder monitoring;
- synthetic validation;
- production architecture planning.

---

## Summary

This project demonstrates a safety-first document-intelligence and automation pipeline for property-document renaming.

The current implementation can:

- process multiple property folders;
- extract text from PDFs;
- OCR scanned documents and images;
- classify common document types;
- generate standardized filenames;
- detect duplicates;
- detect ambiguous classifications;
- identify filename/content conflicts;
- prevent target-name collisions;
- generate audit reports;
- automatically monitor folders for new documents.

The architecture deliberately separates deterministic file operations from semantic document understanding.

This makes it possible to extend the same system with Claude, Power Automate, Microsoft 365, SharePoint, or other workflow tools while keeping validation and file operations predictable and controlled.