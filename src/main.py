from pathlib import Path
import re
import csv
import hashlib

from classifier import (
    extract_pdf_content,
    extract_image_content,
    detect_document_type,
    detect_year,
    detect_details,
    detect_type_from_filename
)


# ============================================================
# SETTINGS
# ============================================================

# This is the REAL company task folder.
# The program will scan MUC project folders directly from here.
PROJECTS_ROOT = Path(
    r"C:\Users\Jabran Mustafa\Desktop\ai assignment appartment\_Task Example AI-Student"
)


# Project root of your Python application
BASE_DIR = Path(__file__).resolve().parent.parent


# Reports will be written here
OUTPUT_FOLDER = BASE_DIR / "output"
OUTPUT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


# IMPORTANT:
# False = show what WOULD happen
# True  = actually rename files
APPLY_RENAMES = True


# File types we support
SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png"
}


# Files with these names/types should not be
# automatically classified using our current reference taxonomy.
UNSUPPORTED_FILENAME_PATTERNS = [
    "kv_",
    "kaufvertrag",
    "modernisierungsaufstellung",
    "rnd-gutachten",
    "exposé",
    "expose"
]


# ============================================================
# HELPER: CALCULATE FILE HASH
# ============================================================

def calculate_file_hash(file_path):

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        while True:

            chunk = file.read(8192)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


# ============================================================
# HELPER: DETECT PROJECT CODE
# ============================================================

def detect_project_code(folder_name):

    project_match = re.search(
        r"(SG|MUC)\s*0*(\d+)",
        folder_name,
        re.IGNORECASE
    )

    if not project_match:
        return None

    prefix = project_match.group(1).upper()
    number = int(project_match.group(2))

    if prefix == "SG":
        return f"SG{number:02d}"

    if prefix == "MUC":
        return f"MUC{number}"

    return None


# ============================================================
# HELPER: FIND SUPPORTED FILES
# ============================================================

def find_supported_files(project_folder):

    document_files = [
        path
        for path in project_folder.rglob("*")
        if path.is_file()
        and path.suffix.lower()
        in SUPPORTED_EXTENSIONS
    ]

    return sorted(
        document_files,
        key=lambda path: str(path).lower()
    )


# ============================================================
# PROCESS ONE PROJECT FOLDER
# ============================================================

