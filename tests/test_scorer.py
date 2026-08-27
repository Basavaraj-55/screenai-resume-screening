from pathlib import Path
import sys

# Add the src directory to Python's import path
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from scorer import REQUIRED_SKILLS, evaluate_skills


def test_required_skills_match():
    """All required skills should be detected."""
    resume = """
    Python developer with Flask and FastAPI experience.
    REST API development using SQL and PostgreSQL.
    Git and GitHub.
    Object-oriented programming and data structures.
    Exception handling and JWT authentication.
    """

    result = evaluate_skills(resume, REQUIRED_SKILLS)

    assert result.score == 100.0
    assert len(result.matched) == len(REQUIRED_SKILLS)
    assert result.missing == []


def test_missing_skills_are_detected():
    """Missing skills should be identified correctly."""
    resume = """
    Python developer with Flask experience.
    """

    result = evaluate_skills(resume, REQUIRED_SKILLS)

    assert result.score < 100.0
    assert "Python" in result.matched
    assert len(result.missing) > 0