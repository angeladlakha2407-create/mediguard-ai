import re
import os
import shutil
import pytesseract

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from difflib import SequenceMatcher


# ============================================================
# CROSS-PLATFORM TESSERACT PATH CONFIGURATION
# ============================================================

def configure_tesseract():

    # 1. Check system PATH first
    #    This is what Streamlit Cloud will normally use.
    tesseract_in_path = shutil.which("tesseract")

    if tesseract_in_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_in_path
        return

    # 2. Windows fallback paths
    windows_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(
            r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
        ),
    ]

    for path in windows_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return


configure_tesseract()


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_image(image):

    image = image.convert("RGB")

    width, height = image.size

    # Upscale image
    try:
        resample_filter = Image.Resampling.LANCZOS
    except AttributeError:
        resample_filter = Image.ANTIALIAS

    image = image.resize(
        (width * 2, height * 2),
        resample_filter
    )

    # Grayscale
    image = ImageOps.grayscale(image)

    # Improve contrast
    image = ImageEnhance.Contrast(image).enhance(2.2)

    # Improve sharpness
    image = ImageEnhance.Sharpness(image).enhance(2)

    # Sharpen
    image = image.filter(ImageFilter.SHARPEN)

    return image


# ============================================================
# OCR TEXT EXTRACTION
# ============================================================

def extract_text(image):

    """
    Extract text using multiple Tesseract page segmentation modes.

    Using more than one OCR pass helps when medicine names are
    printed in unusual layouts or broken into multiple pieces.
    """

    processed_image = preprocess_image(image)

    ocr_results = []

    configs = [
        "--psm 6",
        "--psm 11",
    ]

    for config in configs:

        try:

            text = pytesseract.image_to_string(
                processed_image,
                config=config
            )

            if text:
                ocr_results.append(text)

        except Exception as e:

            print(
                "OCR ERROR:",
                str(e)
            )

    combined_text = "\n".join(
        ocr_results
    )

    print("========== OCR RESULT ==========")
    print(repr(combined_text))
    print("================================")

    return combined_text.strip()


# ============================================================
# NORMALIZE OCR TEXT
# ============================================================

def normalize_text(text):

    """
    Converts OCR text into a comparison-friendly format.
    """

    if text is None:
        return ""

    text = str(text).lower()

    # Common OCR separators
    text = text.replace("|", " ")
    text = text.replace("_", " ")

    # Normalize dash characters
    text = text.replace("–", "-")
    text = text.replace("—", "-")

    # Keep letters, numbers and spaces
    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text
    )

    # Remove extra spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# NORMALIZE INDIVIDUAL FIELD
# ============================================================

def normalize_field(value):

    """
    Useful for comparing OCR values with CSV values.

    Example:

        DEMO-LIC-050
        demo lic 050

    Both become:

        demolic050
    """

    if value is None:
        return ""

    return re.sub(
        r"[^a-z0-9]",
        "",
        str(value).lower()
    )


# ============================================================
# COMPACT TEXT
# ============================================================

def compact_text(value):

    """
    Removes all spaces and special characters.

    Example:

        AM Ox! Cc | LLI N

    becomes approximately:

        amoxccllin
    """

    if value is None:
        return ""

    return re.sub(
        r"[^a-z0-9]",
        "",
        str(value).lower()
    )


# ============================================================
# STRING SIMILARITY
# ============================================================

def similarity_score(value1, value2):

    value1 = compact_text(value1)
    value2 = compact_text(value2)

    if not value1 or not value2:
        return 0.0

    return SequenceMatcher(
        None,
        value1,
        value2
    ).ratio()


# ============================================================
# MEDICINE IDENTIFICATION
# ============================================================

