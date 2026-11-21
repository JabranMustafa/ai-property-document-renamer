import json
from pathlib import Path


# --------------------------------------------------
# LOAD COMPANY DOCUMENT TYPES
# --------------------------------------------------

config_path = Path("../config/document_types.json")

with open(config_path, "r", encoding="utf-8") as file:
    document_types = json.load(file)


# --------------------------------------------------
# SIMPLE CLASSIFICATION FUNCTION
# --------------------------------------------------

def detect_document_type(text):

    text_lower = text.lower()

    matches = []

    for official_type, keywords in document_types.items():

        for keyword in keywords:

            if keyword.lower() in text_lower:

                matches.append(official_type)
                break


    # --------------------------------------------------
    # REMOVE GENERIC TYPES WHEN A MORE SPECIFIC TYPE EXISTS
    # --------------------------------------------------

    if "Einzelwirtschaftsplan" in matches:
        if "Wirtschaftsplan" in matches:
            matches.remove("Wirtschaftsplan")

    if "Gesamtwirtschaftsplan" in matches:
        if "Wirtschaftsplan" in matches:
            matches.remove("Wirtschaftsplan")


    return matches


# --------------------------------------------------
# TEST EXAMPLES
# --------------------------------------------------

examples = [
    "Zusammenfassung der Jahresabrechnung für Ihre Einheit",
    "Protokoll der Eigentümerversammlung vom 15.05.2024",
    "Energieausweis für Wohngebäude",
    "Grundbuchauszug Blatt 3502",
    "Einzelwirtschaftsplan für das Wirtschaftsjahr 2026"
]


for example in examples:

    result = detect_document_type(example)

    print("\nText:")
    print(example)

    print("Detected:")
    print(result)