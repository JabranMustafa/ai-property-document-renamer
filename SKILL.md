# Property Document Renaming Skill

## Purpose

This skill identifies, validates, and renames property-related documents according to a configured document taxonomy and standardized naming convention.

The goal is to:

```text
automate clear cases
+
identify uncertain cases
+
avoid incorrect modifications
```

The system must not guess when the available evidence is insufficient.

Documents with ambiguous, unsupported, conflicting, or unsafe results must be sent to manual review.

---

## Expected Naming Convention

Use the format:

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

The original file extension must be preserved.

Examples:

```text
.pdf
.jpg
.jpeg
.png
```

---

## Project Detection

Determine the property project from the folder name.

The current implementation processes MUC property projects.

Examples:

```text
MUC900
→ MUC900

MUC901
→ MUC901
```

A folder containing a recognizable MUC project identifier may also be normalized to the corresponding project code.

Do not invent a project identifier if it cannot be detected reliably.

---

## Document Taxonomy

The configured document taxonomy is the runtime source of truth for supported document categories and terminology.

The taxonomy is stored in:

```text
config/document_types.json
```

Examples of supported document types include:

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

Do not create a new category simply because an unfamiliar term appears in a document.

If the document type is not represented clearly by the configured taxonomy, send the document to review.

---

## Supported Documents

The current implementation supports:

```text
PDF
JPG
JPEG
PNG
```

For PDFs:

```text
first attempt direct text extraction
```

If the PDF contains too little readable text:

```text
use local OCR
```

For image files:

```text
use OCR directly
```

The current implementation uses PyMuPDF for PDF text extraction and Tesseract for OCR.

---

## Document Classification

Use several sources of evidence:

```text
filename
first-page content
full extracted content
configured document taxonomy
```

The filename alone must not be trusted.

The document content alone must also not automatically override a clear filename when evidence conflicts.

Conflicting evidence should result in manual review.

---

## Classification Principles

Strong evidence near the beginning of the document should receive more importance than incidental mentions elsewhere in the document.

This is necessary because property documents frequently mention other document types.

For example, an ETV protocol may mention:

```text
Teilungserklärung
Wirtschaftsplan
Jahresabrechnung
```

These references do not necessarily mean that the document belongs to one of those categories.

The classifier therefore combines multiple evidence sources and uses weighted scoring.

---

## OCR Rules

For searchable PDFs:

```text
PDF
↓
PyMuPDF text extraction
↓
classification
```

For scanned PDFs:

```text
Scanned PDF
↓
render pages as images
↓
Tesseract OCR
↓
classification
```

For image documents:

```text
JPG / PNG
↓
Tesseract OCR
↓
classification
```

OCR should be used as a fallback when normal PDF extraction does not provide enough readable text.

The current prototype uses:

```text
deu+eng
```

for German and English OCR.

---

## Metadata Extraction

When applicable, extract meaningful metadata required for the standardized filename.

Examples include:

```text
year
GBA Blatt number
Energieausweis validity year
Grundriss ALT
WoFlV certificate
```

Only include metadata when it can be identified reliably.

If metadata is uncertain, do not invent it.

---

## Safety Rules

A document must be marked as:

```text
REVIEW
```

instead of being automatically renamed when any of the following occurs:

```text
the document type cannot be identified confidently

multiple document types are detected

the strongest classification scores are too close

the filename and document content disagree

the document type is not represented clearly in the configured taxonomy

multiple files would receive the same target filename

the target filename already exists

document processing fails
```

Never overwrite an existing document.

---

## READY Status

A document may be marked as:

```text
READY
```

when:

```text
the project identifier is valid

the document type is identified confidently

required naming information is available

there is no dangerous filename/content conflict

there is no target filename collision

the proposed target does not overwrite an existing document
```

Only READY documents should be considered for automatic renaming.

---

## Duplicate Handling

Calculate a SHA-256 hash for every supported document.

The hash must represent file contents rather than the filename.

If an identical document has already been processed:

```text
reuse the previous classification when appropriate
```

If the original classification required review:

```text
the duplicate must also remain a review case
```

Duplicates should be recorded separately.

Example output:

```text
MUC900_duplicates.csv
```

---

## Collision Protection

Before renaming, check whether multiple documents would receive the same target filename inside the same directory.

Example:

```text
Document A
→ MUC901 - GBA 2018.pdf

Document B
→ MUC901 - GBA 2018.pdf
```

Both documents must be sent to review.

Do not choose one automatically.

The system must also refuse to overwrite an existing target file.

---

## Dry-Run Requirement

The safest default is:

```python
APPLY_RENAMES = False
```

In dry-run mode:

```text
do not modify files
```

Instead display actions such as:

```text
WOULD RENAME:

Wirtschaftsplan_2024.pdf

->

MUC900 - Wirtschaftsplan 2024.pdf
```

Actual renaming should only occur when explicitly enabled.

---

## Applying Renames

Actual file renaming can be enabled with:

```python
APPLY_RENAMES = True
```

Only documents classified as READY should be renamed.

Documents marked as REVIEW must remain unchanged.

Before every rename:

```text
check target filename
check target path
check for collision
check for existing file
```

---

## Already Correct Files

The workflow may be executed repeatedly.

If a file already has the correct standardized filename, report:

```text
ALREADY CORRECT
```

and leave the file unchanged.

Repeated execution must not create unnecessary rename operations.

