from __future__ import annotations

import re
from pathlib import Path

try:
    import fitz  # type: ignore
except ImportError:  # pragma: no cover - runtime dependency for PDF parsing
    fitz = None


REGULATORY_TRIGGERS = [
    "hazardous chemical",
    "safety data sheet",
    "label",
    "flammable gas",
    "desensitized explosives",
    "combustible dust",
    "aerosol",
    "concentration range",
    "trade secret",
]


class OSHAViolationEngine:
    def __init__(self, pdf_path: str):
        if fitz is None:
            raise ImportError("PyMuPDF (fitz) is required to load OSHA PDFs")

        self.pdf_path = Path(pdf_path)
        self.pdf_filename = self.pdf_path.name
        self._doc = fitz.open(str(self.pdf_path))
        self._pages: list[dict] | None = None

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip().lower()

    def _extract_pages(self) -> list[dict]:
        if self._pages is None:
            # FRE 702 + TRE 901(b)(9): lazy extraction preserves source fidelity and reproducibility.
            self._pages = [
                {
                    "page_number": index + 1,
                    "text": page.get_text("text"),
                }
                for index, page in enumerate(self._doc)
            ]
        return self._pages

    def search_violations(self, document_text: str) -> list[dict]:
        normalized_document = self._normalize_whitespace(document_text)
        pages = self._extract_pages()

        findings: list[dict] = []
        for trigger in REGULATORY_TRIGGERS:
            normalized_trigger = self._normalize_whitespace(trigger)
            if normalized_trigger not in normalized_document:
                continue

            for page in pages:
                normalized_rule_text = self._normalize_whitespace(page["text"])
                if normalized_trigger in normalized_rule_text:
                    findings.append(
                        {
                            "rule_text": page["text"],
                            "pdf_filename": self.pdf_filename,
                            "page_number": page["page_number"],
                            "matched_phrase": trigger,
                        }
                    )
        return findings
