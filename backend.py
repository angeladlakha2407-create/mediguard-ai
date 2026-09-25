from pathlib import Path
import pandas as pd

# =========================================================
# LOAD DATASETS WITH ROBUST PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

def load_csv_data(filename):
    possible_paths = [
        BASE_DIR / "data" / filename,
        BASE_DIR / filename,
    ]
    for path in possible_paths:
        if path.exists():
            df = pd.read_csv(path)
            df.columns = df.columns.str.strip()
            return df
    # Return empty DataFrame with default fallback columns if missing
    return pd.DataFrame()

medicines = load_csv_data("medicines.csv")
interactions = load_csv_data("interactions.csv")
batches = load_csv_data("batches.csv")


# =========================================================
# NORMALIZATION
# =========================================================

def normalize(value):
    """Normalize text for comparison."""

    if value is None:
        return ""

    if pd.isna(value):
        return ""

    return str(value).strip().lower()


# =========================================================
# SEARCH MEDICINE
# =========================================================

def search_medicine(name):
    """Search the medicine reference database."""

    if not name or medicines.empty:
        return None

    name = normalize(name)

    result = medicines[
        medicines["medicine"]
        .astype(str)
        .str.strip()
        .str.lower()
        == name
    ]

    if result.empty:
        return None

    return result.iloc[0].to_dict()


# =========================================================
# IDENTIFY MEDICINE FROM OCR
# =========================================================

def identify_medicine_from_ocr(ocr_medicine_name):
    """Find OCR-detected medicine in reference database."""

    if not ocr_medicine_name:
        return None

    return search_medicine(ocr_medicine_name)


# =========================================================
# FIND TRUSTED BATCH
# =========================================================

def find_batch(medicine_name, batch_number):
    """
    Search the trusted batch database using medicine name
    and batch number.

    A missing batch is NOT automatically considered fake.
    It simply means the local reference database does not
    contain that batch.
    """

    if not medicine_name or not batch_number or batches.empty:
        return None

    medicine_name = normalize(medicine_name)
    batch_number = normalize(batch_number)

    result = batches[
        (
            batches["medicine"]
            .astype(str)
            .str.strip()
            .str.lower()
            == medicine_name
        )
        &
        (
            batches["batch_number"]
            .astype(str)
            .str.strip()
            .str.lower()
            == batch_number
        )
    ]

    if result.empty:
        return None

    return result.iloc[0].to_dict()


# =========================================================
# FIELD COMPARISON
# =========================================================

def compare_field(field_name, detected_value, expected_value):
    """
    Compare a detected package field with trusted reference data.

    Possible statuses:
        MATCH
        MISMATCH
        NOT_VERIFIED
    """

    detected = normalize(detected_value)
    expected = normalize(expected_value)

    if not detected:
        return {
            "field": field_name,
            "status": "NOT_VERIFIED",
            "detected": None,
            "expected": expected_value,
            "message": (
                f"{field_name} could not be verified "
                f"from the package image."
            )
        }

    if not expected:
        return {
            "field": field_name,
            "status": "NOT_VERIFIED",
            "detected": detected_value,
            "expected": None,
            "message": (
                f"No trusted reference value is available "
                f"for {field_name}."
            )
        }

    if detected == expected:
        return {
            "field": field_name,
            "status": "MATCH",
            "detected": detected_value,
            "expected": expected_value,
            "message": (
                f"{field_name} matches the available "
                f"reference data."
            )
        }

    return {
        "field": field_name,
        "status": "MISMATCH",
        "detected": detected_value,
        "expected": expected_value,
        "message": (
            f"{field_name} mismatch: detected "
            f"'{detected_value}', expected "
            f"'{expected_value}'."
        )
    }


# =========================================================
# MEDICINE NAME VERIFICATION
# =========================================================

def verify_medicine_name(selected_medicine, ocr_medicine):

    if not selected_medicine:
        return {
            "status": "NOT_VERIFIED",
            "message": "Reference medicine was not provided."
        }

    if not ocr_medicine:
        return {
            "status": "NOT_VERIFIED",
            "message": (
                "Medicine name could not be identified "
                "from the package."
            )
        }

    if normalize(selected_medicine) == normalize(ocr_medicine):
        return {
            "status": "MATCH",
            "message": (
                "Medicine name matches the reference data."
            )
        }

    return {
        "status": "MISMATCH",
        "message": (
            f"Expected '{selected_medicine}', but OCR "
            f"identified '{ocr_medicine}'."
        )
    }


# =========================================================
# ACTIVE INGREDIENT VERIFICATION
# =========================================================

