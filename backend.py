from pathlib import Path
import pandas as pd
import re


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
            try:
                df = pd.read_csv(path)
                df.columns = df.columns.str.strip()
                return df
            except Exception:
                return pd.DataFrame()

    return pd.DataFrame()


medicines = load_csv_data("medicines.csv")
interactions = load_csv_data("interactions.csv")
batches = load_csv_data("batches.csv")


# =========================================================
# NORMALIZATION
# =========================================================

def normalize(value):
    """
    Normalize values for reliable comparison.

    Handles:
    - uppercase/lowercase
    - spaces
    - punctuation
    - slash vs hyphen
    - common dash characters
    """

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    value = str(value).strip().lower()

    value = value.replace("–", "-")
    value = value.replace("—", "-")
    value = value.replace("/", "-")

    # Remove spaces and punctuation
    value = re.sub(r"[^a-z0-9]", "", value)

    return value


# =========================================================
# SEARCH MEDICINE
# =========================================================

def search_medicine(name):
    """Search the medicine reference database."""

    if not name or medicines.empty:
        return None

    if "medicine" not in medicines.columns:
        return None

    normalized_name = normalize(name)

    for _, row in medicines.iterrows():

        db_name = normalize(
            row.get("medicine")
        )

        if db_name == normalized_name:
            return row.to_dict()

    return None


# =========================================================
# IDENTIFY MEDICINE FROM OCR
# =========================================================

def identify_medicine_from_ocr(ocr_medicine_name):
    """Find OCR-detected medicine in reference database."""

    if not ocr_medicine_name:
        return None

    return search_medicine(
        ocr_medicine_name
    )


# =========================================================
# FIND TRUSTED BATCH
# =========================================================

def find_batch(
    medicine_name=None,
    batch_number=None
):
    """
    Find a trusted batch record.

    Normal case:
        Search using medicine + batch number.

    If medicine is unavailable:
        Search using batch number only.

    Batch-only lookup is accepted only when exactly
    one local record exists for that batch number.
    """

    if not batch_number or batches.empty:
        return None

    if "batch_number" not in batches.columns:
        return None

    normalized_batch = normalize(
        batch_number
    )

    # -----------------------------------------------------
    # SEARCH BY BATCH NUMBER
    # -----------------------------------------------------

    batch_matches = batches[
        batches["batch_number"]
        .astype(str)
        .apply(normalize)
        == normalized_batch
    ]

    if batch_matches.empty:
        return None

    # -----------------------------------------------------
    # MEDICINE AVAILABLE
    # -----------------------------------------------------

    if medicine_name:

        if "medicine" not in batches.columns:
            return None

        normalized_medicine = normalize(
            medicine_name
        )

        medicine_matches = batch_matches[
            batch_matches["medicine"]
            .astype(str)
            .apply(normalize)
            == normalized_medicine
        ]

        if medicine_matches.empty:
            return None

        return medicine_matches.iloc[0].to_dict()

    # -----------------------------------------------------
    # MEDICINE NOT AVAILABLE
    # -----------------------------------------------------

    # Only use batch-only lookup if unique
    if len(batch_matches) == 1:
        return batch_matches.iloc[0].to_dict()

    return None


# =========================================================
# FIELD COMPARISON
# =========================================================

def compare_field(
    field_name,
    detected_value,
    expected_value
):
    """
    Compare a detected package field with trusted
    reference data.

    Possible statuses:
        MATCH
        MISMATCH
        NOT_VERIFIED
    """

    detected = normalize(
        detected_value
    )

    expected = normalize(
        expected_value
    )

    # -----------------------------------------------------
    # DETECTED VALUE MISSING
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # REFERENCE VALUE MISSING
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # MATCH
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # MISMATCH
    # -----------------------------------------------------

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