---

## Output Reports

For every processed project, generate separate reports.

### Rename Manifest

Example:

```text
MUC900_rename_manifest.csv
```

Contains documents considered safe to rename.

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

Contains documents requiring manual review together with the reason.

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

Contains duplicate files and their matching original documents.

---

## Multi-Project Processing

The system should process multiple MUC property folders from the configured project root.

Example:

```text
PROJECT ROOT
│
├── MUC900
├── MUC901
└── MUC902
```

A single execution may process all discovered MUC projects.

Each project must receive its own independent output reports.

---

## Folder Monitoring

The project includes an automatic watcher.

The watcher monitors the configured property root for:

```text
new PDF files
new JPG files
new JPEG files
new PNG files
new MUC project folders
files moved into monitored folders
```

The watcher should use a short debounce period to group several incoming files into one processing cycle.

For the current prototype, the watcher may trigger the existing multi-project workflow.

A production implementation may instead queue only newly added documents.

---

## Review Philosophy

The goal is not to maximize the percentage of automatically renamed documents.

The priority is:

```text
automate clear cases
+
surface uncertain cases
+
prevent unsafe changes
```

For important company documents, manual review is preferable to an incorrect automatic rename.

Uncertainty must be represented explicitly instead of being hidden.

---

## LLM / Claude Usage

A company-approved Claude environment may be used in the future as a second-stage classifier for difficult documents.

Claude may receive:

```text
extracted document text

known project identifier

approved document taxonomy

approved naming examples
```

Claude should return structured information.

Example:

```json
{
  "project": "MUC900",
  "document_type": "Wirtschaftsplan",
  "year": "2024"
}
```

The LLM must not directly rename files.

Its result must first pass deterministic validation.

Validation should include:

```text
valid project identifier
allowed document type
valid year
valid filename structure
duplicate checks
collision checks
overwrite protection
```

If the result remains uncertain:

```text
send the document to manual review
```

---

## Why the LLM Does Not Control File Operations

An LLM is useful for semantic interpretation.

Deterministic code is better suited for:

```text
filename generation
project validation
duplicate detection
collision detection
overwrite prevention
filesystem operations
audit reporting
```

The semantic layer and the file-operation layer should therefore remain separated.

---

## Microsoft 365 / SharePoint Integration

For production use, the workflow can be connected to a Microsoft 365 environment.

Recommended architecture:

```text
SharePoint Document Library
          ↓
Power Automate Trigger
          ↓
Python Classification Service
          ↓
Optional Claude Fallback
          ↓
Deterministic Validation
          ↓
     High Confidence?
        /        \
      Yes         No
       ↓           ↓
    Rename     Review Queue
       ↓
Microsoft Graph /
SharePoint API
```

Power Automate should handle orchestration.

The Python classification service should remain responsible for:

```text
text extraction
OCR
classification
metadata extraction
naming rules
duplicate detection
validation
collision protection
```

This keeps the document-intelligence logic independently testable.

---

## Production Processing Principle

A possible production workflow is:

```text
New document arrives
        ↓
SharePoint event
        ↓
Power Automate trigger
        ↓
Classification service
        ↓
High confidence?
     /          \
   Yes           No
    ↓             ↓
Validation    Review Queue
    ↓
Rename
    ↓
Audit Log
```

For high-confidence cases, manual interaction should not be required.

Only uncertain cases should enter the review queue.

---

## Privacy

The public/demo version of this project must not contain original confidential property documents.

It must not include:

```text
real property documents

real addresses

personal information

confidential filenames

confidential screenshots

reports generated from confidential documents
```

Testing can be performed using fully synthetic documents containing fictional:

```text
project identifiers

addresses

filenames

contents

metadata
```

OCR runs locally using Tesseract and does not require an external OCR provider.

Documents must not be sent to external services unless those services are explicitly approved for that data.

Confidential production documents must never be committed to the source-code repository.

---

## Synthetic Demo Data

The public/demo workflow may use synthetic projects such as:

```text
MUC900
MUC901
```

The synthetic dataset may contain deliberately difficult scenarios including:

```text
ambiguous documents

unknown document types

scanned PDFs

image documents

duplicate files

filename/content conflicts

target filename collisions
```

These cases are intended to demonstrate the safety behavior of the workflow.

---

## Future Extension

The same workflow can later be extended to determine whether required property documents are complete.

Example:

```text
MUC900

Energieausweis          AVAILABLE
Teilungserklärung       AVAILABLE
Wirtschaftsplan         AVAILABLE
Jahresabrechnung        AVAILABLE
Verwaltervertrag        MISSING
```

The system could automatically generate a completeness report.

This workflow could later run whenever documents are added or changed in SharePoint.

---

## Future Improvements

Possible improvements include:

```text
company-approved Claude fallback

broader configurable taxonomy

semantic document classification

improved OCR quality handling

SharePoint event-based processing

Microsoft Graph integration

review and approval workflows

document completeness checks

missing-document detection

structured audit logging

classification accuracy metrics

precision and review-rate evaluation

manual-correction feedback

queued watcher events

controlled parallel OCR processing

containerized deployment

environment-based configuration

support for additional project prefixes
```

---

## Final Principle

The system should always follow this priority:

```text
correctness
>
automation rate
```

A document should only be renamed automatically when the available evidence is strong enough and all deterministic safety checks pass.

When in doubt:

```text
REVIEW
```