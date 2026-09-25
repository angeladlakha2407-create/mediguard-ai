from pathlib import Path
import streamlit as st
import pandas as pd
from PIL import Image

from backend import (
    search_medicine,
    check_interaction,
    check_barcode,
    verify_package,
    assess_authenticity,
    build_evidence_summary,
    generate_evidence_report,
)

from ocr import (
    extract_text,
    identify_medicine,
    extract_package_details,
)


# ============================================================
# LOAD MEDICINE DATA WITH ROBUST PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "medicines.csv"

if not DATA_PATH.exists():
    DATA_PATH = BASE_DIR / "medicines.csv"

medicines = pd.read_csv(DATA_PATH)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="MediGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# POLISHED UI CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background: #f5f7fb;
    color: #111827;
}

.block-container {
    padding-top: 0.8rem;
    padding-bottom: 4rem;
    max-width: 1450px;
}

header[data-testid="stHeader"] {
    background: transparent;
}


/* ============================================================
   SIDEBAR
   ============================================================ */

section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e5e7eb;
}

section[data-testid="stSidebar"] * {
    color: #1f2937;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #111827 !important;
}

section[data-testid="stSidebar"] .stRadio label {
    padding: 12px 14px;
    margin: 6px 0;
    border-radius: 12px;

    background: #f8fafc;
    border: 1px solid #e5e7eb;

    transition: all 0.2s ease;
    cursor: pointer;
}

section[data-testid="stSidebar"] .stRadio label:hover {
    background: #eef2ff;
    border-color: #c7d2fe;
    transform: translateX(2px);
}

section[data-testid="stSidebar"] .stRadio label p {
    font-weight: 600 !important;
    color: #374151 !important;
}

/* Selected navigation option */
section[data-testid="stSidebar"] .stRadio label:has(input:checked) {
    background: #eef2ff !important;
    border: 1px solid #6366f1 !important;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.10);
}

section[data-testid="stSidebar"] .stRadio label:has(input:checked) p {
    color: #4338ca !important;
    font-weight: 700 !important;
}

/* Keep sidebar title and headings dark */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #111827 !important;
}
}


/* ============================================================
   HERO
   ============================================================ */

.hero-box {
    background: linear-gradient(
        135deg,
        #111827 0%,
        #312e81 55%,
        #4338ca 100%
    ) !important;

    padding: 38px 42px;
    border-radius: 24px;
    color: white;
    margin-bottom: 28px;

    box-shadow:
        0 15px 35px rgba(49, 46, 129, 0.18);

    position: relative;
    overflow: hidden;
}

.hero-box::after {
    content: "";
    position: absolute;
    width: 220px;
    height: 220px;
    right: -70px;
    top: -90px;

    background: rgba(255,255,255,0.08);
    border-radius: 50%;
}

.hero-title {
    font-size: 42px;
    font-weight: 800;
    letter-spacing: -1px;
    margin-bottom: 8px;
    color: white !important;
}

.hero-tagline {
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 2px;
    color: #c7d2fe !important;
    margin-bottom: 12px;
}

.hero-text {
    color: #dbeafe !important;
    font-size: 16px;
    line-height: 1.6;
    max-width: 780px;
}

.hero-features {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 22px;
}

.hero-features span {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.16);
    color: #e0e7ff !important;
    padding: 7px 13px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
}

.hero-box,
.hero-box * {
    color: white !important;
}
/* ============================================================
   HERO TEXT VISIBILITY
   ============================================================ */

.hero-box {
    background: linear-gradient(
        135deg,
        #111827 0%,
        #312e81 55%,
        #4338ca 100%
    ) !important;

    padding: 38px 42px;
    border-radius: 24px;
    color: white !important;
    margin-bottom: 28px;

    box-shadow:
        0 15px 35px rgba(49, 46, 129, 0.18);

    position: relative;
    overflow: hidden;
}

.hero-title {
    font-size: 42px;
    font-weight: 800;
    letter-spacing: -1px;
    margin-bottom: 8px;
    color: white !important;
}

.hero-tagline {
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 2px;
    color: #c7d2fe !important;
    margin-bottom: 12px;
}

.hero-text {
    color: #dbeafe !important;
    font-size: 16px;
    line-height: 1.6;
    max-width: 780px;
}

