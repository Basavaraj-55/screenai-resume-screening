from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from parser import normalize_text, parse_document


def test_normalize_text():
    text = "  Python   Developer\r\n\r\n\r\n Flask  "

    result = normalize_text(text)

    assert result == "Python Developer\n\nFlask"


def test_parse_txt_file(tmp_path):
    resume = tmp_path / "candidate.txt"

    resume.write_text(
        "Python Developer\nFlask\nREST API\nSQL",
        encoding="utf-8"
    )

    result = parse_document(resume)

    assert result.filename == "candidate.txt"
    assert result.file_type == ".txt"
    assert "Python Developer" in result.text
    assert result.character_count > 0