def verify_active_ingredient(
    reference_medicine,
    package_details
):
    """
    Verify active ingredient ONLY when the ingredient is
    independently detected from the package.
    """

    if not reference_medicine:
        return {
            "status": "NOT_VERIFIED",
            "message": (
                "Reference medicine is unavailable."
            )
        }

    reference_ingredient = normalize(
        reference_medicine.get("active ingredient")
    )

    detected_ingredient = normalize(
        (package_details or {}).get("active_ingredient")
    )

    if not reference_ingredient:
        return {
            "status": "NOT_VERIFIED",
            "message": (
                "No active ingredient reference data "
                "is available."
            )
        }

    if not detected_ingredient:
        return {
            "status": "NOT_VERIFIED",
            "message": (
                "Active ingredient could not be "
                "independently verified from OCR."
            ),
            "reference": reference_medicine.get(
                "active ingredient"
            ),
            "detected": None
        }

    if detected_ingredient == reference_ingredient:
        return {
            "status": "MATCH",
            "message": (
                "Active ingredient detected on the package "
                "matches the reference data."
            ),
            "reference": reference_medicine.get(
                "active ingredient"
            ),
            "detected": package_details.get(
                "active_ingredient"
            )
        }

    return {
        "status": "MISMATCH",
        "message": (
            f"Active ingredient mismatch: detected "
            f"'{package_details.get('active_ingredient')}', "
            f"expected "
            f"'{reference_medicine.get('active ingredient')}'."
        ),
        "reference": reference_medicine.get(
            "active ingredient"
        ),
        "detected": package_details.get(
            "active_ingredient"
        )
    }


# =========================================================
# BATCH VERIFICATION
# =========================================================

def verify_batch(
    medicine_name,
    package_details
):
    """
    Verify package-specific fields using batches.csv.

    Batch information is checked only when OCR actually
    detects a batch number.

    Missing local batch records are NOT treated as proof
    of counterfeit medicine.
    """

    package_details = package_details or {}

    batch_number = package_details.get("batch_number")

    # -----------------------------------------------------
    # NO BATCH DETECTED
    # -----------------------------------------------------

    if not batch_number:
        return {
            "status": "NOT_VERIFIED",
            "batch_found": False,
            "signals": [],
            "matches": [],
            "mismatches": [],
            "detected": [],
            "not_verified": [
                "Batch number was not detected from the package."
            ]
        }

    # -----------------------------------------------------
    # SEARCH TRUSTED BATCH DATABASE
    # -----------------------------------------------------

    trusted_batch = find_batch(
        medicine_name,
        batch_number
    )

    # -----------------------------------------------------
    # BATCH NOT IN LOCAL DATABASE
    # -----------------------------------------------------

    if trusted_batch is None:
        return {
            "status": "NOT_VERIFIED",
            "batch_found": False,
            "signals": [],
            "matches": [],
            "mismatches": [],
            "detected": [
                f"Batch number detected: {batch_number}."
            ],
            "not_verified": [
                (
                    f"Batch '{batch_number}' was not found "
                    "in the local trusted batch database."
                )
            ]
        }

    signals = []
    matches = []
    mismatches = []
    detected = []
    not_verified = []

    # -----------------------------------------------------
    # BATCH NUMBER
    # -----------------------------------------------------

    result = compare_field(
        "Batch Number",
        batch_number,
        trusted_batch.get("batch_number")
    )

    signals.append(result)

    if result["status"] == "MATCH":
        matches.append(result["message"])

    elif result["status"] == "MISMATCH":
        mismatches.append(result["message"])

    else:
        not_verified.append(result["message"])

    # -----------------------------------------------------
    # MANUFACTURING DATE
    # -----------------------------------------------------

    result = compare_field(
        "Manufacturing Date",
        package_details.get("manufacturing_date"),
        trusted_batch.get("manufacturing_date")
    )

    signals.append(result)

    if result["status"] == "MATCH":
        matches.append(result["message"])

    elif result["status"] == "MISMATCH":
        mismatches.append(result["message"])

    else:
        not_verified.append(result["message"])

    # -----------------------------------------------------
    # EXPIRY DATE
    # -----------------------------------------------------

    result = compare_field(
        "Expiry Date",
        package_details.get("expiry_date"),
        trusted_batch.get("expiry_date")
    )

    signals.append(result)

    if result["status"] == "MATCH":
        matches.append(result["message"])

    elif result["status"] == "MISMATCH":
        mismatches.append(result["message"])

    else:
        not_verified.append(result["message"])

    # -----------------------------------------------------
    # MRP
    # -----------------------------------------------------

    result = compare_field(
        "MRP",
        package_details.get("mrp"),
        trusted_batch.get("mrp")
    )

    signals.append(result)

    if result["status"] == "MATCH":
        matches.append(result["message"])

    elif result["status"] == "MISMATCH":
        mismatches.append(result["message"])

    else:
        not_verified.append(result["message"])

    # -----------------------------------------------------
    # LICENCE NUMBER
    # -----------------------------------------------------

    result = compare_field(
        "Licence Number",
        package_details.get("licence_number"),
        trusted_batch.get("licence_number")
    )

    signals.append(result)

    if result["status"] == "MATCH":
        matches.append(result["message"])

    elif result["status"] == "MISMATCH":
        mismatches.append(result["message"])

    else:
        not_verified.append(result["message"])

    # -----------------------------------------------------
    # FINAL BATCH STATUS
    # -----------------------------------------------------

    if mismatches:
        status = "MISMATCH"

    elif matches:
        status = "CONSISTENT"

    else:
        status = "NOT_VERIFIED"

    return {
        "status": status,
        "batch_found": True,
        "trusted_batch": trusted_batch,
        "signals": signals,
        "matches": matches,
        "mismatches": mismatches,
        "detected": detected,
        "not_verified": not_verified
    }