.hero-features span {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.16);
    color: #e0e7ff !important;
    padding: 7px 13px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
}

.hero-box,
.hero-box * {
    color: white !important;
}


/* ============================================================
   HEADINGS
   ============================================================ */

.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4,
.stApp h5,
.stApp h6 {
    color: #111827 !important;
    font-weight: 750;
}

.stApp p,
.stApp label,
.stApp span {
    color: #374151;
}


/* ============================================================
   METRIC CARDS
   ============================================================ */

div[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e5e7eb;

    padding: 18px 20px;
    border-radius: 16px;

    box-shadow: 0 5px 16px rgba(15, 23, 42, 0.05);

    transition: all 0.2s ease;
}

div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 9px 22px rgba(15, 23, 42, 0.08);
}

div[data-testid="stMetricLabel"] {
    color: #64748b !important;
}

div[data-testid="stMetricValue"] {
    color: #111827 !important;
    font-weight: 800;
}


/* ============================================================
   FILE UPLOADER
   ============================================================ */

div[data-testid="stFileUploader"] {
    background: #ffffff !important;
    border: 2px dashed #cbd5e1 !important;
    border-radius: 18px !important;
    padding: 12px !important;
}

div[data-testid="stFileUploader"] section {
    background: #ffffff !important;
    border: none !important;
}

div[data-testid="stFileUploader"] section * {
    color: #374151 !important;
}

div[data-testid="stFileUploader"] button {
    background: #4f46e5 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 99px !important;
}

div[data-testid="stFileUploader"] button span {
    color: #ffffff !important;
}

div[data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"] {
    color: #111827 !important;
}

div[data-testid="stFileUploader"] svg {
    color: #4f46e5 !important;
    fill: #4f46e5 !important;
}


/* ============================================================
   INPUTS
   ============================================================ */

.stTextInput input,
.stNumberInput input,
textarea {
    color: #111827 !important;
    background: #ffffff !important;

    border: 1px solid #d1d5db !important;
    border-radius: 10px !important;
}

.stTextInput input:focus,
.stNumberInput input:focus,
textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.12) !important;
}


/* ============================================================
   BUTTONS
   ============================================================ */

.stButton button {
    background: #4f46e5 !important;
    color: white !important;

    border: none !important;
    border-radius: 11px !important;

    padding: 10px 20px !important;

    font-weight: 650 !important;

    transition: all 0.2s ease;
}

.stButton button:hover {
    background: #4338ca !important;
    transform: translateY(-1px);

    box-shadow:
        0 6px 15px rgba(79,70,229,0.25);
}

.stButton button:active {
    transform: translateY(0);
}


/* ============================================================
   TABS
   ============================================================ */

button[data-baseweb="tab"] {
    color: #64748b !important;
    font-weight: 600;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #4f46e5 !important;
}

div[data-baseweb="tab-highlight"] {
    background-color: #4f46e5 !important;
}


/* ============================================================
   ALERTS
   ============================================================ */

div[data-testid="stAlert"] {
    border-radius: 14px;
    border: 1px solid #e5e7eb;
}


/* ============================================================
   CONTAINERS
   ============================================================ */

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff;
    border-radius: 16px;
    border: 1px solid #e5e7eb;

    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);

    padding: 4px;
}


/* ============================================================
   IMAGES
   ============================================================ */

.stImage img {
    border-radius: 16px;
    border: 1px solid #e5e7eb;

    box-shadow:
        0 5px 18px rgba(15, 23, 42, 0.08);
}


/* ============================================================
   CAPTIONS
   ============================================================ */

.stApp [data-testid="stCaptionContainer"] {
    color: #64748b !important;
    font-size: 13px;
}


/* ============================================================
   DIVIDERS
   ============================================================ */

hr {
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 28px 0;
}


/* ============================================================
   VERIFICATION CARD
   ============================================================ */

.verification-card {
    background: #ffffff;
    border-radius: 20px;
    padding: 28px;
    margin: 18px 0 25px 0;
    text-align: center;
    border: 1px solid #e5e7eb;
    box-shadow: 0 8px 25px rgba(15, 23, 42, 0.06);
}

.verification-label {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.8px;
    color: #64748b !important;
    margin-bottom: 8px;
}

