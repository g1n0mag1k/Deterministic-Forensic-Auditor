from __future__ import annotations

import io
import json
import re
import tempfile
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from engine import OSHAViolationEngine
from intake import generate_chain_of_custody

try:
    import fitz  # type: ignore
except ImportError:  # pragma: no cover - runtime dependency for PDF parsing
    fitz = None


BATES_REGEX = re.compile(r"[A-Z]{2,5}-\d{4,}")


def _extract_text_from_upload(uploaded_file) -> str:
    if uploaded_file is None:
        return ""

    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".pdf":
        if fitz is None:
            raise ImportError("PyMuPDF (fitz) is required for PDF extraction")
        data = uploaded_file.getvalue()
        with fitz.open(stream=data, filetype="pdf") as pdf_doc:
            return "\n".join(page.get_text("text") for page in pdf_doc)

    return uploaded_file.getvalue().decode("utf-8", errors="ignore")


def _truth_map_html(findings_df: pd.DataFrame) -> str:
    rows = []
    for row in findings_df.to_dict(orient="records"):
        page_number = int(row["page_number"])
        safe_filename = escape(str(row["pdf_filename"]))
        link = f"{safe_filename}#page={page_number}"
        rows.append(
            "<tr>"
            f"<td>{escape(str(row['matched_phrase']))}</td>"
            f"<td><a href=\"{link}\">Page {page_number}</a></td>"
            f"<td>{escape(str(row['rule_text']))}</td>"
            "</tr>"
        )
    return (
        "<html><body><table border='1'>"
        "<thead><tr><th>Matched Phrase</th><th>Source</th><th>Rule Text</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></body></html>"
    )


def main() -> None:
    st.set_page_config(page_title="Deterministic Forensic Auditor", layout="wide")
    st.title("Deterministic Forensic Auditor")

    st.sidebar.header("Discovery Intake")
    discovery_files = st.sidebar.file_uploader(
        "Upload discovery documents",
        accept_multiple_files=True,
    )

    if discovery_files:
        with st.spinner("Generating SHA-256 chain of custody manifest..."):
            temp_paths = []
            with tempfile.TemporaryDirectory() as tmp_dir:
                for uploaded in discovery_files:
                    temp_path = Path(tmp_dir) / uploaded.name
                    temp_path.write_bytes(uploaded.getvalue())
                    temp_paths.append(str(temp_path))

                # FRE 702 + TRE 901(b)(9): cryptographic manifests support method reliability and process authentication.
                manifest = generate_chain_of_custody(temp_paths)

        st.sidebar.json(manifest)
        st.sidebar.download_button(
            "Download custody manifest",
            data=io.StringIO(json.dumps(manifest, indent=2)).getvalue(),
            file_name="custody_manifest.json",
            mime="application/json",
        )

    st.header("OSHA Audit")
    osha_pdf = st.file_uploader("Upload OSHA source PDF", type=["pdf"])
    audit_document = st.file_uploader("Upload document to audit", type=["pdf", "txt", "md"], key="audit")

    if osha_pdf and audit_document:
        with tempfile.TemporaryDirectory() as tmp_dir:
            osha_path = Path(tmp_dir) / osha_pdf.name
            osha_path.write_bytes(osha_pdf.getvalue())

            audit_text = _extract_text_from_upload(audit_document)
            bates_numbers = sorted(set(BATES_REGEX.findall(audit_text)))

            engine = OSHAViolationEngine(str(osha_path))
            findings = engine.search_violations(audit_text)
            findings_df = pd.DataFrame(findings)

        if bates_numbers:
            st.caption(f"Detected Bates numbers: {', '.join(bates_numbers)}")

        st.subheader("Findings")
        default_findings_df = pd.DataFrame(
            columns=["rule_text", "pdf_filename", "page_number", "matched_phrase"]
        )
        st.dataframe(findings_df if not findings_df.empty else default_findings_df)

        st.markdown("### Human-in-the-Loop Verification (ABA Opinion 512)")
        verified = st.checkbox("I have manually verified these findings before legal use.")

        if verified and not findings_df.empty:
            csv_data = findings_df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                data=csv_data,
                file_name="osha_findings.csv",
                mime="text/csv",
            )

            html_map = _truth_map_html(findings_df)
            st.download_button(
                "Download HTML Truth Map",
                data=html_map,
                file_name="truth_map.html",
                mime="text/html",
            )


if __name__ == "__main__":
    main()