def identify_medicine(text, medicines_df):

    """
    
    Robust medicine identification from noisy OCR.

    Handles OCR like:
        AM Ox! Cc | LLI N Batch No: AC250318

    and matches it against:
        Amoxicillin
    """

    import re
    from difflib import SequenceMatcher

    print("\n========== MEDICINE MATCHING ==========")

    if text is None or not str(text).strip():
        print("OCR TEXT EMPTY")
        print("====================================")
        return None

    if medicines_df is None or medicines_df.empty:
        print("MEDICINE DATABASE EMPTY")
        print("====================================")
        return None

    # ---------------------------------------------------------
    # 1. Find medicine column
    # ---------------------------------------------------------

    medicine_column = None

    for col in medicines_df.columns:
        if str(col).strip().lower() == "medicine":
            medicine_column = col
            break

    if medicine_column is None:
        print("NO 'medicine' COLUMN FOUND")
        print("====================================")
        return None

    # ---------------------------------------------------------
    # 2. Normalization helpers
    # ---------------------------------------------------------

    def normalize(value):
        if value is None:
            return ""

        value = str(value).lower()

        # OCR punctuation -> spaces
        value = re.sub(r"[^a-z0-9]+", " ", value)

        # Remove extra spaces
        value = re.sub(r"\s+", " ", value).strip()

        return value

    def compact(value):
        return re.sub(r"[^a-z0-9]", "", str(value).lower())

    def similarity(a, b):
        return SequenceMatcher(
            None,
            compact(a),
            compact(b)
        ).ratio()

    # ---------------------------------------------------------
    # 3. Prepare medicine database
    # ---------------------------------------------------------

    medicines = []

    for value in medicines_df[medicine_column].dropna():
        medicine = str(value).strip()

        if not medicine:
            continue

        medicines.append({
            "original": medicine,
            "normalized": normalize(medicine),
            "compact": compact(medicine)
        })

    if not medicines:
        print("NO MEDICINES FOUND IN CSV")
        print("====================================")
        return None

    # ---------------------------------------------------------
    # 4. Print normalized OCR
    # ---------------------------------------------------------

    normalized_full = normalize(text)

    print("OCR NORMALIZED:")
    print(normalized_full)

    # ---------------------------------------------------------
    # 5. Exact matching against complete OCR
    # ---------------------------------------------------------

    for med in medicines:

        if med["normalized"] in normalized_full:
            print("EXACT MATCH:", med["original"])
            print("====================================")
            return med["original"]

    # ---------------------------------------------------------
    # 6. Compact exact matching
    # ---------------------------------------------------------

    compact_ocr = compact(text)

    for med in medicines:

        if med["compact"] in compact_ocr:
            print("COMPACT EXACT MATCH:", med["original"])
            print("====================================")
            return med["original"]

    # ---------------------------------------------------------
    # 7. Extract ONLY relevant OCR lines
    # ---------------------------------------------------------

    raw_lines = str(text).splitlines()

    relevant_lines = []

    ignored_keywords = [
        "manufacturer",
        "mfg",
        "exp",
        "expiry",
        "mrp",
        "licence",
        "license",
        "batch",
        "batch no",
        "manufactured",
        "marketed by"
    ]

    for line in raw_lines:

        line = line.strip()

        if not line:
            continue

        lower_line = line.lower()

        # -----------------------------------------------------
        # Important:
        # If medicine and Batch are on SAME line,
        # keep everything BEFORE "Batch".
        # -----------------------------------------------------

        batch_match = re.search(
            r"\b(?:batch\s*(?:no|number)?|lot\s*(?:no|number)?)\b",
            lower_line
        )

        if batch_match:
            line = line[:batch_match.start()].strip()
            lower_line = line.lower()

        if not line:
            continue

        # Ignore metadata lines
        if any(keyword in lower_line for keyword in ignored_keywords):
            continue

        relevant_lines.append(line)

    print("\nRELEVANT OCR LINES:")
    for line in relevant_lines:
        print(repr(line))

    # ---------------------------------------------------------
    # 8. Create OCR tokens
    # ---------------------------------------------------------

    candidate_tokens = []

    for line in relevant_lines:

        # Keep alphabetic chunks
        tokens = re.findall(r"[A-Za-z]+", line)

        for token in tokens:

            token = token.lower().strip()

            if not token:
                continue

            candidate_tokens.append(token)

    print("\nMEDICINE CANDIDATE TOKENS:")
    print(candidate_tokens)

    # ---------------------------------------------------------
    # 9. Remove obvious non-medicine OCR garbage
    # ---------------------------------------------------------

    garbage = {
        "tablets",
        "tablet",
        "capsules",
        "capsule",
        "mg",
        "ml",
        "g",
        "kg",
        "usp",
        "ip",
        "bp",
        "for",
        "oral",
        "use",
        "only",
        "each",
        "contains",
        "film",
        "coated",
        "composition",
        "strength"
    }

    candidate_tokens = [
        token
        for token in candidate_tokens
        if token not in garbage
    ]

    # ---------------------------------------------------------
    # 10. Generate joined OCR candidates
    #
    # AM + Ox + Cc + LLI + N
    #
    # becomes:
    # amoxccllin
    #
    # which can then be fuzzy matched against:
    # amoxicillin
    # ---------------------------------------------------------

    joined_candidates = []

    # Individual tokens
    for token in candidate_tokens:
        if len(token) >= 2:
            joined_candidates.append(token)

    # Consecutive token combinations
    max_window = min(7, len(candidate_tokens))

    for window in range(2, max_window + 1):

        for i in range(len(candidate_tokens) - window + 1):

            chunk = candidate_tokens[i:i + window]

            joined = "".join(chunk)

            if len(joined) >= 4:
                joined_candidates.append(joined)

    # Remove duplicates while preserving order
    seen = set()
    unique_candidates = []

    for candidate in joined_candidates:

        if candidate not in seen:
            seen.add(candidate)
            unique_candidates.append(candidate)

    joined_candidates = unique_candidates

    print("\nJOINED OCR CANDIDATES:")
    print(joined_candidates)

    # ---------------------------------------------------------
    # 11. Fuzzy matching
    # ---------------------------------------------------------

    best_medicine = None
    best_candidate = None
    best_score = 0.0

    for candidate in joined_candidates:

        for med in medicines:

            score = similarity(candidate, med["compact"])

            if score > best_score:

                best_score = score
                best_medicine = med["original"]
                best_candidate = candidate

    print("\nBEST JOINED MATCH:")
    print(best_candidate)

    print("BEST MEDICINE:")
    print(best_medicine)

    print("BEST SCORE:")
    print(round(best_score, 4))

    # ---------------------------------------------------------
    # 12. Normal fuzzy threshold
    # ---------------------------------------------------------

    threshold = 0.68

    print("THRESHOLD:")
    print(threshold)

    if best_medicine and best_score >= threshold:

        print("\nFINAL FUZZY MATCH:")
        print(best_medicine)

        print("====================================")

        return best_medicine

    # ---------------------------------------------------------
    # 13. Character-window fallback
    #
    # Useful if OCR inserted spaces/punctuation badly.
    # ---------------------------------------------------------

    print("\nFINAL FUZZY MATCH:")
    print("NONE")

    best_window_medicine = None
    best_window_score = 0.0
    best_window = None

    compact_text = compact(text)

    for med in medicines:

        target = med["compact"]

        if len(target) < 4:
            continue

        window_length = len(target)

        # Search around the target length
        for extra in range(-2, 3):

            current_length = window_length + extra

            if current_length < 4:
                continue

            for i in range(
                0,
                max(0, len(compact_text) - current_length + 1)
            ):

                window = compact_text[
                    i:i + current_length
                ]

                score = SequenceMatcher(
                    None,
                    window,
                    target
                ).ratio()

                if score > best_window_score:

                    best_window_score = score
                    best_window_medicine = med["original"]
                    best_window = window

    print("\nWINDOW FALLBACK:")
    print("BEST WINDOW:", best_window)
    print("BEST MEDICINE:", best_window_medicine)
    print("BEST SCORE:", round(best_window_score, 4))

    if (
        best_window_medicine
        and best_window_score >= 0.72
    ):

        print("\nFINAL WINDOW MATCH:")
        print(best_window_medicine)

        print("====================================")

        return best_window_medicine

    print("\nNO MEDICINE MATCH FOUND")
    print("====================================")

    return None