# =========================================================
# PACKAGE VERIFICATION
# =========================================================

def verify_package(reference_medicine, package_details):

    if not reference_medicine:
        return {
            "status": "NOT_VERIFIED",
            "signals": [],
            "matches": [],
            "mismatches": [],
            "detected": [],
            "not_verified": []
        }

    package_details = package_details or {}

    signals = []
    matches = []
    mismatches = []
    detected = []
    not_verified = []

    # -----------------------------------------------------
    # MEDICINE NAME
    # -----------------------------------------------------

    medicine_result = verify_medicine_name(
        reference_medicine.get("medicine"),
        package_details.get("medicine")
    )

    signals.append(medicine_result)

    if medicine_result["status"] == "MATCH":
        matches.append(medicine_result["message"])

    elif medicine_result["status"] == "MISMATCH":
        mismatches.append(medicine_result["message"])

    else:
        not_verified.append(medicine_result["message"])

    # -----------------------------------------------------
    # STRENGTH
    # -----------------------------------------------------

    if "strength" in reference_medicine:

        result = compare_field(
            "Strength",
            package_details.get("strength"),
            reference_medicine.get("strength")
        )

        signals.append(result)

        if result["status"] == "MATCH":
            matches.append(result["message"])

        elif result["status"] == "MISMATCH":
            mismatches.append(result["message"])

        else:
            not_verified.append(result["message"])

    elif package_details.get("strength"):

        message = (
            f"Strength detected: "
            f"{package_details['strength']}."
        )

        signals.append({
            "field": "Strength",
            "status": "DETECTED",
            "detected": package_details["strength"],
            "expected": None,
            "message": message
        })

        detected.append(message)

    else:

        message = "Strength was not detected."

        signals.append({
            "field": "Strength",
            "status": "NOT_VERIFIED",
            "detected": None,
            "expected": None,
            "message": message
        })

        not_verified.append(message)

    # -----------------------------------------------------
    # MANUFACTURER
    # -----------------------------------------------------

    if "manufacturer" in reference_medicine:

        result = compare_field(
            "Manufacturer",
            package_details.get("manufacturer"),
            reference_medicine.get("manufacturer")
        )

        signals.append(result)

        if result["status"] == "MATCH":
            matches.append(result["message"])

        elif result["status"] == "MISMATCH":
            mismatches.append(result["message"])

        else:
            not_verified.append(result["message"])

    elif package_details.get("manufacturer"):

        message = (
            f"Manufacturer detected: "
            f"{package_details['manufacturer']}."
        )

        signals.append({
            "field": "Manufacturer",
            "status": "DETECTED",
            "detected": package_details["manufacturer"],
            "expected": None,
            "message": message
        })

        detected.append(message)

    else:

        message = "Manufacturer was not detected."

        signals.append({
            "field": "Manufacturer",
            "status": "NOT_VERIFIED",
            "detected": None,
            "expected": None,
            "message": message
        })

        not_verified.append(message)

    # -----------------------------------------------------
    # BATCH VERIFICATION
    # -----------------------------------------------------

    batch_result = verify_batch(
        reference_medicine.get("medicine"),
        package_details
    )

    # Add batch signals to overall package verification
    signals.extend(
        batch_result.get("signals", [])
    )

    matches.extend(
        batch_result.get("matches", [])
    )

    mismatches.extend(
        batch_result.get("mismatches", [])
    )

    detected.extend(
        batch_result.get("detected", [])
    )

    not_verified.extend(
        batch_result.get("not_verified", [])
    )

    # -----------------------------------------------------
    # FINAL PACKAGE STATUS
    # -----------------------------------------------------

    if mismatches:
        status = "MISMATCH"

    elif matches:
        status = "CONSISTENT"

    else:
        status = "NOT_VERIFIED"

    return {
        "status": status,
        "signals": signals,
        "matches": matches,
        "mismatches": mismatches,
        "detected": detected,
        "not_verified": not_verified,
        "batch": batch_result
    }