.verification-status {
    font-size: 27px;
    font-weight: 800;
    color: #111827 !important;
    margin-bottom: 10px;
}

.verification-description {
    max-width: 760px;
    margin: auto;
    font-size: 14px;
    line-height: 1.6;
    color: #64748b !important;
}

.verification-suspicious {
    border-top: 4px solid #dc2626;
}

.verification-safe {
    border-top: 4px solid #16a34a;
}

.verification-unknown {
    border-top: 4px solid #f59e0b;
}


/* ============================================================
   SCROLLBAR
   ============================================================ */

::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f5f9;
}

::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "scan_result" not in st.session_state:
    st.session_state.scan_result = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🛡️ MediGuard AI")
    st.caption("Medicine Safety Intelligence")

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "📷 Package Scanner",
            "🔎 Medicine Search",
            "⚕️ Interaction Checker",
        ],
    )

    st.divider()

    st.subheader("About")

    st.caption(
        "MediGuard AI analyzes visible medicine-package information "
        "and highlights verification signals."
    )

    st.info(
        "MediGuard does not guarantee that a medicine is genuine or counterfeit."
    )


# ============================================================
# HERO
# ============================================================

st.html(
    """
<div class="hero-box">
    <div class="hero-title">MediGuard AI</div>
    <div class="hero-tagline">VERIFY BEFORE YOU TRUST</div>
    <div class="hero-text">
        AI-powered medicine package verification and safety screening.
    </div>
    <div class="hero-features">
        <span>🔍 OCR Scanning</span>
        <span>🏷️ Batch Verification</span>
        <span>📊 Evidence-Based Analysis</span>
    </div>
</div>
"""
)


# ============================================================
# PACKAGE SCANNER
# ============================================================