def process_project(input_folder):

    project = detect_project_code(
        input_folder.name
    )

    if not project:

        print(
            "\nSKIPPING:",
            input_folder.name,
            "- project code not detected."
        )

        return


    # --------------------------------------------------------
    # FIND FILES
    # --------------------------------------------------------

    document_files = find_supported_files(
        input_folder
    )


    print("\n")
    print("=" * 80)

    print(
        "PROCESSING PROJECT:",
        project
    )

    print(
        "INPUT PATH:",
        input_folder
    )

    print(
        "SUPPORTED FILES FOUND:",
        len(document_files)
    )

    print("=" * 80)


    # --------------------------------------------------------
    # PROJECT DATA
    # --------------------------------------------------------

    problem_cases = []
    rename_manifest = []
    duplicate_files = []

    seen_hashes = {}


    # ========================================================
    # PROCESS EVERY FILE
    # ========================================================

    for file_path in document_files:

        try:

            # ------------------------------------------------
            # DUPLICATE CHECK
            # ------------------------------------------------

            file_hash = calculate_file_hash(
                file_path
            )


            if file_hash in seen_hashes:

                cached = seen_hashes[
                    file_hash
                ]

                relative_path = str(
                    file_path.relative_to(
                        input_folder
                    )
                )


                print(
                    "\nOriginal:",
                    file_path.name
                )

                print(
                    "Status: DUPLICATE"
                )

                print(
                    "Duplicate of:",
                    cached["original_file"]
                )


                duplicate_files.append({
                    "duplicate_file":
                        relative_path,

                    "duplicate_of":
                        cached["original_file"]
                })


                # --------------------------------------------
                # REUSE SAFE CLASSIFICATION
                # --------------------------------------------

                if (
                    cached["status"]
                    == "READY"
                ):

                    # Keep duplicate's own extension
                    duplicate_extension = (
                        file_path.suffix.lower()
                    )

                    proposed_stem = Path(
                        cached[
                            "proposed_filename"
                        ]
                    ).stem

                    duplicate_proposed_name = (
                        proposed_stem
                        + duplicate_extension
                    )


                    rename_manifest.append({
                        "original_file":
                            relative_path,

                        "document_type":
                            cached[
                                "document_type"
                            ],

                        "year":
                            cached["year"],

                        "proposed_filename":
                            duplicate_proposed_name,

                        "ocr_used":
                            False
                    })


                    print(
                        "Duplicate action: "
                        "reuse classification "
                        "for rename"
                    )


                else:

                    problem_cases.append({
                        "original_file":
                            relative_path,

                        "detected_type":
                            cached[
                                "document_type"
                            ] or "",

                        "year":
                            cached[
                                "year"
                            ] or "",

                        "proposed_filename":
                            cached[
                                "proposed_filename"
                            ] or "",

                        "reason":
                            "Duplicate of a "
                            "document that "
                            "requires review."
                    })


                    print(
                        "Duplicate action: REVIEW"
                    )


                continue


            # ------------------------------------------------
            # CONTENT EXTRACTION
            # ------------------------------------------------

            extension = (
                file_path.suffix.lower()
            )


            if extension == ".pdf":

                (
                    first_page_text,
                    text,
                    used_ocr
                ) = extract_pdf_content(
                    file_path
                )

            else:

                (
                    first_page_text,
                    text,
                    used_ocr
                ) = extract_image_content(
                    file_path
                )


            # ------------------------------------------------
            # CLASSIFICATION
            # ------------------------------------------------

            detected_types, scores = (
                detect_document_type(
                    file_path.name,
                    first_page_text,
                    text
                )
            )


            filename_types = (
                detect_type_from_filename(
                    file_path.name
                )
            )


            document_type = None
            year = None
            details = None


            if len(detected_types) == 1:

                document_type = (
                    detected_types[0]
                )


                year = detect_year(
                    text,
                    document_type,
                    file_path.name
                )


                details = detect_details(
                    file_path.name,
                    document_type
                )


            # ------------------------------------------------
            # BUILD PROPOSED FILENAME
            # ------------------------------------------------

            proposed_filename = None


            if (
                project
                and document_type
            ):

                # --------------------------------------------
                # SPECIAL WoFlV CERTIFICATE RULE
                # --------------------------------------------

                if (
                    document_type == "WoFlV"
                    and details == "Zertifikat"
                ):

                    proposed_filename = (
                        f"{project} - "
                        f"Zertifikat WoFlV"
                    )

                else:

                    proposed_filename = (
                        f"{project} - "
                        f"{document_type}"
                    )


                    # Examples:
                    # Blatt 3502
                    # bis 2028
                    # ALT
                    if details:

                        proposed_filename += (
                            f" {details}"
                        )

                    elif year:

                        proposed_filename += (
                            f" {year}"
                        )


                # Preserve original format
                proposed_filename += (
                    extension
                )


            # ------------------------------------------------
            # DISPLAY CLASSIFICATION
            # ------------------------------------------------

            print(
                "\nOriginal:",
                file_path.name
            )

            print(
                "Detected type:",
                document_type
            )

            print(
                "Filename suggests:",
                filename_types
            )

            print(
                "Year:",
                year
            )

            print(
                "Details:",
                details
            )

            print(
                "OCR used:",
                used_ocr
            )

            print(
                "Scores:",
                scores
            )

            print(
                "Proposed:",
                proposed_filename
            )


            # =================================================
            # SAFETY CHECKS
            # =================================================

            filename_lower = (
                file_path.name.lower()
            )

            force_review = False
            review_reason = None


            # ------------------------------------------------
            # UNSUPPORTED DOCUMENT TYPE
            # ------------------------------------------------

            for pattern in (
                UNSUPPORTED_FILENAME_PATTERNS
            ):

                if (
                    pattern
                    in filename_lower
                ):

                    force_review = True

                    review_reason = (
                        "Document type not "
                        "clearly represented "
                        "in reference folders."
                    )

                    break


            # ------------------------------------------------
            # MULTIPLE TYPES DETECTED
            # ------------------------------------------------

            if len(detected_types) > 1:

                force_review = True

                review_reason = (
                    "Multiple document "
                    "types detected."
                )


            # ------------------------------------------------
            # AMBIGUOUS SCORE
            # ------------------------------------------------

            if len(scores) >= 2:

                sorted_scores = sorted(
                    scores.items(),
                    key=lambda item:
                        item[1],
                    reverse=True
                )


                best_type, best_score = (
                    sorted_scores[0]
                )

                (
                    second_type,
                    second_score
                ) = sorted_scores[1]


                score_difference = (
                    best_score
                    - second_score
                )


                if (
                    second_score >= 4
                    and
                    score_difference <= 3
                ):

                    force_review = True

                    review_reason = (
                        f"Ambiguous "
                        f"classification: "
                        f"{best_type}="
                        f"{best_score}, "
                        f"{second_type}="
                        f"{second_score}."
                    )


            # ------------------------------------------------
            # FILENAME / CONTENT CONFLICT
            # ------------------------------------------------

            if (
                len(filename_types) == 1
                and
                len(detected_types) == 1
                and
                filename_types[0]
                != detected_types[0]
            ):

                force_review = True

                review_reason = (
                    "Filename and document "
                    "content suggest different "
                    "document types."
                )


            # =================================================
            # FINAL DECISION
            # =================================================

            relative_path = str(
                file_path.relative_to(
                    input_folder
                )
            )


            if force_review:

                print(
                    "Status: REVIEW"
                )

                print(
                    "Reason:",
                    review_reason
                )


                problem_cases.append({
                    "original_file":
                        relative_path,

                    "detected_type":
                        document_type or "",

                    "year":
                        year or "",

                    "proposed_filename":
                        proposed_filename
                        or "",

                    "reason":
                        review_reason
                })


                seen_hashes[
                    file_hash
                ] = {

                    "original_file":
                        relative_path,

                    "status":
                        "REVIEW",

                    "document_type":
                        document_type,

                    "year":
                        year or "",

                    "proposed_filename":
                        proposed_filename
                        or ""
                }


            elif proposed_filename:

                print(
                    "Status: READY"
                )


                rename_manifest.append({
                    "original_file":
                        relative_path,

                    "document_type":
                        document_type,

                    "year":
                        year or "",

                    "proposed_filename":
                        proposed_filename,

                    "ocr_used":
                        used_ocr
                })


                seen_hashes[
                    file_hash
                ] = {

                    "original_file":
                        relative_path,

                    "status":
                        "READY",

                    "document_type":
                        document_type,

                    "year":
                        year or "",

                    "proposed_filename":
                        proposed_filename
                }


            else:

                reason = (
                    "Could not identify "
                    "document confidently."
                )


                print(
                    "Status: REVIEW"
                )

                print(
                    "Reason:",
                    reason
                )


                problem_cases.append({
                    "original_file":
                        relative_path,

                    "detected_type":
                        document_type or "",

                    "year":
                        year or "",

                    "proposed_filename":
                        proposed_filename
                        or "",

                    "reason":
                        reason
                })


                seen_hashes[
                    file_hash
                ] = {

                    "original_file":
                        relative_path,

                    "status":
                        "REVIEW",

                    "document_type":
                        document_type,

                    "year":
                        year or "",

                    "proposed_filename":
                        proposed_filename
                        or ""
                }


        # ----------------------------------------------------
        # PROCESSING ERROR
        # ----------------------------------------------------

        except Exception as error:

            print(
                "\nOriginal:",
                file_path.name
            )

            print(
                "Status: ERROR"
            )

            print(
                "Error:",
                error
            )


            problem_cases.append({
                "original_file": str(
                    file_path.relative_to(
                        input_folder
                    )
                ),

                "detected_type": "",

                "year": "",

                "proposed_filename": "",

                "reason":
                    f"Processing error: "
                    f"{error}"
            })


    # ========================================================
    # PLANNED TARGET COLLISION CHECK
    # ========================================================

    target_groups = {}


    for item in rename_manifest:

        source_path = (
            input_folder
            / item["original_file"]
        )


        target_path = (
            source_path.with_name(
                item[
                    "proposed_filename"
                ]
            )
        )


        # Windows paths are case-insensitive
        target_key = str(
            target_path.resolve()
        ).lower()


        if (
            target_key
            not in target_groups
        ):

            target_groups[
                target_key
            ] = []


        target_groups[
            target_key
        ].append(
            item
        )


    collision_files = set()


    for (
        target_key,
        items
    ) in target_groups.items():

        if len(items) > 1:

            print(
                "\nTARGET "
                "COLLISION DETECTED:"
            )

            print(
                "Proposed target:",
                items[0][
                    "proposed_filename"
                ]
            )


            for item in items:

                print(
                    " -",
                    item[
                        "original_file"
                    ]
                )


                collision_files.add(
                    item[
                        "original_file"
                    ]
                )


                problem_cases.append({
                    "original_file":
                        item[
                            "original_file"
                        ],

                    "detected_type":
                        item[
                            "document_type"
                        ] or "",

                    "year":
                        item[
                            "year"
                        ] or "",

                    "proposed_filename":
                        item[
                            "proposed_filename"
                        ],

                    "reason":
                        "Multiple files would "
                        "be renamed to the "
                        "same target filename "
                        "inside the same folder."
                })


    # Remove collision cases
    # from auto-renaming
    rename_manifest = [
        item
        for item in rename_manifest
        if item[
            "original_file"
        ] not in collision_files
    ]


    # ========================================================
    # SAVE PROJECT REPORTS
    # ========================================================

    problem_file = (
        OUTPUT_FOLDER
        / f"{project}_problem_cases.csv"
    )


    manifest_file = (
        OUTPUT_FOLDER
        / f"{project}_rename_manifest.csv"
    )


    duplicate_file = (
        OUTPUT_FOLDER
        / f"{project}_duplicates.csv"
    )


    # --------------------------------------------------------
    # SAVE PROBLEM CASES
    # --------------------------------------------------------

    with open(
        problem_file,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "original_file",
                "detected_type",
                "year",
                "proposed_filename",
                "reason"
            ]
        )

        writer.writeheader()

        writer.writerows(
            problem_cases
        )


    # --------------------------------------------------------
    # SAVE RENAME MANIFEST
    # --------------------------------------------------------

    with open(
        manifest_file,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "original_file",
                "document_type",
                "year",
                "proposed_filename",
                "ocr_used"
            ]
        )

        writer.writeheader()

        writer.writerows(
            rename_manifest
        )


    # --------------------------------------------------------
    # SAVE DUPLICATES
    # --------------------------------------------------------

    with open(
        duplicate_file,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "duplicate_file",
                "duplicate_of"
            ]
        )

        writer.writeheader()

        writer.writerows(
            duplicate_files
        )


    print(
        "\nReports created:"
    )

    print(
        problem_file
    )

    print(
        manifest_file
    )

    print(
        duplicate_file
    )


    # ========================================================
    # RENAME
    # ========================================================

    print(
        "\n" + "=" * 80
    )


    if APPLY_RENAMES:

        print(
            "RENAME MODE: APPLY"
        )

    else:

        print(
            "RENAME MODE: DRY RUN"
        )


    for item in rename_manifest:

        source_path = (
            input_folder
            / item[
                "original_file"
            ]
        )


        target_path = (
            source_path.with_name(
                item[
                    "proposed_filename"
                ]
            )
        )


        # --------------------------------------------
        # ALREADY CORRECT
        # --------------------------------------------

        if (
            source_path
            == target_path
        ):

            print(
                "ALREADY CORRECT:",
                source_path.name
            )

            continue


        # --------------------------------------------
        # NEVER OVERWRITE
        # --------------------------------------------

        if target_path.exists():

            print(
                "COLLISION:",
                source_path.name,
                "->",
                target_path.name
            )

            continue


        # --------------------------------------------
        # APPLY OR DRY RUN
        # --------------------------------------------

        if APPLY_RENAMES:

            source_path.rename(
                target_path
            )

            print(
                "RENAMED:",
                source_path.name,
                "->",
                target_path.name
            )

        else:

            print(
                "WOULD RENAME:",
                source_path.name,
                "->",
                target_path.name
            )


    # ========================================================
    # PROJECT SUMMARY
    # ========================================================

    total_files = len(
        document_files
    )


    unique_content = (
        total_files
        - len(duplicate_files)
    )


    print(
        "\nSummary for",
        project
    )


    print(
        "READY FILES:",
        len(rename_manifest)
    )


    print(
        "REVIEW FILES:",
        len(problem_cases)
    )


    print(
        "DUPLICATE COPIES:",
        len(duplicate_files)
    )


    print(
        "TOTAL FILES:",
        total_files
    )


    print(
        "UNIQUE CONTENT:",
        unique_content
    )


    print("=" * 80)