# =========================================================
# BARCODE VERIFICATION
# =========================================================

def check_barcode(medicine_name, barcode_medicine):

    if not barcode_medicine:
        return {
            "status": "NOT_VERIFIED",
            "message": "Barcode was not detected."
        }

    if not medicine_name:
        return {
            "status": "NOT_VERIFIED",
            "message": "Reference medicine is unavailable."
        }

    if normalize(barcode_medicine) == normalize(medicine_name):
        return {
            "status": "MATCH",
            "message": (
                "Barcode information matches the medicine."
            )
        }

    return {
        "status": "MISMATCH",
        "message": (
            f"Barcode indicates '{barcode_medicine}', "
            f"while the expected medicine is "
            f"'{medicine_name}'."
        )
    }


# =========================================================
# INTERACTION CHECKER
# =========================================================

def check_interaction(medicine1, medicine2):

    if not medicine1 or not medicine2 or interactions.empty:
        return None

    medicine1 = normalize(medicine1)
    medicine2 = normalize(medicine2)

    result = interactions[
        (
            (
                interactions["medicine_1"]
                .astype(str)
                .str.lower()
                .str.strip()
                == medicine1
            )
            &
            (
                interactions["medicine_2"]
                .astype(str)
                .str.lower()
                .str.strip()
                == medicine2
            )
        )
        |
        (
            (
                interactions["medicine_1"]
                .astype(str)
                .str.lower()
                .str.strip()
                == medicine2
            )
            &
            (
                interactions["medicine_2"]
                .astype(str)
                .str.lower()
                .str.strip()
                == medicine1
            )
        )
    ]

    if result.empty:
        return {
            "found": False,
            "status": "No recorded interaction found."
        }

    interaction = result.iloc[0]

    return {
        "found": True,
        "status": "Interaction found.",
        "interaction": interaction.get(
            "interaction",
            ""
        ),
        "severity": interaction.get(
            "severity",
            "Unknown"
        )
    }


# =========================================================
# AUTHENTICITY / VERIFICATION ASSESSMENT
# =========================================================

def assess_authenticity(
    package_result,
    barcode_result,
    ingredient_result=None
):
    """
    Evidence-based package assessment.

    Possible results:

    SUSPICIOUS
    NO_MAJOR_INCONSISTENCY
    INSUFFICIENT_EVIDENCE

    This does NOT prove genuine or counterfeit status.
    """

    package_result = package_result or {}
    barcode_result = barcode_result or {}
    ingredient_result = ingredient_result or {}

    mismatches = len(
        package_result.get("mismatches", [])
    )

    barcode_status = barcode_result.get(
        "status",
        "NOT_VERIFIED"
    )

    ingredient_status = ingredient_result.get(
        "status",
        "NOT_VERIFIED"
    )

    # -----------------------------------------------------
    # REAL INCONSISTENCY
    # -----------------------------------------------------

    if (
        mismatches > 0
        or barcode_status == "MISMATCH"
        or ingredient_status == "MISMATCH"
    ):

        return {
            "assessment": "SUSPICIOUS",
            "summary": (
                "One or more verification inconsistencies "
                "were detected in the available package data."
            ),
            "mismatch_count": (
                mismatches
                + (1 if barcode_status == "MISMATCH" else 0)
                + (1 if ingredient_status == "MISMATCH" else 0)
            ),
            "barcode_status": barcode_status
        }

    # -----------------------------------------------------
    # STRONGER POSITIVE EVIDENCE
    # -----------------------------------------------------

    verified_matches = len(
        package_result.get("matches", [])
    )

    barcode_match = barcode_status == "MATCH"

    ingredient_match = ingredient_status == "MATCH"

    if barcode_match:

        return {
            "assessment": "NO_MAJOR_INCONSISTENCY",
            "summary": (
                "The available package information and "
                "barcode data are consistent with the "
                "reference data."
            ),
            "mismatch_count": 0,
            "barcode_status": barcode_status
        }

    if verified_matches >= 2 or ingredient_match:

        return {
            "assessment": "NO_MAJOR_INCONSISTENCY",
            "summary": (
                "The available verified package information "
                "is consistent with the reference data."
            ),
            "mismatch_count": 0,
            "barcode_status": barcode_status
        }

    # -----------------------------------------------------
    # NOT ENOUGH EVIDENCE
    # -----------------------------------------------------

    return {
        "assessment": "INSUFFICIENT_EVIDENCE",
        "summary": (
            "Some package information is consistent with "
            "the reference data, but there is not enough "
            "independently verified information for a "
            "strong authenticity assessment."
        ),
        "mismatch_count": 0,
        "barcode_status": barcode_status
    }


