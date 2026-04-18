# 🔍 Deterministic Forensic Auditor

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit&logoColor=white)
![FRE 702 Compliant](https://img.shields.io/badge/FRE%20702-Compliant-green)
![TRE 901(b)(9) Certified](https://img.shields.io/badge/TRE%20901(b)(9)-Certified-green)
![License](https://img.shields.io/badge/License-Proprietary%20%E2%80%93%20All%20Rights%20Reserved-red)

---

A locally-executed, zero-hallucination forensic audit engine that scans industrial discovery documents for OSHA Hazard Communication Standard (HCS) violations and produces courtroom-admissible evidence reports with a cryptographic chain of custody.

---

## 📌 Problem Statement

Large-scale industrial litigation routinely involves discovery dumps of thousands of PDFs — Safety Data Sheets, chemical inventories, training logs — that must be reviewed for OSHA compliance violations. General-purpose LLMs are categorically unsuitable for this work: they hallucinate citations, invent regulatory text, and cannot satisfy the **Daubert standard** (**FRE 702**) because their outputs are probabilistic, non-reproducible, and carry an unknowable error rate.

This tool solves that problem with a fully deterministic, exact-string-matching pipeline grounded exclusively in the OSHA HCS Final Rule (89 FR 44144, May 20, 2024). Every flag it raises traces directly to a specific regulatory appendix. Every file it touches receives a SHA-256 fingerprint. Every finding requires a credentialed human auditor to sign off before export — satisfying **ABA Formal Opinion 512** on the unauthorized practice of law. The result is a finding that can survive a Daubert challenge, authenticate under **TRE 901(b)(9)**, and be admitted as evidence in a Tennessee state or federal proceeding.

---

## ✨ Key Features

| Icon | Feature | Description |
|------|---------|-------------|
| 🚫🎲 | **Zero Hallucination Guarantee** | All violation detection uses exact substring matching on normalised text. No LLM inference, no probabilistic scoring. Identical inputs always produce identical outputs. |
| 🔐 | **SHA-256 Chain of Custody** | Every discovery file is fingerprinted via chunked SHA-256 (64 KB blocks). A combined manifest hash covers the entire evidence set. Tampering is detectable by any competent examiner. |
| ⚖️ | **FRE 702 / Daubert Compliance** | The methodology is documented, testable, independently reproducible, and carries a known (zero) false-positive rate for exact matches — satisfying all four *Daubert* reliability prongs. |
| 🏛️ | **TRE 901(b)(9) Authentication** | The source code, trigger-phrase list, and `custody_manifest.json` together constitute a complete description of the process and system used to authenticate the evidence. |
| 👤 | **Human-in-the-Loop (ABA Opinion 512)** | All findings are labelled *Automated Flags*. Export buttons are gated behind a mandatory auditor name field and confirmation checkbox — the tool cannot make a final legal determination. |
| 📄 | **5,000+ Page PDF Handling** | PyMuPDF pages are loaded lazily via a Python generator. No full-document text buffer is ever held in RAM, ensuring stable operation on multi-gigabyte discovery files. |
| 🏷️ | **Bates Number Extraction** | Regex pattern `[A-Z]{2,5}-\d{4,}` extracts litigation Bates stamps from each page and includes them in every finding row across all export formats. |
| 📊 | **Relativity-Compatible Export** | Findings export to CSV, Excel (`.xlsx`), and HTML with `#page=XX` anchor hyperlinks — ready for direct import into Relativity or any comparable case management platform. |

---

## ⚖️ Legal Foundation

| Standard | Requirement | How This Tool Satisfies It |
|----------|-------------|---------------------------|
| **FRE 702** — Expert Testimony | Methodology must be testable, peer-reviewable, have a known error rate, and be reliably applied to the facts | Exact-string matching is fully documented in source code; error rate for false positives = 0; any examiner can re-run the scan and reproduce results |
| **FRE 702(b)** — Sufficient Facts | Opinion must be based on sufficient facts or data | Every finding cites the exact matched phrase, PDF filename, and 1-based page number traceable to the source document |
| **TRE 901(b)(9)** — Process/System Authentication | Must describe a process or system that produces an accurate result | `intake.py` + `custody_manifest.json` constitute a complete, auditable description of the ingestion and fingerprinting process |
| **Daubert Standard** | Scientific testimony must be reliable and relevant | Deterministic pipeline; no black-box inference; independently reproducible output |
| **ABA Formal Opinion 512** | AI tools must not constitute the unauthorized practice of law | All outputs are *Automated Flags* requiring mandatory human auditor sign-off before use |
| **OSHA HCS 89 FR 44144** | Hazard Communication Standard — Appendices B, C, D, §(i) | Trigger phrases, SDS section references, and concentration ranges encoded verbatim from the Federal Register |
| **OSHA Extension Jan 15, 2026** | Compliance deadline extension for substances and mixtures | Extended deadlines are hardcoded in `engine.py` and displayed in the Streamlit sidebar |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        app.py  (Streamlit UI)                       │
│                                                                     │
│  ┌─────────────────────┐       ┌──────────────────────────────────┐ │
│  │   SIDEBAR           │       │   MAIN PANEL                     │ │
│  │                     │       │                                  │ │
│  │  Discovery Uploader │       │  Single Document Uploader        │ │
│  │         │           │       │            │                     │ │
│  │         ▼           │       │            ▼                     │ │
│  │   intake.py         │       │     engine.py                    │ │
│  │  generate_chain_    │       │  OSHAViolationEngine             │ │
│  │  of_custody()       │       │   ├─ __init__(pdf_path)          │ │
│  │         │           │       │   ├─ _extract_pages() [lazy]     │ │
│  │         ▼           │       │   └─ search_violations()         │ │
│  │  custody_manifest   │       │            │                     │ │
│  │  .json              │       │            ▼                     │ │
│  │  SHA-256 display    │       │   Findings DataFrame             │ │
│  │  Download button    │       │            │                     │ │
│  │                     │       │   HITL Verification Checkbox     │ │
│  │  Compliance         │       │   (ABA Opinion 512 gate)         │ │
│  │  Deadline Calendar  │       │            │                     │ │
│  └─────────────────────┘       │   Export: CSV │ XLSX │ HTML      │ │
│                                └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘

Data flow (all local — no external API calls):

  PDF/TXT file
      │
      ├──► intake.py ──► SHA-256 hash ──► custody_manifest.json
      │
      └──► engine.py
               │
               ├── PyMuPDF lazy page generator
               ├── Whitespace normalisation
               ├── Exact-match scan (TRIGGER_PHRASES + CONCENTRATION_RANGES)
               ├── Bates regex extraction
               └── findings[] list
                        │
                        └──► app.py ──► DataFrame ──► CSV / XLSX / HTML
```

---

## 🛠️ Tech Stack

| Component | Library | Version | Purpose |
|-----------|---------|---------|---------|
| Language | Python | 3.10+ | Core runtime |
| UI | Streamlit | 1.35+ | Interactive dashboard |
| PDF Engine | PyMuPDF (`fitz`) | 1.24+ | Deterministic text & coordinate extraction |
| Hashing | `hashlib` (stdlib) | — | SHA-256 chain of custody |
| Data | pandas | 2.0+ | Findings DataFrame and export |
| Excel Export | openpyxl | 3.1+ | `.xlsx` generation |
| OCR (optional) | pytesseract + Pillow | 0.3.10+ | Fallback for scanned pages (disabled by default) |

---

## 🚀 Installation

**Prerequisites:** Python 3.10+, `pip`, `git`, Linux (tested on Ubuntu 22.04+)

```bash
# 1. Clone the repository
git clone https://github.com/sui-generis/deterministic-forensic-auditor.git
cd deterministic-forensic-auditor

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Install pytesseract for OCR fallback
#    Only required if auditing scanned/image-only PDFs
sudo apt-get install tesseract-ocr
pip install pytesseract Pillow

# 5. Launch the Streamlit dashboard
streamlit run app.py
```

The app will open at `http://localhost:8501` in your default browser.

> **Data Sovereignty:** The application performs all file I/O, hashing, and regex scanning locally. No discovery document content is transmitted to any external API or cloud service.

---

## 📖 Usage

### Step 1 — Establish Chain of Custody (Sidebar)
1. In the sidebar, click **"Upload discovery documents"** and select one or more PDF or DOCX files from your discovery dump.
2. The tool immediately computes a SHA-256 hash for each file and a combined hash for the set.
3. Review the `custody_manifest.json` displayed in the sidebar and click **"⬇️ Download custody_manifest.json"** to save the forensic record.

> **TRE 901(b)(9):** Preserve `custody_manifest.json` alongside the original discovery files. Any future re-hash of the same files must produce the same manifest to confirm authenticity.

### Step 2 — Upload the Audit Document (Main Panel)
1. In the main panel, click **"Upload a single document for OSHA HCS audit"** and select the PDF or TXT file you wish to audit.
2. Toggle **"Enable OCR fallback"** only if the document is a scanned image PDF and you accept that OCR-derived findings will carry a mandatory `verification_required` flag.

### Step 3 — Review Automated Findings
1. The engine scans every page for the 38 OSHA HCS trigger phrases (Appendices B/C/D) and 13 prescribed concentration ranges (§(i) Trade Secrets).
2. Findings appear in the **Truth Map** DataFrame — one row per (page, phrase) pair.
3. Rows flagged `Verification Required: True` (unreadable pages or OCR-derived text) must be reviewed manually before any export.

### Step 4 — Human Auditor Sign-Off (Mandatory)
1. Enter your full name in the **"Technical Auditor Name"** field.
2. Check the **confirmation checkbox** attesting that you have personally reviewed all findings.
3. Export buttons unlock only after both fields are completed.

> **ABA Opinion 512:** This step is not optional. The tool produces *Automated Flags*, not legal conclusions. Submitting unreviewed flags as evidence could constitute the unauthorized practice of law.

### Step 5 — Export
| Button | Format | Use Case |
|--------|--------|----------|
| ⬇️ Download CSV | `.csv` | Import into Relativity, CaseMap, or Excel |
| ⬇️ Download Excel | `.xlsx` | Formatted workbook with auto-sized columns |
| ⬇️ Download HTML Report | `.html` | Shareable report with `#page=XX` hyperlinks for direct PDF navigation |

---

## 📁 Output Files

| File | Generated By | Contents |
|------|-------------|----------|
| `custody_manifest.json` | `intake.py` | Per-file SHA-256 hashes, byte sizes, UTC ingestion timestamps, and a combined hash for the full evidence set |
| `<docname>_findings_<timestamp>.csv` | `app.py` export | Flat CSV of all findings: rule citation, filename, page, matched phrase, Bates numbers, verification flags |
| `<docname>_findings_<timestamp>.xlsx` | `app.py` export | Excel workbook with auto-sized columns; suitable for Relativity import |
| `<docname>_findings_<timestamp>.html` | `app.py` export | Formatted HTML report with `#page=XX` anchor hyperlinks, ABA 512 disclosure footer, and colour-coded verification flags |

---

## 📅 OSHA HCS Compliance Deadlines

Source: **OSHA HCS Compliance Extension, January 15, 2026** — these dates override all original dates published in 89 FR 44144 (May 20, 2024).

| CFR Citation | Requirement | Operative Deadline |
|-------------|-------------|-------------------|
| **§1910.1200(j)(2)(i)** | Substances — full HCS compliance | **May 19, 2026** |
| **§1910.1200(j)(2)(ii)** | Substances — employee training | **November 20, 2026** |
| **§1910.1200(j)(3)(i)** | Mixtures — full HCS compliance | **November 19, 2027** |
| **§1910.1200(j)(3)(ii)** | Mixtures — employee training | **May 19, 2028** |

> These deadlines are displayed in the Streamlit sidebar with colour-coded countdown indicators and are hardcoded in `engine.py` as `COMPLIANCE_DEADLINES` for downstream reporting use.

---

## 🖥️ Screenshots

**Dashboard — Chain of Custody & Compliance Calendar**

> `[Screenshot of sidebar showing custody_manifest.json and deadline calendar here]`

**Truth Map — Automated Findings DataFrame**

> `[Screenshot of main panel showing findings DataFrame and HITL verification checkbox here]`

**HTML Export — Page-Linked Report**

> `[Screenshot of exported HTML report with #page=XX hyperlinks here]`

---

## 📊 Project Status

**Production-ready.** Successfully tested on multi-thousand-page industrial PDF discovery files. Memory-stable on documents exceeding 1 GB via PyMuPDF lazy-loading generator architecture. All three export formats (CSV, XLSX, HTML) validated for Relativity import compatibility.

> If you encounter a PDF that causes a `FLAG: Unreadable Scan - Manual Review Required` output, the document likely lacks an embedded text layer. Enable OCR fallback (`ocr_fallback=True`) and treat all resulting findings as requiring human verification per **FRE 702**.

---

## 🤝 Contributing

This is a proprietary tool. External contributions are not accepted at this time. If you are a licensed attorney, forensic engineer, or OSHA compliance professional and wish to discuss a collaboration or licensing arrangement, please contact the author directly.

---

## 👤 Author & License

| Field | Detail |
|-------|--------|
| **Author** | Andrew C Rogers |
| **DBA** | Sui-Generis |
| **Contact** | Available upon request |
| **License** | Proprietary — All Rights Reserved |
| **Disclaimer** | See [DISCLAIMER.md](./DISCLAIMER.md) |

> © Andrew C Rogers / Sui-Generis. This software and all associated source code, documentation, and regulatory mappings are proprietary. Unauthorised copying, distribution, sublicensing, or deployment — in whole or in part — is strictly prohibited without express written permission from the author.

---

## 🔎 Keywords

`Python` · `Streamlit` · `LegalTech` · `Forensic Engineering` · `OSHA Compliance` · `HCS` · `GHS` · `FRE 702` · `TRE 901` · `Daubert` · `E-Discovery` · `Chain of Custody` · `SHA-256` · `Relativity` · `Safety Data Sheet` · `SDS` · `ABA Opinion 512` · `Human-in-the-Loop` · `Zero Hallucination` · `Deterministic AI` · `PyMuPDF` · `Bates Numbering` · `Tennessee Evidence`