# ============================================================
# MAIN
# ============================================================

print(
    "PROJECT ROOT:",
    PROJECTS_ROOT
)


print(
    "ROOT EXISTS:",
    PROJECTS_ROOT.exists()
)


if not PROJECTS_ROOT.exists():

    print(
        "ERROR: Project root "
        "does not exist."
    )


else:

    # --------------------------------------------------------
    # FIND ALL MUC PROJECT FOLDERS
    # --------------------------------------------------------

    project_folders = []


    for folder in (
        PROJECTS_ROOT.iterdir()
    ):

        if not folder.is_dir():
            continue


        project_code = (
            detect_project_code(
                folder.name
            )
        )


        # IMPORTANT:
        # Only process MUC folders.
        #
        # SG04 / SG08 are sorted references,
        # so we intentionally ignore them.
        if (
            project_code
            and project_code.startswith(
                "MUC"
            )
        ):

            project_folders.append(
                folder
            )


    project_folders = sorted(
        project_folders,
        key=lambda folder:
            folder.name.lower()
    )


    print(
        "MUC PROJECTS FOUND:",
        len(project_folders)
    )


    # --------------------------------------------------------
    # PROCESS ALL MUC PROJECTS
    # --------------------------------------------------------

    projects_processed = 0


    for project_folder in (
        project_folders
    ):

        process_project(
            project_folder
        )

        projects_processed += 1


    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    print("\n")
    print("#" * 80)

    print(
        "ALL PROJECTS FINISHED"
    )

    print(
        "Projects processed:",
        projects_processed
    )

    print("#" * 80)