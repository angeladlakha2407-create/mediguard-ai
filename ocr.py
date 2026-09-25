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
    # 1. Check system PATH first (Linux / Streamlit Cloud)
    tesseract_in_path = shutil.which("tesseract")
    if tesseract_in_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_in_path
        return

    # 2. Windows fallback paths
    windows_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]

    for path in windows_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return

configure_tesseract()


# ============================================================
# OCR TEXT EXTRACTION
# ============================================================

def extract_text(image):
    """
    Preprocess image and extract text using Tesseract.
    """

    image = image.convert("RGB")

    width, height = image.size

    # Upscale image using non-deprecated resample filter
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
    image = ImageEnhance.Contrast(image).enhance(2)

    # Sharpen
    image = image.filter(ImageFilter.SHARPEN)

    # OCR
    text = pytesseract.image_to_string(
        image,
        config="--psm 6"
    )

    print("========== OCR RESULT ==========")
    print(repr(text))
    print("================================")

    return text.strip()


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

    # Remove common OCR separators
    text = text.replace("|", " ")
    text = text.replace("_", " ")

    # Keep only letters, numbers and spaces
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
        DEMO-LIC-031
        demo lic 031

    Both become:
        demolic031
    """

    if value is None:
        return ""

    return re.sub(
        r"[^a-z0-9]",
        "",
        str(value).lower()
    )


# ============================================================
# MEDICINE IDENTIFICATION
# ============================================================

def identify_medicine(ocr_text, medicines):

    text = normalize_text(ocr_text)

    if (
        not text
        or medicines is None
        or "medicine" not in medicines.columns
    ):
        return None

    print("========== MEDICINE MATCHING ==========")
    print("OCR NORMALIZED:")
    print(text)

    # Remove spaces completely.
    # This helps with OCR such as:
    #
    # ROSUVASTATI N
    #
    # becoming:
    #
    # rosuvastatin

    compact_text = re.sub(
        r"[^a-z0-9]",
        "",
        text
    )

    candidates = []

    for medicine in medicines["medicine"].dropna():

        original_name = str(medicine).strip()

        if not original_name:
            continue

        normalized_name = normalize_text(
            original_name
        )

        compact_name = re.sub(
            r"[^a-z0-9]",
            "",
            normalized_name
        )

        if compact_name:
            candidates.append(
                (
                    original_name,
                    normalized_name,
                    compact_name
                )
            )

    # Try longer names first
    candidates.sort(
        key=lambda x: len(x[2]),
        reverse=True
    )

    # --------------------------------------------------------
    # METHOD 1: NORMAL EXACT MATCH
    # --------------------------------------------------------

    for (
        original_name,
        normalized_name,
        compact_name
    ) in candidates:

        pattern = (
            r"\b"
            + re.escape(normalized_name)
            + r"\b"
        )

        if re.search(
            pattern,
            text
        ):

            print(
                "MATCH FOUND:",
                original_name
            )

            return original_name

    # --------------------------------------------------------
    # METHOD 2: REMOVE OCR SPACES
    # --------------------------------------------------------

    for (
        original_name,
        normalized_name,
        compact_name
    ) in candidates:

        if compact_name in compact_text:

            print(
                "MATCH FOUND AFTER "
                "REMOVING OCR SPACES:",
                original_name
            )

            return original_name

    # --------------------------------------------------------
    # METHOD 3: FUZZY MATCH
    # --------------------------------------------------------

    for (
        original_name,
        normalized_name,
        compact_name
    ) in candidates:

        medicine_length = len(
            compact_name
        )

        # Avoid matching extremely short names
        if medicine_length < 4:
            continue

        min_len = max(
            4,
            medicine_length - 2
        )

        max_len = (
            medicine_length + 2
        )

        for length in range(
            min_len,
            max_len + 1
        ):

            for i in range(
                0,
                len(compact_text) - length + 1
            ):

                chunk = compact_text[
                    i:i + length
                ]

                score = SequenceMatcher(
                    None,
                    compact_name,
                    chunk
                ).ratio()

                if score >= 0.90:

                    print(
                        "FUZZY MATCH:",
                        original_name,
                        "score:",
                        round(score, 3)
                    )

                    return original_name

    print("NO MEDICINE MATCH FOUND")
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
    # MANUFACTURER
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


    manufacturer_found = False

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


        # Text after "Manufacturer:"
        first_part = (
            manufacturer_match
            .group(1)
            .strip()
        )

        # Remove OCR garbage at end
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
        # Collect continuation lines
        # ----------------------------------------------------

        j = i + 1

        while j < len(
            cleaned_lines
        ):

            next_line = (
                cleaned_lines[j]
                .strip()
            )


            # Blank line = manufacturer section ended
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


            # Add continuation line
            manufacturer_parts.append(
                next_line
            )

            j += 1


        if manufacturer_parts:

            manufacturer = " ".join(
                manufacturer_parts
            )

            # Remove OCR garbage
            manufacturer = re.sub(
                r"[^A-Za-z0-9.&,+()'\/\- ]",
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

            manufacturer_found = True

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

        batch_number = (
            batch_match
            .group(1)
            .strip()
        )

        details[
            "batch_number"
        ] = batch_number


    # ========================================================
    # MRP
    # ========================================================

    mrp_match = re.search(

        r"(?:"
        r"mrp"
        r"|m\.r\.p\.?"
        r")"
        r"\s*"
        r"(?:rs\.?|₹)?"
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
        r"[\s\/\-]"
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
            mfg_match
            .group(2)
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
        r"[\s\/\-]"
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
            expiry_match
            .group(2)
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

    # Step 2: Extract package fields
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