def verify_medicine_name(
    selected_medicine,
    ocr_medicine
):

    if not selected_medicine:

        return {
            "status": "NOT_VERIFIED",
            "message": (
                "Reference medicine was not provided."
            )
        }

    if not ocr_medicine:

        return {
            "status": "NOT_VERIFIED",
            "message": (
                "Medicine name could not be identified "
                "from the package."
            )
        }

    if (
        normalize(selected_medicine)
        == normalize(ocr_medicine)
    ):

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
    Verify active ingredient only when independently
    detected from the package.
    """

    if not reference_medicine:

        return {
            "status": "NOT_VERIFIED",
            "message": (
                "Reference medicine is unavailable."
            )
        }

    reference_ingredient = normalize(
        reference_medicine.get(
            "active ingredient"
        )
    )

    detected_ingredient = normalize(
        (package_details or {}).get(
            "active_ingredient"
        )
    )

    # -----------------------------------------------------
    # NO REFERENCE
    # -----------------------------------------------------

    if not reference_ingredient:

        return {
            "status": "NOT_VERIFIED",
            "message": (
                "No active ingredient reference data "
                "is available."
            )
        }

    # -----------------------------------------------------
    # NOT DETECTED
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # MATCH
    # -----------------------------------------------------

    if (
        detected_ingredient
        == reference_ingredient
    ):

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

    # -----------------------------------------------------
    # MISMATCH
    # -----------------------------------------------------

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

    Checks:
        - Batch Number
        - Manufacturing Date
        - Expiry Date
        - MRP
        - Licence Number

    If medicine is unavailable, batch number alone can be
    used when it uniquely identifies one trusted local
    batch record.

    Missing local batch records are NOT treated as proof
    of counterfeit medicine.
    """

    package_details = package_details or {}

    batch_number = package_details.get(
        "batch_number"
    )

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
    # SEARCH TRUSTED BATCH
    # -----------------------------------------------------

    trusted_batch = find_batch(
        medicine_name=medicine_name,
        batch_number=batch_number
    )

    # -----------------------------------------------------
    # BATCH NOT FOUND
    # -----------------------------------------------------

    if trusted_batch is None:

        detected = [
            f"Batch number detected: {batch_number}."
        ]

        not_verified = [
            (
                f"Batch '{batch_number}' was not found "
                "in the local trusted batch database."
            )
        ]

        return {
            "status": "NOT_VERIFIED",
            "batch_found": False,
            "signals": [],
            "matches": [],
            "mismatches": [],
            "detected": detected,
            "not_verified": not_verified
        }

    signals = []
    matches = []
    mismatches = []
    detected = []
    not_verified = []

    # -----------------------------------------------------
    # HELPER
    # -----------------------------------------------------

    def process_result(result):

        signals.append(result)

        if result["status"] == "MATCH":
            matches.append(
                result["message"]
            )

        elif result["status"] == "MISMATCH":
            mismatches.append(
                result["message"]
            )

        elif result["status"] == "NOT_VERIFIED":
            not_verified.append(
                result["message"]
            )

    # -----------------------------------------------------
    # BATCH NUMBER
    # -----------------------------------------------------

    result = compare_field(
        "Batch Number",
        batch_number,
        trusted_batch.get(
            "batch_number"
        )
    )

    process_result(result)

    # -----------------------------------------------------
    # MANUFACTURING DATE
    # -----------------------------------------------------

    result = compare_field(
        "Manufacturing Date",
        package_details.get(
            "manufacturing_date"
        ),
        trusted_batch.get(
            "manufacturing_date"
        )
    )

    process_result(result)

    # -----------------------------------------------------
    # EXPIRY DATE
    # -----------------------------------------------------

    result = compare_field(
        "Expiry Date",
        package_details.get(
            "expiry_date"
        ),
        trusted_batch.get(
            "expiry_date"
        )
    )

    process_result(result)

    # -----------------------------------------------------
    # MRP
    # -----------------------------------------------------

    result = compare_field(
        "MRP",
        package_details.get(
            "mrp"
        ),
        trusted_batch.get(
            "mrp"
        )
    )

    process_result(result)

    # -----------------------------------------------------
    # LICENCE NUMBER
    # -----------------------------------------------------

    result = compare_field(
        "Licence Number",
        package_details.get(
            "licence_number"
        ),
        trusted_batch.get(
            "licence_number"
        )
    )

    process_result(result)

    # -----------------------------------------------------
    # FINAL STATUS
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