if page == "📷 Package Scanner":

    st.header("📷 Package Scanner")

    st.caption(
        "Upload a clear image of a medicine package to extract and analyze visible information."
    )

    upload_col, checks_col = st.columns(
        [1.35, 1],
        gap="large",
    )

    # --------------------------------------------------------
    # UPLOAD
    # --------------------------------------------------------

    with upload_col:

        with st.container(border=True):

            st.header("📦 Scan Medicine Package")

            st.caption(
                "Upload a clear image of the medicine strip, box, or package "
                "to extract and verify available information."
            )

            uploaded_file = st.file_uploader(
                "Choose an image",
                type=[
                    "png",
                    "jpg",
                    "jpeg",
                    "webp",
                ],
                label_visibility="collapsed",
            )

    # --------------------------------------------------------
    # CHECKS
    # --------------------------------------------------------

    with checks_col:

        with st.container(border=True):

            st.subheader("🔍 What MediGuard checks")

            st.markdown(
                """
                - 🔍 Medicine name
                - 💊 Strength / formulation
                - 🏭 Manufacturer information
                - 📦 Batch & date fields
                - 💰 MRP
                - 🔐 Licence information
                - 🧬 Active ingredient
                - 🔳 Barcode evidence
                """
            )

    # ========================================================
    # IMAGE PROCESSING
    # ========================================================

    if uploaded_file:

        image = Image.open(uploaded_file)

        st.divider()

        st.header("🔬 Scan Analysis")

        preview_col, ocr_col = st.columns(
            [1, 1.35],
            gap="large",
        )

        # ----------------------------------------------------
        # PREVIEW
        # ----------------------------------------------------

        with preview_col:

            with st.container(border=True):

                st.subheader("📦 Package Preview")

                st.image(
                    image,
                    use_container_width=True,
                )

                st.caption(
                    f"Image size: {image.width} × {image.height}px"
                )

        # ----------------------------------------------------
        # OCR
        # ----------------------------------------------------

        with ocr_col:

            with st.container(border=True):

                st.subheader("🔍 OCR Analysis")

                with st.spinner(
                    "Reading package information..."
                ):

                    try:

                        raw_text = extract_text(
                            image
                        )

                        ocr_medicine = identify_medicine(
                            raw_text,
                            medicines,
                        )

                        package_details = extract_package_details(
                            raw_text
                        )

                        if not package_details.get(
                            "medicine"
                        ):

                            package_details["medicine"] = (
                                ocr_medicine
                            )

                    except Exception as e:

                        st.error(
                            f"OCR analysis failed: {e}"
                        )

                        st.stop()

                if raw_text and raw_text.strip():

                    st.text_area(
                        "Detected text",
                        raw_text,
                        height=190,
                        label_visibility="collapsed",
                    )

                else:

                    st.warning(
                        "No readable text was detected. "
                        "Try uploading a clearer image."
                    )

        # ====================================================
        # IDENTIFICATION
        # ====================================================

        st.divider()

        st.header("💊 Medicine Identification")

        medicine_name = (
            ocr_medicine
            or package_details.get("medicine")
            or "Not identified"
        )

        reference = None

        if medicine_name != "Not identified":

            try:

                reference = search_medicine(
                    medicine_name
                )

            except Exception:

                reference = None

        if reference is not None:

            category = reference.get(
                "category",
                "—",
            )

            active_ingredient = reference.get(
                "active ingredient",
                reference.get(
                    "active_ingredient",
                    "—",
                ),
            )

        else:

            category = "Reference not found"
            active_ingredient = "—"

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Medicine",
                str(medicine_name),
            )

        with c2:

            st.metric(
                "Category",
                str(category),
            )

        with c3:

            st.metric(
                "Active Ingredient",
                str(active_ingredient),
            )

        # ====================================================
        # PACKAGE INFORMATION
        # ====================================================

        st.divider()

        st.header("📦 Package Information")

        st.caption(
            "Information detected directly from the uploaded package."
        )

        fields = [
            (
                "Medicine",
                package_details.get("medicine"),
            ),
            (
                "Strength",
                package_details.get("strength"),
            ),
            (
                "Manufacturer",
                package_details.get("manufacturer"),
            ),
            (
                "Batch Number",
                package_details.get("batch_number"),
            ),
            (
                "Manufacturing Date",
                package_details.get(
                    "manufacturing_date"
                ),
            ),
            (
                "Expiry Date",
                package_details.get(
                    "expiry_date"
                ),
            ),
            (
                "MRP",
                package_details.get("mrp"),
            ),
            (
                "Licence Number",
                package_details.get(
                    "licence_number"
                ),
            ),
        ]

        for start in range(
            0,
            len(fields),
            4,
        ):

            cols = st.columns(4)

            for col, (label, value) in zip(
                cols,
                fields[start:start + 4],
            ):

                display = (
                    str(value)
                    if value not in [
                        None,
                        "",
                        "None",
                    ]
                    else "Not detected"
                )

                with col:

                    with st.container(border=True):

                        st.caption(label)

                        st.markdown(
                            f"**{display}**"
                        )

        # ====================================================
        # GENERATE REPORT
        # ====================================================

        try:

           report = generate_evidence_report(
         medicine_name=ocr_medicine if ocr_medicine else None,
         package_details=package_details,
         )

        except Exception as e:

            st.error(
                f"Verification analysis failed: {e}"
            )

            report = {}

        st.session_state.scan_result = {
            "report": report,
            "package_details": package_details,
            "medicine": medicine_name,
        }

        # ====================================================
        # VERIFICATION RESULT
        # ====================================================

        st.divider()

        st.header("🔐 Verification Result")

        authenticity = report.get(
            "authenticity",
            {},
        )

        if isinstance(authenticity, dict):

            status = (
                authenticity.get("status")
                or authenticity.get("label")
                or authenticity.get("result")
                or "INSUFFICIENT_EVIDENCE"
            )

        else:

            status = (
                authenticity
                or "INSUFFICIENT_EVIDENCE"
            )

        status = str(status).upper()

        if status == "SUSPICIOUS":

            status_title = "⚠️ SUSPICIOUS"

            status_description = (
                "One or more available package signals are inconsistent "
                "with the reference information. This is an indication "
                "for further verification, not proof of counterfeit status."
            )

            status_class = "verification-suspicious"

        elif status == "NO_MAJOR_INCONSISTENCY":

            status_title = "✓ NO MAJOR INCONSISTENCY"

            status_description = (
                "The available evidence did not reveal a major inconsistency. "
                "This does not independently prove authenticity."
            )

            status_class = "verification-safe"

        else:

            status_title = "ℹ️ INSUFFICIENT EVIDENCE"

            status_description = (
                "Not enough independently verifiable package information "
                "was detected to reach a stronger verification result."
            )

            status_class = "verification-unknown"

        # ====================================================
        # VERIFICATION CARD
        # ====================================================

        st.html(
            f"""
<div class="verification-card {status_class}">
    <div class="verification-label">VERIFICATION STATUS</div>
    <div class="verification-status">{status_title}</div>
    <div class="verification-description">
        {status_description}
    </div>
</div>
"""
        )

        # ====================================================
        # VERIFICATION DETAILS
        # ====================================================

        st.divider()

        st.header("📊 Evidence Breakdown")

        verification = report.get(
            "verification",
            {},
        )

        package_result = (
            verification.get(
                "package",
                {},
            )
            if isinstance(
                verification,
                dict,
            )
            else {}
        )

        ingredient_result = (
            verification.get(
                "active_ingredient",
                {},
            )
            if isinstance(
                verification,
                dict,
            )
            else {}
        )

        barcode_result = (
            verification.get(
                "barcode",
                {},
            )
            if isinstance(
                verification,
                dict,
            )
            else {}
        )

        batch_result = (
            verification.get(
                "batch",
                {},
            )
            if isinstance(
                verification,
                dict,
            )
            else {}
        )

        matches = (
            package_result.get(
                "matches",
                [],
            )
            if isinstance(
                package_result,
                dict,
            )
            else []
        )

        mismatches = (
            package_result.get(
                "mismatches",
                [],
            )
            if isinstance(
                package_result,
                dict,
            )
            else []
        )

        detected = (
            package_result.get(
                "detected",
                [],
            )
            if isinstance(
                package_result,
                dict,
            )
            else []
        )

        not_verified = (
            package_result.get(
                "not_verified",
                [],
            )
            if isinstance(
                package_result,
                dict,
            )
            else []
        )

        b1, b2, b3, b4 = st.columns(4)

        with b1:

            st.metric(
                "Matching Signals",
                len(matches),
            )

        with b2:

            st.metric(
                "Mismatches",
                len(mismatches),
            )

        with b3:

            st.metric(
                "Detected Fields",
                len(detected),
            )

        with b4:

            st.metric(
                "Unverified Fields",
                len(not_verified),
            )

        # ====================================================
        # EVIDENCE TABS
        # ====================================================

        evidence_tabs = st.tabs(
            [
                "✓ Matches",
                "⚠ Mismatches",
                "📌 Detected",
                "ℹ Not Verified",
            ]
        )

        with evidence_tabs[0]:

            if matches:

                for item in matches:

                    st.success(
                        str(item)
                    )

            else:

                st.info(
                    "No independently verified matching fields."
                )

        with evidence_tabs[1]:

            if mismatches:

                for item in mismatches:

                    st.error(
                        str(item)
                    )

            else:

                st.success(
                    "No mismatch detected."
                )

        with evidence_tabs[2]:

            if detected:

                for item in detected:

                    st.info(
                        str(item)
                    )

            else:

                st.info(
                    "No additional fields detected."
                )

        with evidence_tabs[3]:

            if not_verified:

                for item in not_verified:

                    st.warning(
                        str(item)
                    )

            else:

                st.success(
                    "No fields currently require verification."
                )

        # ====================================================
        # ACTIVE INGREDIENT
        # ====================================================

        st.divider()

        st.header("🧬 Active Ingredient")

        ingredient_col1, ingredient_col2 = st.columns(2)

        with ingredient_col1:

            with st.container(border=True):

                st.caption(
                    "Reference active ingredient"
                )

                st.subheader(
                    str(active_ingredient)
                )

        with ingredient_col2:

            with st.container(border=True):

                st.caption(
                    "Package ingredient verification"
                )

                if isinstance(
                    ingredient_result,
                    dict,
                ):

                    ingredient_status = str(
                        ingredient_result.get(
                            "status",
                            ingredient_result.get(
                                "result",
                                "Not independently verified",
                            ),
                        )
                    )

                    st.write(
                        ingredient_status
                    )

                else:

                    st.write(
                        "Not independently verified"
                    )

        # ====================================================
        # BARCODE
        # ====================================================

        st.divider()

        st.header("🔳 Barcode Verification")

        if isinstance(
            barcode_result,
            dict,
        ):

            barcode_status = barcode_result.get(
                "status",
                barcode_result.get(
                    "result",
                    "Not verified",
                ),
            )

            barcode_message = barcode_result.get(
                "message",
                "Barcode verification is not currently available.",
            )

        else:

            barcode_status = "Not verified"

            barcode_message = (
                "Barcode decoding is not currently implemented "
                "in the OCR pipeline."
            )

        st.info(
            f"**Status:** {barcode_status}\n\n"
            f"{barcode_message}"
        )

        st.caption(
            "A visible barcode alone is not treated as authenticity evidence "
            "without decoding and comparison against a trusted source."
        )

        # ====================================================
        # BATCH VERIFICATION
        # ====================================================

        st.divider()

        st.header("🏷️ Batch Verification")

        if isinstance(
            batch_result,
            dict,
        ):

            batch_status = str(
                batch_result.get(
                    "status",
                    "NOT_VERIFIED",
                )
            ).upper()

            if batch_status == "CONSISTENT":

                st.success(
                    "✓ BATCH INFORMATION CONSISTENT"
                )

                st.info(
                    "The detected batch information matches "
                    "the available local reference record."
                )

            elif batch_status == "MISMATCH":

                st.error(
                    "⚠️ BATCH INFORMATION MISMATCH"
                )

                st.warning(
                    "One or more detected batch fields do not match "
                    "the available local reference record. "
                    "This is a verification signal, not proof of counterfeit status."
                )

            else:

                st.warning(
                    "ℹ️ BATCH NOT VERIFIED"
                )

                st.info(
                    "The batch could not be independently verified "
                    "against the available local reference database."
                )

            batch_matches = batch_result.get(
                "matches",
                [],
            )

            batch_mismatches = batch_result.get(
                "mismatches",
                [],
            )

            batch_not_verified = batch_result.get(
                "not_verified",
                [],
            )

            bc1, bc2, bc3 = st.columns(3)

            with bc1:

                st.metric(
                    "Matching Fields",
                    len(batch_matches),
                )

            with bc2:

                st.metric(
                    "Mismatching Fields",
                    len(batch_mismatches),
                )

            with bc3:

                st.metric(
                    "Unverified Fields",
                    len(batch_not_verified),
                )

            if batch_matches:

                with st.container(border=True):

                    st.caption(
                        "Matching batch fields"
                    )

                    for item in batch_matches:

                        st.write(
                            f"✓ {item}"
                        )

            if batch_mismatches:

                with st.container(border=True):

                    st.caption(
                        "Mismatching batch fields"
                    )

                    for item in batch_mismatches:

                        st.write(
                            f"⚠ {item}"
                        )

            if batch_not_verified:

                with st.container(border=True):

                    st.caption(
                        "Unverified batch fields"
                    )

                    for item in batch_not_verified:

                        st.write(
                            f"ℹ {item}"
                        )

        else:

            st.info(
                "Batch verification information is not available."
            )

        st.caption(
            "Batch verification is based only on the local reference dataset. "
            "A local match does not independently prove medicine authenticity."
        )

        # ====================================================
        # EVIDENCE REPORT
        # ====================================================

        st.divider()

        st.header("🧾 Evidence Report")

        evidence = report.get(
            "evidence",
            [],
        )

        if evidence:

            for item in evidence:

                st.markdown(
                    f"- {item}"
                )

        else:

            st.info(
                "No additional evidence summary available."
            )

        # ====================================================
        # REFERENCE INFORMATION
        # ====================================================

        if reference is not None:

            st.divider()

            st.header("📚 Reference Information")

            ref1, ref2 = st.columns(2)

            with ref1:

                with st.container(border=True):

                    st.subheader(
                        "Medicine Profile"
                    )

                    st.write(
                        "**Category:**",
                        reference.get(
                            "category",
                            "—",
                        ),
                    )

                    st.write(
                        "**Uses:**",
                        reference.get(
                            "uses",
                            "—",
                        ),
                    )

            with ref2:

                with st.container(border=True):

                    st.subheader(
                        "Reference Notes"
                    )

                    st.write(
                        "**Warnings:**",
                        reference.get(
                            "warnings",
                            "—",
                        ),
                    )

                    st.write(
                        "**Side Effects:**",
                        reference.get(
                            "side effects",
                            reference.get(
                                "side_effects",
                                "—",
                            ),
                        ),
                    )