# ============================================================
# PACKAGE DETAIL EXTRACTION
# ============================================================

def extract_package_details(ocr_text):

    text = normalize_text(
        ocr_text
    )

    details = {
        "medicine": None,
        "strength": None,
        "manufacturer": None,
        "batch_number": None,
        "manufacturing_date": None,
        "expiry_date": None,
        "mrp": None,
        "licence_number": None,
        "raw_text": ocr_text
    }

    if not text:
        return details

    # ========================================================
    # STRENGTH
    # ========================================================

    strength_match = re.search(
        r"\b"
        r"\d+(?:\.\d+)?"
        r"\s*"
        r"(?:mg|mcg|g|ml|iu)"
        r"\b",
        text,
        re.IGNORECASE
    )

    if strength_match:

        details["strength"] = (
            strength_match
            .group(0)
            .strip()
        )

    # ========================================================
    # RAW OCR LINES
    # ========================================================

    raw_lines = str(
        ocr_text
    ).splitlines()

    cleaned_lines = []

    for line in raw_lines:

        line = re.sub(
            r"\s+",
            " ",
            line
        ).strip()

        cleaned_lines.append(
            line
        )

    # ========================================================
    # MANUFACTURER
    # ========================================================

    for i, line in enumerate(
        cleaned_lines
    ):

        manufacturer_match = re.search(
            r"\bmanufacturer\b"
            r"\s*[:\-]?\s*(.*)",
            line,
            re.IGNORECASE
        )

        if not manufacturer_match:
            continue

        manufacturer_parts = []

        first_part = (
            manufacturer_match
            .group(1)
            .strip()
        )

        # Remove trailing OCR garbage
        first_part = re.sub(
            r"[\|\!\_]+$",
            "",
            first_part
        ).strip()

        if first_part:
            manufacturer_parts.append(
                first_part
            )

        # ----------------------------------------------------
        # Continuation lines
        # ----------------------------------------------------

        j = i + 1

        while j < len(
            cleaned_lines
        ):

            next_line = (
                cleaned_lines[j]
                .strip()
            )

            if not next_line:
                break

            # Stop at another package field
            if re.search(
                r"\b(?:"
                r"batch"
                r"|b\.?\s*no"
                r"|mfg"
                r"|mfd"
                r"|manufacturing"
                r"|manufactured"
                r"|exp"
                r"|expiry"
                r"|expires"
                r"|mrp"
                r"|licence"
                r"|license"
                r"|lic"
                r")\b",
                next_line,
                re.IGNORECASE
            ):
                break

            manufacturer_parts.append(
                next_line
            )

            j += 1

        if manufacturer_parts:

            manufacturer = " ".join(
                manufacturer_parts
            )

            manufacturer = re.sub(
                r"[^A-Za-z0-9.&,+()'/\- ]",
                "",
                manufacturer
            )

            manufacturer = re.sub(
                r"\s+",
                " ",
                manufacturer
            ).strip()

            details[
                "manufacturer"
            ] = manufacturer

            break

    # ========================================================
    # BATCH NUMBER
    # ========================================================

    batch_match = re.search(
        r"(?:"
        r"batch\s*(?:no|number)?"
        r"|b\.?\s*no\.?"
        r")"
        r"\s*[:\-]?\s*"
        r"([a-z0-9][a-z0-9\/\-]*)",
        text,
        re.IGNORECASE
    )

    if batch_match:

        details[
            "batch_number"
        ] = (
            batch_match
            .group(1)
            .strip()
        )

    # ========================================================
    # MRP
    # ========================================================

    mrp_match = re.search(
        r"(?:"
        r"mrp"
        r"|m\.?r\.?p\.?"
        r")"
        r"\s*"
        r"(?:rs\.?|₹|\$)?"
        r"\s*"
        r"([0-9]+(?:\.[0-9]+)?)",
        text,
        re.IGNORECASE
    )

    if mrp_match:

        mrp = (
            mrp_match
            .group(1)
            .strip()
        )

        try:

            mrp_value = float(
                mrp
            )

            if mrp_value.is_integer():
                mrp = str(
                    int(mrp_value)
                )

        except ValueError:
            pass

        details["mrp"] = mrp

    # ========================================================
    # MANUFACTURING DATE
    # ========================================================

    mfg_match = re.search(
        r"(?:"
        r"mfg"
        r"|mfd"
        r"|manufactured"
        r"|manufacturing"
        r")"
        r"\s*[:\-]?\s*"
        r"(\d{1,2})"
        r"\s*"
        r"[\/\-\s]"
        r"\s*"
        r"(\d{4})",
        text,
        re.IGNORECASE
    )

    if mfg_match:

        month = int(
            mfg_match.group(1)
        )

        year = (
            mfg_match.group(2)
        )

        if 1 <= month <= 12:

            details[
                "manufacturing_date"
            ] = (
                f"{month:02d}/{year}"
            )

    # ========================================================
    # EXPIRY DATE
    # ========================================================

    expiry_match = re.search(
        r"(?:"
        r"exp"
        r"|expiry"
        r"|expires"
        r"|expiration"
        r")"
        r"\s*[:\-]?\s*"
        r"(\d{1,2})"
        r"\s*"
        r"[\/\-\s]"
        r"\s*"
        r"(\d{4})",
        text,
        re.IGNORECASE
    )

    if expiry_match:

        month = int(
            expiry_match.group(1)
        )

        year = (
            expiry_match.group(2)
        )

        if 1 <= month <= 12:

            details[
                "expiry_date"
            ] = (
                f"{month:02d}/{year}"
            )

    # ========================================================
    # LICENCE NUMBER
    # ========================================================

    licence_match = re.search(
        r"(?:"
        r"licence"
        r"|license"
        r"|lic"
        r")"
        r"\s*"
        r"(?:no|number)?"
        r"\s*[:\-]?\s*"
        r"([a-z0-9][a-z0-9\/\-\s]*)",
        text,
        re.IGNORECASE
    )

    if licence_match:

        licence_number = (
            licence_match
            .group(1)
            .strip()
        )

        # Stop at another known package field
        licence_number = re.split(
            r"\s+"
            r"(?:"
            r"manufacturer"
            r"|batch"
            r"|mfg"
            r"|mfd"
            r"|manufacturing"
            r"|exp"
            r"|expiry"
            r"|mrp"
            r")"
            r"\b",
            licence_number,
            maxsplit=1,
            flags=re.IGNORECASE
        )[0].strip()

        details[
            "licence_number"
        ] = licence_number

    return details


# ============================================================
# COMPLETE PACKAGE ANALYSIS
# ============================================================

def analyze_package(
    image,
    medicines=None
):

    # Step 1: OCR
    ocr_text = extract_text(
        image
    )

    # Step 2: Extract package details
    package_details = (
        extract_package_details(
            ocr_text
        )
    )

    # Step 3: Identify medicine
    if medicines is not None:

        package_details[
            "medicine"
        ] = identify_medicine(
            ocr_text,
            medicines
        )

    return package_details