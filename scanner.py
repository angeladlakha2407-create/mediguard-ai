from pathlib import Path
import streamlit as st
import pandas as pd
from PIL import Image

# Import directly from root files
from ocr import (
    extract_text,
    extract_package_details,
    identify_medicine
)

from backend import (
    generate_evidence_report
)


# =========================================================
# LOAD MEDICINE DATABASE WITH ROBUST PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "medicines.csv"

if not DATA_PATH.exists():
    DATA_PATH = BASE_DIR / "medicines.csv"

medicines = pd.read_csv(DATA_PATH)
medicines.columns = medicines.columns.str.strip()


# =========================================================
# MEDIGUARD AI
# Scan Medicine / Package Upload Page
# =========================================================

st.set_page_config(
    page_title="MedGuard AI | Scan Medicine",
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

/* =========================================================
   GLOBAL
========================================================= */

.stApp {
    background: #F5F9FB;
}

.block-container {
    max-width: 1250px;
    padding: 35px 42px 55px 42px;
}

header[data-testid="stHeader"] {
    background: transparent !important;
}

/* Hide automatic multipage navigation */
div[data-testid="stSidebarNav"] {
    display: none !important;
}


/* =========================================================
   SIDEBAR
========================================================= */

section[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E2EBEF;
}

section[data-testid="stSidebar"] > div {
    padding: 0 16px 20px 16px;
}


/* Brand */

.sidebar-brand {
    padding: 22px 10px 20px 10px;
    border-bottom: 1px solid #EDF2F4;
    margin-bottom: 13px;
}

.brand-top {
    display: flex;
    align-items: center;
    gap: 11px;
}

.brand-logo {
    width: 43px;
    height: 43px;
    border-radius: 13px;
    background: linear-gradient(135deg, #083B56, #0A858A);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 20px;
    box-shadow: 0 7px 17px rgba(8, 59, 86, 0.18);
}

.brand-name {
    color: #083B56;
    font-size: 16px;
    font-weight: 850;
    letter-spacing: -0.3px;
}

.brand-tagline {
    color: #8A9BA7;
    font-size: 8px;
    margin-top: 3px;
    letter-spacing: 0.7px;
}


/* Sidebar labels */

.side-label {
    color: #91A0AA;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 1.4px;
    margin: 20px 8px 8px 8px;
}


/* Sidebar buttons */

section[data-testid="stSidebar"] .stButton {
    margin-bottom: 4px;
}

section[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    min-height: 40px;
    border: 1px solid transparent;
    background: transparent;
    color: #526879;
    border-radius: 10px;
    text-align: left;
    font-size: 11px;
    font-weight: 650;
    padding: 8px 11px;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: #EDF8F8;
    border-color: #D7EEEE;
    color: #087579;
}


/* Active scanner button */

section[data-testid="stSidebar"] a[aria-current="page"] {
    background: #EDF8F8 !important;
    border-radius: 10px !important;
    color: #087579 !important;
}


/* System status */

.sidebar-status {
    margin: 24px 4px 0 4px;
    padding: 14px;
    border-radius: 14px;
    background: linear-gradient(
        145deg,
        #F2F8FA,
        #EDF8F7
    );
    border: 1px solid #DCECEE;
}

.status-heading {
    color: #7B8E9A;
    font-size: 8px;
    font-weight: 800;
    letter-spacing: 1px;
}

.status-online {
    color: #168A67;
    font-size: 10px;
    font-weight: 750;
    margin-top: 7px;
}


/* Trust box */

.trust-box {
    margin: 11px 4px 0 4px;
    padding: 13px;
    border-radius: 13px;
    background: #FFFFFF;
    border: 1px solid #E6EDF1;
}

.trust-title {
    color: #526879;
    font-size: 9px;
    font-weight: 750;
}

.trust-text {
    color: #91A0AC;
    font-size: 8px;
    line-height: 1.55;
    margin-top: 4px;
}


/* =========================================================
   PAGE HEADER
========================================================= */

.page-eyebrow {
    color: #0C8790;
    font-size: 9px;
    font-weight: 850;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.page-title {
    color: #083B56;
    font-size: 35px;
    line-height: 1.1;
    font-weight: 850;
    letter-spacing: -1.2px;
    margin: 0;
}

.page-subtitle {
    color: #718697;
    font-size: 12px;
    line-height: 1.65;
    margin-top: 8px;
    max-width: 720px;
}


/* =========================================================
   UPLOAD CARD
========================================================= */

.upload-card {
    background: #FFFFFF;
    border: 1px solid #E0EAEF;
    border-radius: 21px;
    padding: 25px 27px 18px 27px;
    margin-top: 28px;
    box-shadow: 0 8px 28px rgba(8,59,86,0.045);
}

.upload-heading {
    color: #083B56;
    font-size: 17px;
    font-weight: 820;
}

.upload-text {
    color: #8496A3;
    font-size: 10px;
    line-height: 1.6;
    margin-top: 5px;
}


/* =========================================================
   FILE UPLOADER
========================================================= */

div[data-testid="stFileUploader"] {
    margin-top: 8px;
    background: #F7FBFC;
    border: 2px dashed #B8DADC;
    border-radius: 17px;
    padding: 11px;
}

div[data-testid="stFileUploader"]:hover {
    border-color: #0A858A;
    background: #F1FAFA;
}


/* =========================================================
   PREVIEW
========================================================= */

.preview-heading {
    color: #083B56;
    font-size: 16px;
    font-weight: 820;
    margin-top: 28px;
    margin-bottom: 11px;
}

.preview-card {
    background: #FFFFFF;
    border: 1px solid #E0EAEF;
    border-radius: 19px;
    padding: 16px;
    box-shadow: 0 7px 24px rgba(8,59,86,0.035);
}


/* =========================================================
   BUTTONS
========================================================= */

.stButton > button {
    min-height: 43px;
    border-radius: 11px;
    border: 1px solid #0A7D82;
    background: linear-gradient(
        135deg,
        #083B56,
        #087F82
    );
    color: #FFFFFF;
    font-size: 11px;
    font-weight: 800;
    transition: all 0.18s ease;
}

.stButton > button:hover {
    border-color: #0A858A;
    background: linear-gradient(
        135deg,
        #0A4563,
        #0A9290
    );
    color: #FFFFFF;
}


/* =========================================================
   INFORMATION CARDS
========================================================= */

.info-card {
    background: #FFFFFF;
    border: 1px solid #E0EAEF;
    border-radius: 18px;
    padding: 20px;
    min-height: 145px;
    box-shadow: 0 7px 22px rgba(8,59,86,0.035);
}

.info-icon {
    width: 38px;
    height: 38px;
    border-radius: 11px;
    background: #EAF7F7;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    margin-bottom: 11px;
}

.info-title {
    color: #083B56;
    font-size: 12px;
    font-weight: 780;
}

.info-text {
    color: #7D909D;
    font-size: 9px;
    line-height: 1.65;
    margin-top: 5px;
}


/* =========================================================
   SAFETY NOTE
========================================================= */

.safety-note {
    margin-top: 28px;
    background: linear-gradient(
        135deg,
        #EEF8F9,
        #EAF7F7
    );
    border: 1px solid #D3ECEC;
    border-radius: 17px;
    padding: 17px 20px;
}

.safety-title {
    color: #18586A;
    font-size: 11px;
    font-weight: 820;
}

.safety-text {
    color: #69838D;
    font-size: 9px;
    line-height: 1.6;
    margin-top: 5px;
}


/* =========================================================
   FOOTER
========================================================= */

.footer {
    text-align: center;
    color: #9AA8B3;
    font-size: 8px;
    line-height: 1.7;
    margin-top: 38px;
}


/* =========================================================
   MOBILE
========================================================= */

@media (max-width: 800px) {

    .block-container {
        padding: 25px 20px 40px 20px;
    }

    .page-title {
        font-size: 28px;
    }

}

</style>
""", unsafe_allow_html=True)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.html("""
    <div class="sidebar-brand">

        <div class="brand-top">

            <div class="brand-logo">
                🛡️
            </div>

            <div>
                <div class="brand-name">
                    MEDIGUARD AI
                </div>

                <div class="brand-tagline">
                    MEDICINE SAFETY INTELLIGENCE
                </div>
            </div>

        </div>

    </div>
    """)

    st.html("""
    <div class="side-label">
        OVERVIEW
    </div>
    """)

    st.page_link(
        "app.py",
        label="⌂   Home",
        use_container_width=True
    )

    st.page_link(
        "pages/dashboard.py",
        label="▣   Dashboard",
        use_container_width=True
    )

    st.html("""
    <div class="side-label">
        SAFETY TOOLS
    </div>
    """)

    st.page_link(
        "pages/medicine_analyzer.py",
        label="💊   Medicine Analyzer",
        use_container_width=True
    )

    st.page_link(
        "pages/scanner.py",
        label="📷   Scan Medicine",
        use_container_width=True
    )

    st.page_link(
        "pages/interaction_checker.py",
        label="↔   Interaction Checker",
        use_container_width=True
    )

    st.html("""
    <div class="sidebar-status">

        <div class="status-heading">
            SYSTEM STATUS
        </div>

        <div class="status-online">
            ● Prototype Online
        </div>

    </div>

    <div class="trust-box">

        <div class="trust-title">
            🛡️ Safety-first design
        </div>

        <div class="trust-text">
            Built to organize medicine information
            and highlight potential safety concerns.
        </div>

    </div>
    """)


# =========================================================
# PAGE HEADER
# =========================================================

st.html("""
<div class="page-eyebrow">
    MEDIGUARD AI / SAFETY TOOLS
</div>

<div class="page-title">
    Scan Medicine
</div>

<div class="page-subtitle">
    Upload an image of a medicine package to begin
    the package verification process.
</div>
""")


# =========================================================
# UPLOAD CARD
# =========================================================

st.html("""
<div class="upload-card">

    <div class="upload-heading">
        📷 Upload medicine package
    </div>

    <div class="upload-text">
        Upload a clear image of the medicine packaging.
        Make sure the medicine name and important package
        details are visible.
    </div>

</div>
""")


# =========================================================
# FILE UPLOAD
# =========================================================

uploaded_file = st.file_uploader(
    "Browse Files",
    type=["png", "jpg", "jpeg"],
    help="Supported formats: PNG, JPG and JPEG"
)


# =========================================================
# IMAGE PREVIEW + ANALYZE
# =========================================================

if uploaded_file is not None:

    st.html("""
    <div class="preview-heading">
        Image Preview
    </div>
    """)

    st.html("""
    <div class="preview-card">
    """)

    st.image(
        uploaded_file,
        caption="Uploaded medicine package",
        use_container_width=True
    )

    st.html("""
    </div>
    """)

    st.write("")

    analyze_clicked = st.button(
        "🔍  Analyze Medicine Package",
        use_container_width=True
    )

    if analyze_clicked:

        try:

            # =================================================
            # OPEN IMAGE
            # =================================================

            image = Image.open(uploaded_file)

            # =================================================
            # STEP 1 — OCR
            # =================================================

            with st.spinner(
                "Reading medicine package..."
            ):

                ocr_text = extract_text(image)

            if not ocr_text:

                st.warning(
                    "No readable text was detected. "
                    "Please upload a clearer package image."
                )

            else:

                # =================================================
                # STEP 2 — EXTRACT PACKAGE DETAILS
                # =================================================

                with st.spinner(
                    "Extracting package information..."
                ):

                    package_details = extract_package_details(
                        ocr_text
                    )

                # =================================================
                # STEP 3 — IDENTIFY MEDICINE
                # =================================================

                package_details["medicine"] = identify_medicine(
                    ocr_text,
                    medicines
                )

                medicine_name = package_details.get(
                    "medicine"
                )

                # =================================================
                # RAW OCR
                # =================================================

                st.success(
                    "Package text extracted successfully."
                )

                st.subheader(
                    "📄 Extracted Package Text"
                )

                with st.expander(
                    "View OCR text"
                ):

                    st.text_area(
                        "OCR Output",
                        ocr_text,
                        height=180,
                        label_visibility="collapsed"
                    )

                # =================================================
                # STEP 4 — PACKAGE INFORMATION
                # =================================================

                st.subheader(
                    "📦 Detected Package Information"
                )

                info_col1, info_col2, info_col3 = st.columns(
                    3
                )

                with info_col1:

                    st.metric(
                        "Medicine",
                        package_details.get(
                            "medicine"
                        ) or "Not detected"
                    )

                    st.metric(
                        "Strength",
                        package_details.get(
                            "strength"
                        ) or "Not detected"
                    )

                    st.metric(
                        "Manufacturer",
                        package_details.get(
                            "manufacturer"
                        ) or "Not detected"
                    )

                with info_col2:

                    st.metric(
                        "Batch",
                        package_details.get(
                            "batch_number"
                        ) or "Not detected"
                    )

                    st.metric(
                        "MFG",
                        package_details.get(
                            "manufacturing_date"
                        ) or "Not detected"
                    )

                    st.metric(
                        "EXP",
                        package_details.get(
                            "expiry_date"
                        ) or "Not detected"
                    )

                with info_col3:

                    mrp = package_details.get("mrp")

                    st.metric(
                        "MRP",
                        f"₹{mrp}" if mrp else "Not detected"
                    )

                    st.metric(
                        "Licence",
                        package_details.get(
                            "licence_number"
                        ) or "Not detected"
                    )

                # =================================================
                # MEDICINE NOT FOUND
                # =================================================

                if not medicine_name:

                    st.warning(
                        "The package was scanned, but a medicine "
                        "from the available reference database "
                        "could not be identified."
                    )

                    st.info(
                        "Try uploading a clearer image where "
                        "the medicine name is clearly visible."
                    )

                else:

                    # =================================================
                    # STEP 5 — BACKEND VERIFICATION
                    # =================================================

                    with st.spinner(
                        "Verifying package information..."
                    ):

                        report = generate_evidence_report(
                            medicine_name=medicine_name,
                            package_details=package_details
                        )

                    if not report.get("success"):

                        st.error(
                            report.get(
                                "message",
                                "Verification could not be completed."
                            )
                        )

                    else:

                        # =================================================
                        # VERIFICATION EVIDENCE
                        # =================================================

                        st.subheader(
                            "🔎 Verification Evidence"
                        )

                        verification = report.get(
                            "verification",
                            {}
                        )

                        package_result = verification.get(
                            "package",
                            {}
                        )

                        ingredient_result = verification.get(
                            "active_ingredient",
                            {}
                        )

                        # -------------------------------------------------
                        # MATCHES
                        # -------------------------------------------------

                        matches = package_result.get(
                            "matches",
                            []
                        )

                        if matches:

                            st.markdown(
                                "### ✅ Matching Information"
                            )

                            for match in matches:

                                st.success(
                                    match
                                )

                        # -------------------------------------------------
                        # MISMATCHES
                        # -------------------------------------------------

                        mismatches = package_result.get(
                            "mismatches",
                            []
                        )

                        if mismatches:

                            st.markdown(
                                "### ⚠️ Mismatched Information"
                            )

                            for mismatch in mismatches:

                                st.error(
                                    mismatch
                                )

                        # -------------------------------------------------
                        # ACTIVE INGREDIENT
                        # -------------------------------------------------

                        st.markdown(
                            "### 🧪 Active Ingredient"
                        )

                        ingredient_status = ingredient_result.get(
                            "status",
                            "NOT_VERIFIED"
                        )

                        ingredient_message = ingredient_result.get(
                            "message",
                            "Active ingredient could not be verified."
                        )

                        if ingredient_status == "MATCH":

                            st.success(
                                "MATCH — "
                                + ingredient_message
                            )

                        elif ingredient_status == "MISMATCH":

                            st.error(
                                "MISMATCH — "
                                + ingredient_message
                            )

                        else:

                            st.info(
                                "NOT VERIFIED — "
                                + ingredient_message
                            )

                        # =================================================
                        # AUTHENTICITY ASSESSMENT
                        # =================================================

                        st.subheader(
                            "🛡️ Authenticity Assessment"
                        )

                        authenticity = report.get(
                            "authenticity",
                            {}
                        )

                        assessment = authenticity.get(
                            "assessment",
                            "INSUFFICIENT_EVIDENCE"
                        )

                        summary = authenticity.get(
                            "summary",
                            ""
                        )

                        if assessment == "SUSPICIOUS":

                            st.error(
                                "⚠️ SUSPICIOUS"
                            )

                        elif assessment == "NO_MAJOR_INCONSISTENCY":

                            st.success(
                                "✅ NO MAJOR INCONSISTENCY DETECTED"
                            )

                        else:

                            st.warning(
                                "ℹ️ INSUFFICIENT EVIDENCE"
                            )

                        st.info(summary)

                        # =================================================
                        # EVIDENCE SUMMARY
                        # =================================================

                        st.subheader(
                            "📋 Evidence Summary"
                        )

                        evidence = report.get(
                            "evidence",
                            {}
                        )

                        evidence_matches = (
                            evidence.get("matches", [])
                            if isinstance(evidence, dict)
                            else []
                        )

                        evidence_mismatches = (
                            evidence.get("mismatches", [])
                            if isinstance(evidence, dict)
                            else []
                        )

                        if evidence_matches:

                            st.markdown(
                                "**Verified / matching:**"
                            )

                            for item in evidence_matches:

                                st.markdown(
                                    f"✓ {item}"
                                )

                        if evidence_mismatches:

                            st.markdown(
                                "**Flagged:**"
                            )

                            for item in evidence_mismatches:

                                st.markdown(
                                    f"⚠️ {item}"
                                )

                        if (
                            not evidence_matches
                            and not evidence_mismatches
                        ):

                            st.info(
                                "No comparison evidence was "
                                "available from the current data."
                            )

                        # =================================================
                        # SAFETY DISCLAIMER
                        # =================================================

                        st.caption(
                            "This is a screening prototype based on "
                            "the uploaded image and available reference "
                            "data. A 'No Major Inconsistency' result "
                            "does not prove that a medicine is genuine, "
                            "and a 'Suspicious' result does not by itself "
                            "prove that it is counterfeit."
                        )

        except Exception as e:

            st.error(
                f"Scanner Error: {e}"
            )


# =========================================================
# INFORMATION CARDS
# =========================================================

st.write("")
st.write("")

col1, col2, col3 = st.columns(
    3,
    gap="medium"
)


with col1:

    st.html("""
    <div class="info-card">

        <div class="info-icon">
            📸
        </div>

        <div class="info-title">
            Clear Image
        </div>

        <div class="info-text">
            Upload a well-lit image where the medicine
            name and package information are clearly readable.
        </div>

    </div>
    """)


with col2:

    st.html("""
    <div class="info-card">

        <div class="info-icon">
            🔎
        </div>

        <div class="info-title">
            Information Extraction
        </div>

        <div class="info-text">
            OCR extracts medicine and package information
            from the uploaded image for verification.
        </div>

    </div>
    """)


with col3:

    st.html("""
    <div class="info-card">

        <div class="info-icon">
            🛡️
        </div>

        <div class="info-title">
            Evidence-Based Verification
        </div>

        <div class="info-text">
            Detected package information is compared with
            available reference data to highlight inconsistencies.
        </div>

    </div>
    """)


# =========================================================
# SAFETY NOTE
# =========================================================

st.html("""
<div class="safety-note">

    <div class="safety-title">
        🛡️ Safety-first screening
    </div>

    <div class="safety-text">
        MEDIGUARD AI is a student prototype designed to
        organize medicine information and highlight potential
        package inconsistencies. It is not a replacement for
        professional medical advice or official medicine
        authentication services.
    </div>

</div>
""")


# =========================================================
# FOOTER
# =========================================================

st.html("""
<div class="footer">

    <b>MEDIGUARD AI</b>
    &nbsp;•&nbsp;
    Medicine Safety Intelligence

    <br>

    Engineering Day 2026 • Working Prototype

</div>
""")