# =========================================================
# HUMAN-READABLE EVIDENCE
# =========================================================

def build_evidence_summary(
    package_result,
    ingredient_result,
    barcode_result
):
    """Create clean human-readable evidence statements."""

    evidence = []

    package_result = package_result or {}
    ingredient_result = ingredient_result or {}
    barcode_result = barcode_result or {}

    # Package matches
    for message in package_result.get("matches", []):
        evidence.append(f"✓ {message}")

    # Package mismatches
    for message in package_result.get("mismatches", []):
        evidence.append(f"⚠ {message}")

    # Detected information
    for message in package_result.get("detected", []):
        evidence.append(f"ℹ {message}")

    # Missing / unverified information
    for message in package_result.get("not_verified", []):
        evidence.append(f"ℹ {message}")

    # Active ingredient
    ingredient_status = ingredient_result.get(
        "status"
    )

    if ingredient_status == "MATCH":
        evidence.append(
            f"✓ {ingredient_result.get('message')}"
        )

    elif ingredient_status == "MISMATCH":
        evidence.append(
            f"⚠ {ingredient_result.get('message')}"
        )

    else:
        evidence.append(
            f"ℹ {ingredient_result.get('message')}"
        )

    # Barcode
    barcode_status = barcode_result.get(
        "status"
    )

    if barcode_status == "MATCH":
        evidence.append(
            f"✓ {barcode_result.get('message')}"
        )

    elif barcode_status == "MISMATCH":
        evidence.append(
            f"⚠ {barcode_result.get('message')}"
        )

    else:
        evidence.append(
            f"ℹ {barcode_result.get('message')}"
        )

    return evidence


# =========================================================
# COMPLETE EVIDENCE REPORT
# =========================================================

def generate_evidence_report(
    medicine_name,
    package_details=None,
    barcode_medicine=None
):

    # -----------------------------------------------------
    # REFERENCE MEDICINE
    # -----------------------------------------------------

    reference_medicine = search_medicine(
        medicine_name
    )

    if reference_medicine is None:

        return {
            "success": False,
            "message": (
                "Medicine was not found in the "
                "reference database."
            )
        }

    # -----------------------------------------------------
    # PACKAGE VERIFICATION
    # -----------------------------------------------------

    package_result = verify_package(
        reference_medicine,
        package_details
    )

    # -----------------------------------------------------
    # ACTIVE INGREDIENT
    # -----------------------------------------------------

    ingredient_result = verify_active_ingredient(
        reference_medicine,
        package_details
    )

    # -----------------------------------------------------
    # BARCODE
    # -----------------------------------------------------

    barcode_result = check_barcode(
        medicine_name,
        barcode_medicine
    )

    # -----------------------------------------------------
    # AUTHENTICITY ASSESSMENT
    # -----------------------------------------------------

    authenticity = assess_authenticity(
        package_result,
        barcode_result,
        ingredient_result
    )

    # -----------------------------------------------------
    # HUMAN-READABLE EVIDENCE
    # -----------------------------------------------------

    evidence = build_evidence_summary(
        package_result,
        ingredient_result,
        barcode_result
    )

    # -----------------------------------------------------
    # FINAL REPORT
    # -----------------------------------------------------

    return {
        "success": True,

        "medicine": reference_medicine.get(
            "medicine"
        ),

        "reference_data": reference_medicine,

        "package": package_details or {},

        "verification": {
            "package": package_result,
            "active_ingredient": ingredient_result,
            "barcode": barcode_result,
            "batch": package_result.get("batch", {})
        },

        "authenticity": authenticity,

        "evidence": evidence
    }


# =========================================================
# BACKWARD-COMPATIBLE ENTRY POINT
# =========================================================

def generate_safety_analysis(
    medicine_name,
    ocr_medicine_name=None,
    barcode_medicine=None
):

    package_details = {
        "medicine": ocr_medicine_name
    }

    return generate_evidence_report(
        medicine_name=medicine_name,
        package_details=package_details,
        barcode_medicine=barcode_medicine
    )