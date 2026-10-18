import pytest
import io
import os
from cv_parser import extract_text_from_cv, validate_cv_file, CVExtractionError

class DummyFile:
    def __init__(self, name: str, content: bytes, size: int | None = None):
        self.name = name
        self._content = content
        self.size = size if size is not None else len(content)
        self._io = io.BytesIO(content)

    def read(self, *args, **kwargs):
        return self._io.read(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self._io.seek(*args, **kwargs)

class TestCVParser:
    def test_text_file_extraction(self):
        content = "Jane Doe\nSoftware Engineer\nSkills: Python, FastAPI, Docker".encode("utf-8")
        f = DummyFile("resume.txt", content)
        text = extract_text_from_cv(f)
        assert "Jane Doe" in text
        assert "Python" in text

    def test_csv_file_extraction(self):
        content = "Techstack,Links\nPython,https://github.com/test\nReact,https://github.com/react".encode("utf-8")
        f = DummyFile("portfolio.csv", content)
        text = extract_text_from_cv(f)
        assert "Python" in text
        assert "React" in text

    def test_disallowed_file_extension(self):
        f = DummyFile("malicious.exe", b"binarycontent")
        with pytest.raises(CVExtractionError) as exc_info:
            extract_text_from_cv(f)
        assert "Unsupported file format" in str(exc_info.value)

    def test_oversized_file_rejected(self):
        # 16 MB dummy file
        oversized = 16 * 1024 * 1024
        f = DummyFile("huge_resume.pdf", b"abc", size=oversized)
        with pytest.raises(CVExtractionError) as exc_info:
            validate_cv_file(f)
        assert "exceeds the 15 MB limit" in str(exc_info.value)

    def test_empty_file_rejected(self):
        f = DummyFile("empty.txt", b"   ")
        with pytest.raises(CVExtractionError) as exc_info:
            extract_text_from_cv(f)
        assert "does not contain readable text" in str(exc_info.value)