def verify_package(
    reference_medicine,
    package_details
):
    """
    Overall package verification.

    This does NOT replace Verify Batch.
    Batch verification is performed through verify_batch().
    """

    package_details = package_details or {}

    signals = []
    matches = []
    mismatches = []
    detected = []
    not_verified = []

    # -----------------------------------------------------
    # NO REFERENCE MEDICINE
    # -----------------------------------------------------

    if not reference_medicine:

        # Medicine itself cannot be verified
        if package_details.get("medicine"):

            message = (
                f"Medicine detected: "
                f"{package_details['medicine']}, "
                "but no matching reference record was found."
            )

            signals.append({
                "field": "Medicine",
                "status": "DETECTED",
                "detected": package_details["medicine"],
                "expected": None,
                "message": message
            })

            detected.append(message)

        else:

            message = (
                "Medicine name could not be identified "
                "from the package."
            )

            signals.append({
                "field": "Medicine",
                "status": "NOT_VERIFIED",
                "detected": None,
                "expected": None,
                "message": message
            })

            not_verified.append(message)

        # -------------------------------------------------
        # STRENGTH
        # -------------------------------------------------

        if package_details.get("strength"):

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

        # -------------------------------------------------
        # MANUFACTURER
        # -------------------------------------------------

        if package_details.get("manufacturer"):

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

        # -------------------------------------------------
        # BATCH VERIFICATION
        # -------------------------------------------------

        batch_result = verify_batch(
            None,
            package_details
        )

        signals.extend(
            batch_result.get(
                "signals", []
            )
        )

        matches.extend(
            batch_result.get(
                "matches", []
            )
        )

        mismatches.extend(
            batch_result.get(
                "mismatches", []
            )
        )

        detected.extend(
            batch_result.get(
                "detected", []
            )
        )

        not_verified.extend(
            batch_result.get(
                "not_verified", []
            )
        )

        return {
            "status": (
                "MISMATCH"
                if mismatches
                else (
                    "CONSISTENT"
                    if matches
                    else "NOT_VERIFIED"
                )
            ),
            "signals": signals,
            "matches": matches,
            "mismatches": mismatches,
            "detected": detected,
            "not_verified": not_verified,
            "batch": batch_result
        }

    # =====================================================
    # REFERENCE MEDICINE AVAILABLE
    # =====================================================

    # -----------------------------------------------------
    # MEDICINE NAME
    # -----------------------------------------------------

    medicine_result = verify_medicine_name(
        reference_medicine.get(
            "medicine"
        ),
        package_details.get(
            "medicine"
        )
    )

    signals.append(
        medicine_result
    )

    if medicine_result["status"] == "MATCH":

        matches.append(
            medicine_result["message"]
        )

    elif medicine_result["status"] == "MISMATCH":

        mismatches.append(
            medicine_result["message"]
        )

    else:

        not_verified.append(
            medicine_result["message"]
        )

    # -----------------------------------------------------
    # STRENGTH
    # -----------------------------------------------------

    if (
        "strength"
        in reference_medicine
    ):

        result = compare_field(
            "Strength",
            package_details.get(
                "strength"
            ),
            reference_medicine.get(
                "strength"
            )
        )

        signals.append(result)

        if result["status"] == "MATCH":
            matches.append(
                result["message"]
            )

        elif result["status"] == "MISMATCH":
            mismatches.append(
                result["message"]
            )

        else:
            not_verified.append(
                result["message"]
            )

    elif package_details.get(
        "strength"
    ):

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

    if (
        "manufacturer"
        in reference_medicine
    ):

        result = compare_field(
            "Manufacturer",
            package_details.get(
                "manufacturer"
            ),
            reference_medicine.get(
                "manufacturer"
            )
        )

        signals.append(result)

        if result["status"] == "MATCH":
            matches.append(
                result["message"]
            )

        elif result["status"] == "MISMATCH":
            mismatches.append(
                result["message"]
            )

        else:
            not_verified.append(
                result["message"]
            )

    elif package_details.get(
        "manufacturer"
    ):

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

        message = (
            "Manufacturer was not detected."
        )

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
        reference_medicine.get(
            "medicine"
        ),
        package_details
    )

    signals.extend(
        batch_result.get(
            "signals", []
        )
    )

    matches.extend(
        batch_result.get(
            "matches", []
        )
    )

    mismatches.extend(
        batch_result.get(
            "mismatches", []
        )
    )

    detected.extend(
        batch_result.get(
            "detected", []
        )
    )

    not_verified.extend(
        batch_result.get(
            "not_verified", []
        )
    )

    # -----------------------------------------------------
    # FINAL STATUS
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

