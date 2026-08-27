from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pytest

from matcher import SemanticMatcher


def test_similarity_identical_vectors():
    vector = np.array([1.0, 0.0, 0.0])

    score = SemanticMatcher.calculate_similarity(vector, vector)

    assert score == pytest.approx(1.0)


def test_similarity_to_percentage():
    assert SemanticMatcher.similarity_to_percentage(0.87) == 87.0
    assert SemanticMatcher.similarity_to_percentage(0.5) == 50.0


def test_empty_text_is_rejected():
    with pytest.raises(ValueError):
        SemanticMatcher._validate_text("", "resume_text")