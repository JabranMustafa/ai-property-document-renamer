import json
import re
import io
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
# --------------------------------------------------
# LOAD DOCUMENT TYPE CONFIG
# --------------------------------------------------

config_path = Path("../config/document_types.json")

with open(config_path, "r", encoding="utf-8") as file:
    document_types = json.load(file)


# --------------------------------------------------
# EXTRACT PDF CONTENT
# --------------------------------------------------

def extract_pdf_content(pdf_path):

    document = pymupdf.open(pdf_path)

    full_text = ""
    first_page_text = ""

    # --------------------------------------------------
    # 1. TRY NORMAL PDF TEXT EXTRACTION FIRST
    # --------------------------------------------------

    for page_number, page in enumerate(document):

        page_text = page.get_text()

        full_text += page_text + "\n"

        if page_number == 0:
            first_page_text = page_text


    # --------------------------------------------------
    # 2. CHECK IF TEXT QUALITY IS GOOD ENOUGH
    # --------------------------------------------------

    extracted_characters = len(full_text.strip())

    used_ocr = False


    # If almost no useful text exists,
    # treat document as scanned.
    if extracted_characters < 150:

        used_ocr = True

        print("OCR fallback activated:", pdf_path.name)

        ocr_text = ""
        ocr_first_page = ""

        # OCR only first 3 pages for classification
        pages_to_ocr = min(3, len(document))

        for page_number in range(pages_to_ocr):

            page = document[page_number]

            # Render PDF page as image
            pix = page.get_pixmap(
                matrix=pymupdf.Matrix(2, 2),
                alpha=False
            )

            image_bytes = pix.tobytes("png")

            image = Image.open(
                io.BytesIO(image_bytes)
            )

            # German + English OCR
            page_ocr_text = pytesseract.image_to_string(
                image,
                lang="deu+eng"
            )

            ocr_text += page_ocr_text + "\n"

            if page_number == 0:
                ocr_first_page = page_ocr_text


        full_text = ocr_text
        first_page_text = ocr_first_page


    return first_page_text, full_text, used_ocr

def normalize_text(text):

    text = text.lower()

    # Treat separators as spaces
    text = text.replace("_", " ")
    text = text.replace("-", " ")
    text = text.replace("+", " ")

    # Remove repeated spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# --------------------------------------------------
# HELPER FOR KEYWORD MATCHING
# --------------------------------------------------

def keyword_exists(text, keyword):

    text_lower = text.lower()
    keyword_lower = keyword.lower()

    # Short abbreviations like GBA should only match
    # as separate words, not inside another word.
    if len(keyword_lower) <= 3:

        pattern = (
            r"(?<!\w)"
            + re.escape(keyword_lower)
            + r"(?!\w)"
        )

        return re.search(
            pattern,
            text_lower
        ) is not None

    return keyword_lower in text_lower


# --------------------------------------------------
# DOCUMENT CLASSIFICATION
# --------------------------------------------------

def detect_document_type(
    filename,
    first_page_text,
    full_text
):
    filename_lower = normalize_text(filename)
    first_page_lower = normalize_text(first_page_text)
    full_text_lower = normalize_text(full_text)

    scores = {}

    # --------------------------------------------------
    # SPECIAL CASE: MULTIPLE DOCUMENT TYPES IN ONE FILE
    # --------------------------------------------------

    normalized_filename = normalize_text(filename)

    has_wp = (
        "wp2024" in filename.lower()
        or "wirtschaftsplan" in normalized_filename
    )

    has_etv = (
        "etv2024" in filename.lower()
        or "etv protokoll" in normalized_filename
    )

    if has_wp and has_etv:

        return [
            "Wirtschaftsplan",
            "ETV-Protokoll"
        ], {
            "Wirtschaftsplan": 100,
            "ETV-Protokoll": 100
        }


    # --------------------------------------------------
    # STRONG TITLE PATTERNS
    # ONLY CHECK FIRST PAGE
    # --------------------------------------------------

    strong_patterns = {

        "Jahresabrechnung": [
            "verwaltungseinzelabrechnung",
            "zusammenfassung der jahresabrechnung",
            "jahresabrechnung"
        ],

        "Einzelwirtschaftsplan": [
            "einzelwirtschaftsplan"
        ],

        "Gesamtwirtschaftsplan": [
            "gesamtwirtschaftsplan"
        ],

        "Wirtschaftsplan": [
            "wirtschaftsplan"
        ],

        "ETV-Protokoll": [
            "protokoll der eigentümerversammlung",
            "niederschrift der eigentümerversammlung"
        ],

        "Energieausweis": [
            "energieausweis"
        ],

        "Teilungserklärung": [
            "teilungserklärung"
        ],

        "Grundriss": [
            "grundriss"
        ],

        "Flurkarte": [
            "flurkarte"
        ],

        "GBA": [
            "grundbuch",
            "grundbuchauszug"
        ],

        "Hausordnung": [
            "hausordnung"
        ]
    }


    # --------------------------------------------------
    # 1. FILENAME = STRONG EVIDENCE
    # --------------------------------------------------

    for official_type, keywords in document_types.items():

        for keyword in keywords:

            if keyword_exists(
                filename_lower,
                keyword
            ):

                scores[official_type] = (
                    scores.get(official_type, 0) + 8
                )

                break


    # --------------------------------------------------
    # 2. FIRST PAGE TITLE = VERY STRONG EVIDENCE
    # --------------------------------------------------

    for document_type, patterns in strong_patterns.items():

        for pattern in patterns:

            if pattern in first_page_lower:

                scores[document_type] = (
                    scores.get(document_type, 0) + 12
                )

                break


    # --------------------------------------------------
    # 3. NORMAL KEYWORDS ON FIRST PAGE
    # --------------------------------------------------

    for official_type, keywords in document_types.items():

        for keyword in keywords:

            if keyword_exists(
                first_page_lower,
                keyword
            ):

                scores[official_type] = (
                    scores.get(official_type, 0) + 4
                )

                break


    # --------------------------------------------------
    # 4. WHOLE DOCUMENT = WEAK EVIDENCE
    # --------------------------------------------------

    for official_type, keywords in document_types.items():

        for keyword in keywords:

            if keyword_exists(
                full_text_lower,
                keyword
            ):

                scores[official_type] = (
                    scores.get(official_type, 0) + 1
                )

                break


    # --------------------------------------------------
    # SPECIFIC WIRTSCHAFTSPLAN TYPES
    # --------------------------------------------------

    if "Einzelwirtschaftsplan" in scores:

        if (
            scores["Einzelwirtschaftsplan"]
            >= scores.get("Wirtschaftsplan", 0)
        ):
            scores.pop("Wirtschaftsplan", None)


    if "Gesamtwirtschaftsplan" in scores:

        if (
            scores["Gesamtwirtschaftsplan"]
            >= scores.get("Wirtschaftsplan", 0)
        ):
            scores.pop("Wirtschaftsplan", None)

    # Prefer Wohngebäudeversicherung over generic Versicherungspolice
    if "Wohngebäudeversicherung" in scores:
        scores.pop("Versicherungspolice", None)
    # --------------------------------------------------
    # NOTHING FOUND
    # --------------------------------------------------

    if not scores:
        return [], {}


    # Sort highest score first
    sorted_scores = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    best_type = sorted_scores[0][0]
    best_score = sorted_scores[0][1]


    # If we only found a weak mention somewhere
    # in the document, don't trust it.
    if best_score < 4:
        return [], scores


    return [best_type], scores