# ============================================================
# MEDICINE SEARCH
# ============================================================

elif page == "🔎 Medicine Search":

    st.header("🔎 Medicine Search")

    st.caption(
        "Search the local medicine reference database."
    )

    search_query = st.text_input(
        "Medicine name",
        placeholder="Try Paracetamol, Aspirin, Metformin...",
    )

    if search_query.strip():

        result = search_medicine(
            search_query.strip()
        )

        if result is None:

            st.warning(
                "No matching medicine found."
            )

        else:

            medicine_name = result.get(
                "medicine",
                search_query,
            )

            st.subheader(
                f"💊 {medicine_name}"
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                st.metric(
                    "Category",
                    result.get(
                        "category",
                        "—",
                    ),
                )

            with c2:

                st.metric(
                    "Active Ingredient",
                    result.get(
                        "active ingredient",
                        result.get(
                            "active_ingredient",
                            "—",
                        ),
                    ),
                )

            with c3:

                st.metric(
                    "Reference",
                    "Available",
                )

            st.divider()

            left, right = st.columns(2)

            with left:

                with st.container(border=True):

                    st.subheader("Uses")

                    st.write(
                        result.get(
                            "uses",
                            "—",
                        )
                    )

            with right:

                with st.container(border=True):

                    st.subheader("Warnings")

                    st.write(
                        result.get(
                            "warnings",
                            "—",
                        )
                    )

            with st.container(border=True):

                st.subheader(
                    "Side Effects"
                )

                st.write(
                    result.get(
                        "side effects",
                        result.get(
                            "side_effects",
                            "—",
                        ),
                    )
                )


# ============================================================
# INTERACTION CHECKER
# ============================================================

elif page == "⚕️ Interaction Checker":

    st.header("⚕️ Interaction Checker")

    st.caption(
        "Check the interaction dataset for a pair of medicines."
    )

    medicine_list = (
        medicines["medicine"]
        .dropna()
        .astype(str)
        .tolist()
        if not medicines.empty and "medicine" in medicines.columns
        else []
    )

    c1, c2 = st.columns(2)

    with c1:

        medicine_1 = st.selectbox(
            "Medicine 1",
            ["Select medicine"] + medicine_list,
        )

    with c2:

        medicine_2 = st.selectbox(
            "Medicine 2",
            ["Select medicine"] + medicine_list,
        )

    if st.button(
        "🔍 Check Interaction",
        type="primary",
        use_container_width=True,
    ):

        if (
            medicine_1 == "Select medicine"
            or medicine_2 == "Select medicine"
        ):

            st.warning(
                "Please select both medicines."
            )

        elif medicine_1 == medicine_2:

            st.info(
                "Please select two different medicines."
            )

        else:

            try:

                result = check_interaction(
                    medicine_1,
                    medicine_2,
                )

                if result:

                    if isinstance(
                        result,
                        dict,
                    ):

                        interaction_text = result.get(
                            "interaction",
                            "Interaction found.",
                        )

                        severity = result.get(
                            "severity",
                            "Not specified",
                        )

                    else:

                        interaction_text = str(
                            result
                        )

                        severity = (
                            "Not specified"
                        )

                    st.warning(
                        "⚠️ Interaction entry found"
                    )

                    st.write(
                        f"**{medicine_1} + {medicine_2}**"
                    )

                    st.info(
                        interaction_text
                    )

                    st.metric(
                        "Severity",
                        severity,
                    )

                else:

                    st.success(
                        "✓ No interaction entry found in the local dataset."
                    )

                    st.caption(
                        "This only means no entry was found in the current "
                        "reference dataset."
                    )

            except Exception as e:

                st.error(
                    f"Interaction check failed: {e}"
                )


# ============================================================
# DISCLAIMER
# ============================================================

st.divider()

st.caption(
    "⚠️ MediGuard AI is a student prototype for package-information "
    "analysis and evidence-based screening. It does not guarantee "
    "medicine authenticity, safety, or suitability. Authenticity "
    "verification requires trusted manufacturer, regulatory, pharmacy, "
    "or other authoritative sources."
)