def check_barcode(
    medicine_name,
    barcode_medicine
):

    if not barcode_medicine:

        return {
            "status": "NOT_VERIFIED",
            "message": (
                "Barcode was not detected."
            )
        }

    if not medicine_name:

        return {
            "status": "NOT_VERIFIED",
            "message": (
                "Reference medicine is unavailable."
            )
        }

    if (
        normalize(barcode_medicine)
        == normalize(medicine_name)
    ):

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

def check_interaction(
    medicine1,
    medicine2
):

    if (
        not medicine1
        or not medicine2
        or interactions.empty
    ):
        return None

    if (
        "medicine_1" not in interactions.columns
        or "medicine_2" not in interactions.columns
    ):
        return None

    medicine1 = normalize(
        medicine1
    )

    medicine2 = normalize(
        medicine2
    )

    med1 = interactions[
        "medicine_1"
    ].astype(str).apply(normalize)

    med2 = interactions[
        "medicine_2"
    ].astype(str).apply(normalize)

    result = interactions[
        (
            (med1 == medicine1)
            & (med2 == medicine2)
        )
        |
        (
            (med1 == medicine2)
            & (med2 == medicine1)
        )
    ]

    if result.empty:

        return {
            "found": False,
            "status": (
                "No recorded interaction found."
            )
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

    package_result = (
        package_result or {}
    )

    barcode_result = (
        barcode_result or {}
    )

    ingredient_result = (
        ingredient_result or {}
    )

    mismatches = len(
        package_result.get(
            "mismatches",
            []
        )
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

        mismatch_count = (
            mismatches
            + (
                1
                if barcode_status == "MISMATCH"
                else 0
            )
            + (
                1
                if ingredient_status == "MISMATCH"
                else 0
            )
        )

        return {
            "status": "SUSPICIOUS",
            "assessment": "SUSPICIOUS",
            "summary": (
                "One or more verification inconsistencies "
                "were detected in the available package data."
            ),
            "mismatch_count": mismatch_count,
            "barcode_status": barcode_status
        }

    # -----------------------------------------------------
    # STRONGER POSITIVE EVIDENCE
    # -----------------------------------------------------

    verified_matches = len(
        package_result.get(
            "matches",
            []
        )
    )

    barcode_match = (
        barcode_status == "MATCH"
    )

    ingredient_match = (
        ingredient_status == "MATCH"
    )

    if barcode_match:

        return {
            "status": "NO_MAJOR_INCONSISTENCY",
            "assessment": "NO_MAJOR_INCONSISTENCY",
            "summary": (
                "The available package information and "
                "barcode data are consistent with the "
                "reference data."
            ),
            "mismatch_count": 0,
            "barcode_status": barcode_status
        }

    if (
        verified_matches >= 2
        or ingredient_match
    ):

        return {
            "status": "NO_MAJOR_INCONSISTENCY",
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
        "status": "INSUFFICIENT_EVIDENCE",
        "assessment": "INSUFFICIENT_EVIDENCE",
        "summary": (
            "Some package information is available, but "
            "there is not enough independently verified "
            "information for a stronger assessment."
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

    package_result = (
        package_result or {}
    )

    ingredient_result = (
        ingredient_result or {}
    )

    barcode_result = (
        barcode_result or {}
    )

    # -----------------------------------------------------
    # PACKAGE MATCHES
    # -----------------------------------------------------

    for message in package_result.get(
        "matches",
        []
    ):

        evidence.append(
            f"✓ {message}"
        )

    # -----------------------------------------------------
    # PACKAGE MISMATCHES
    # -----------------------------------------------------

    for message in package_result.get(
        "mismatches",
        []
    ):

        evidence.append(
            f"⚠ {message}"
        )

    # -----------------------------------------------------
    # DETECTED INFORMATION
    # -----------------------------------------------------

    for message in package_result.get(
        "detected",
        []
    ):

        evidence.append(
            f"ℹ {message}"
        )

    # -----------------------------------------------------
    # UNVERIFIED INFORMATION
    # -----------------------------------------------------

    for message in package_result.get(
        "not_verified",
        []
    ):

        evidence.append(
            f"ℹ {message}"
        )

    # -----------------------------------------------------
    # ACTIVE INGREDIENT
    # -----------------------------------------------------

    ingredient_status = (
        ingredient_result.get(
            "status"
        )
    )

    ingredient_message = (
        ingredient_result.get(
            "message"
        )
    )

    if ingredient_message:

        if ingredient_status == "MATCH":

            evidence.append(
                f"✓ {ingredient_message}"
            )

        elif ingredient_status == "MISMATCH":

            evidence.append(
                f"⚠ {ingredient_message}"
            )

        else:

            evidence.append(
                f"ℹ {ingredient_message}"
            )

    # -----------------------------------------------------
    # BARCODE
    # -----------------------------------------------------

    barcode_status = (
        barcode_result.get(
            "status"
        )
    )

    barcode_message = (
        barcode_result.get(
            "message"
        )
    )

    if barcode_message:

        if barcode_status == "MATCH":

            evidence.append(
                f"✓ {barcode_message}"
            )

        elif barcode_status == "MISMATCH":

            evidence.append(
                f"⚠ {barcode_message}"
            )

        else:

            evidence.append(
                f"ℹ {barcode_message}"
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
    """
    Generate the complete MediGuard evidence report.

    Important:
    Medicine identification is NOT required for batch
    verification if a unique batch record exists.
    """

    package_details = (
        package_details or {}
    )

    # -----------------------------------------------------
    # REFERENCE MEDICINE
    # -----------------------------------------------------

    reference_medicine = None

    if medicine_name:

        reference_medicine = search_medicine(
            medicine_name
        )

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

    ingredient_result = (
        verify_active_ingredient(
            reference_medicine,
            package_details
        )
        if reference_medicine
        else {
            "status": "NOT_VERIFIED",
            "message": (
                "Active ingredient could not be "
                "verified because the medicine "
                "reference was not identified."
            )
        }
    )

    # -----------------------------------------------------
    # BATCH
    # -----------------------------------------------------

    batch_result = package_result.get(
        "batch",
        {}
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
    # MEDICINE LABEL
    # -----------------------------------------------------

    if reference_medicine:

        medicine_label = (
            reference_medicine.get(
                "medicine"
            )
        )

    elif package_details.get(
        "medicine"
    ):

        medicine_label = (
            package_details.get(
                "medicine"
            )
        )

    else:

        medicine_label = None

    # -----------------------------------------------------
    # FINAL REPORT
    # -----------------------------------------------------

    return {
        "success": True,

        "medicine": medicine_label,

        "reference_available": (
            reference_medicine is not None
        ),

        "reference_data": (
            reference_medicine
            if reference_medicine
            else {}
        ),

        "package": package_details,

        "verification": {
            "package": package_result,

            "active_ingredient": (
                ingredient_result
            ),

            "barcode": barcode_result,

            "batch": batch_result
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