# --------------------------------------------------
# YEAR DETECTION
# --------------------------------------------------

def detect_year(text, document_type, filename=""):
    if document_type == "Jahresabrechnung":

        match = re.search(
            r"abrechnungszeitraum\s*"
            r"\d{2}\.\d{2}\.(\d{4})\s*[-–]\s*"
            r"\d{2}\.\d{2}\.(\d{4})",
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(2)


    if document_type in [
        "Wirtschaftsplan",
        "Einzelwirtschaftsplan",
        "Gesamtwirtschaftsplan"
    ]:

        match = re.search(
            r"wirtschaftsjahr\s*(20\d{2})",
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(1)


    if document_type == "ETV-Protokoll":

        match = re.search(
            r"(?:eigentümerversammlung|eigentuemerversammlung)"
            r".{0,100}?"
            r"(\d{2}\.\d{2}\.(20\d{2}))",
            text,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            return match.group(2)
    # --------------------------------------------------
    # FALLBACK: YEAR FROM FILENAME
    # --------------------------------------------------

    filename_years = re.findall(
        r"\b(20\d{2})\b",
        normalize_text(filename)
    )

    if filename_years:

        # Use first year found in filename
        return filename_years[0]


    return None


def detect_details(filename, document_type):
    normalized = normalize_text(filename)
    original_lower = filename.lower()

    details = None

    # --------------------------------------------------
    # GBA
    # Example:
    # GBA_vom_14.08.2024_Blatt_3502.pdf
    # → Blatt 3502
    # --------------------------------------------------

    if document_type == "GBA":

        match = re.search(
            r"blatt[\s_]*(\d+)",
            filename,
            re.IGNORECASE
        )

        if match:
            return f"Blatt {match.group(1)}"

    # --------------------------------------------------
    # ENERGIEAUSWEIS
    # Example:
    # Energieausweis_bis2028
    # → bis 2028
    # --------------------------------------------------

    if document_type == "Energieausweis":

        match = re.search(
            r"bis[\s_-]*(20\d{2})",
            filename,
            re.IGNORECASE
        )

        if match:
            return f"bis {match.group(1)}"

    # --------------------------------------------------
    # GRUNDRISS ALT
    # Reference folder contains:
    # SG08 - Grundriss ALT
    # --------------------------------------------------

    if document_type == "Grundriss":

        if re.search(
                r"\balt\b",
                normalized,
                re.IGNORECASE
        ):
            return "ALT"

    # --------------------------------------------------
    # ZERTIFIKAT WOFLV
    # --------------------------------------------------

    if document_type == "WoFlV":

        if "zertifikat" in normalized:
            return "Zertifikat"

    return details

def detect_type_from_filename(filename):

    normalized_filename = normalize_text(filename)

    filename_matches = []

    for official_type, keywords in document_types.items():

        for keyword in keywords:

            if keyword_exists(
                normalized_filename,
                keyword
            ):

                filename_matches.append(official_type)
                break


    # Remove generic Wirtschaftsplan when specific type exists
    if "Einzelwirtschaftsplan" in filename_matches:
        if "Wirtschaftsplan" in filename_matches:
            filename_matches.remove("Wirtschaftsplan")

    if "Gesamtwirtschaftsplan" in filename_matches:
        if "Wirtschaftsplan" in filename_matches:
            filename_matches.remove("Wirtschaftsplan")


    # Prefer specific insurance type
    if "Wohngebäudeversicherung" in filename_matches:
        if "Versicherungspolice" in filename_matches:
            filename_matches.remove("Versicherungspolice")


    return filename_matches
def extract_image_content(image_path):

    image = Image.open(image_path)

    text = pytesseract.image_to_string(
        image,
        lang="deu+eng"
    )

    return text, text, True