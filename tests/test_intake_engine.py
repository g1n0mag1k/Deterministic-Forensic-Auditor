import hashlib
import tempfile
import unittest
from pathlib import Path

from engine import OSHAViolationEngine
from intake import generate_chain_of_custody


class TestIntake(unittest.TestCase):
    def test_generate_chain_of_custody_single_and_combined_hash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = Path.cwd()
            tmp_path = Path(tmpdir)
            file_a = tmp_path / "a.txt"
            file_b = tmp_path / "b.txt"
            file_a.write_text("hazardous chemical", encoding="utf-8")
            file_b.write_text("combustible dust", encoding="utf-8")

            try:
                # manifest is expected to be emitted in working directory
                import os
                os.chdir(tmp_path)
                manifest = generate_chain_of_custody([str(file_a), str(file_b)])
            finally:
                os.chdir(cwd)

            self.assertEqual(len(manifest["files"]), 2)
            for entry in manifest["files"]:
                self.assertIn("timestamp", entry)
                self.assertIn("filename", entry)
                self.assertIn("hash", entry)
                self.assertIn("size_bytes", entry)

            expected_hashes = sorted(
                [
                    hashlib.sha256(file_a.read_bytes()).hexdigest(),
                    hashlib.sha256(file_b.read_bytes()).hexdigest(),
                ]
            )
            expected_combined = hashlib.sha256("".join(expected_hashes).encode("utf-8")).hexdigest()
            self.assertEqual(manifest["combined_hash"], expected_combined)
            self.assertTrue((tmp_path / "custody_manifest.json").exists())


class TestEngine(unittest.TestCase):
    def test_search_violations_uses_normalized_matching(self):
        engine = OSHAViolationEngine.__new__(OSHAViolationEngine)
        engine.pdf_filename = "osha.pdf"
        engine._pages = [
            {"page_number": 3, "text": "A safety   data sheet must list concentration range for each hazardous chemical."},
            {"page_number": 7, "text": "Label requirements include aerosol handling details."},
        ]
        engine._extract_pages = lambda: engine._pages

        findings = engine.search_violations(
            "Document references SAFETY data\n\nSHEET and concentration   range and aerosol and label controls."
        )

        phrases = {item["matched_phrase"] for item in findings}
        self.assertIn("safety data sheet", phrases)
        self.assertIn("concentration range", phrases)
        self.assertIn("aerosol", phrases)
        self.assertIn("label", phrases)
        self.assertTrue(all(item["pdf_filename"] == "osha.pdf" for item in findings))


if __name__ == "__main__":
    unittest.main()
