"""
Resume Screening Agent
======================

NLP Matching Engine

This module compares a Job Description (JD) with candidate resumes
using semantic embeddings and cosine similarity.

Pipeline:
    Job Description
          ↓
    Sentence Transformer
          ↓
    JD Embedding
          ↓
    Resume Embeddings
          ↓
    Cosine Similarity
          ↓
    Relevance Score
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================================
# Logging
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"

# Similarity is converted from [0, 1] to a percentage.
MIN_SCORE = 0.0
MAX_SCORE = 100.0


# ============================================================================
# Data Models
# ============================================================================

@dataclass(frozen=True)
class MatchResult:
    """
    Represents the semantic similarity between a resume and a Job Description.

    Attributes:
        candidate_name: Resume filename.
        similarity_score: Raw cosine similarity.
        relevance_score: Similarity represented as a percentage.
    """

    candidate_name: str
    similarity_score: float
    relevance_score: float


# ============================================================================
# Exceptions
# ============================================================================

class MatcherError(Exception):
    """Base exception for NLP matching failures."""


# ============================================================================
# Embedding Model
# ============================================================================

class SemanticMatcher:
    """
    Semantic matching engine powered by Sentence Transformers.

    The model converts text into numerical vectors called embeddings.
    Semantically similar documents produce embeddings that are closer
    together in vector space.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
    ) -> None:
        """
        Initialize the semantic matching engine.

        Args:
            model_name: Sentence Transformer model identifier.
        """

        self.model_name = model_name

        logger.info(
            "Loading Sentence Transformer model: %s",
            model_name,
        )

        try:
            self.model = SentenceTransformer(model_name)

        except Exception as exc:
            raise MatcherError(
                f"Unable to load embedding model: {model_name}"
            ) from exc

        logger.info("Embedding model loaded successfully.")

    # ------------------------------------------------------------------------
    # Text Validation
    # ------------------------------------------------------------------------

    @staticmethod
    def _validate_text(text: str, field_name: str) -> None:
        """
        Validate input text before generating embeddings.
        """

        if not isinstance(text, str):
            raise TypeError(
                f"{field_name} must be a string."
            )

        if not text.strip():
            raise ValueError(
                f"{field_name} cannot be empty."
            )

    # ------------------------------------------------------------------------
    # Embedding Generation
    # ------------------------------------------------------------------------

    def encode(self, text: str) -> np.ndarray:
        """
        Convert text into a semantic embedding vector.

        Args:
            text: Input document text.

        Returns:
            NumPy embedding vector.
        """

        self._validate_text(text, "text")

        try:
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )

            return embedding

        except Exception as exc:
            raise MatcherError(
                "Failed to generate text embedding."
            ) from exc

    # ------------------------------------------------------------------------
    # Similarity Calculation
    # ------------------------------------------------------------------------

    @staticmethod
    def calculate_similarity(
        first_embedding: np.ndarray,
        second_embedding: np.ndarray,
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Returns:
            Similarity value between 0 and 1.
        """

        first_vector = np.asarray(first_embedding).reshape(1, -1)
        second_vector = np.asarray(second_embedding).reshape(1, -1)

        score = cosine_similarity(
            first_vector,
            second_vector,
        )[0][0]

        # Numerical safety.
        return float(np.clip(score, 0.0, 1.0))

    # ------------------------------------------------------------------------
    # Score Conversion
    # ------------------------------------------------------------------------

    @staticmethod
    def similarity_to_percentage(
        similarity: float,
    ) -> float:
        """
        Convert cosine similarity into a percentage score.

        Example:
            0.87 → 87.0
        """

        score = similarity * MAX_SCORE

        return round(
            np.clip(
                score,
                MIN_SCORE,
                MAX_SCORE,
            ),
            2,
        )

    # ------------------------------------------------------------------------
    # Single Resume Matching
    # ------------------------------------------------------------------------

    def match(
        self,
        job_description: str,
        resume_text: str,
        candidate_name: str,
    ) -> MatchResult:
        """
        Compare one resume against a Job Description.

        Args:
            job_description: Job Description text.
            resume_text: Candidate resume text.
            candidate_name: Candidate filename.

        Returns:
            MatchResult containing similarity and relevance scores.
        """

        self._validate_text(
            job_description,
            "job_description",
        )

        self._validate_text(
            resume_text,
            "resume_text",
        )

        logger.debug(
            "Matching candidate: %s",
            candidate_name,
        )

        jd_embedding = self.encode(job_description)
        resume_embedding = self.encode(resume_text)

        similarity = self.calculate_similarity(
            jd_embedding,
            resume_embedding,
        )

        relevance_score = self.similarity_to_percentage(
            similarity
        )

        return MatchResult(
            candidate_name=candidate_name,
            similarity_score=round(similarity, 4),
            relevance_score=relevance_score,
        )

    # ------------------------------------------------------------------------
    # Batch Matching
    # ------------------------------------------------------------------------

    def match_batch(
        self,
        job_description: str,
        resumes: Sequence,
    ) -> list[MatchResult]:
        """
        Compare a Job Description against multiple resumes.

        The Job Description embedding is generated only once,
        which is more efficient than encoding it repeatedly.

        Args:
            job_description: Job Description text.
            resumes: Collection of ParsedDocument-like objects.

        Returns:
            List of MatchResult objects.
        """

        self._validate_text(
            job_description,
            "job_description",
        )

        if not resumes:
            logger.warning("No resumes provided for matching.")
            return []

        logger.info(
            "Starting batch matching for %d resumes.",
            len(resumes),
        )

        # Encode JD only once.
        jd_embedding = self.encode(job_description)

        results: list[MatchResult] = []

        for resume in resumes:

            try:
                resume_embedding = self.encode(
                    resume.text
                )

                similarity = self.calculate_similarity(
                    jd_embedding,
                    resume_embedding,
                )

                relevance_score = self.similarity_to_percentage(
                    similarity
                )

                result = MatchResult(
                    candidate_name=resume.filename,
                    similarity_score=round(
                        similarity,
                        4,
                    ),
                    relevance_score=relevance_score,
                )

                results.append(result)

                logger.info(
                    "Matched %-25s → %.2f%%",
                    resume.filename,
                    relevance_score,
                )

            except Exception as exc:
                logger.error(
                    "Failed to match %s: %s",
                    resume.filename,
                    exc,
                )

        logger.info(
            "Batch matching completed: %d results.",
            len(results),
        )

        return results


# ============================================================================
# Ranking Utility
# ============================================================================

def rank_candidates(
    results: Sequence[MatchResult],
) -> list[MatchResult]:
    """
    Rank candidates from highest to lowest relevance score.

    Args:
        results: Candidate match results.

    Returns:
        Sorted candidate results.
    """

    return sorted(
        results,
        key=lambda result: result.relevance_score,
        reverse=True,
    )


# ============================================================================
# Convenience Function
# ============================================================================

@lru_cache(maxsize=1)
def get_matcher(
    model_name: str = DEFAULT_MODEL_NAME,
) -> SemanticMatcher:
    """
    Return a cached SemanticMatcher instance.

    Caching prevents repeatedly loading the embedding model
    when the matcher is requested multiple times.
    """

    return SemanticMatcher(model_name)


# ============================================================================
# Local Development Test
# ============================================================================

if __name__ == "__main__":

    from parser import load_job_description, load_resumes

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    print("\n" + "=" * 70)
    print("🤖 RESUME SCREENING AGENT")
    print("🧠 NLP SEMANTIC MATCHING ENGINE")
    print("=" * 70)

    # ------------------------------------------------------------------------
    # Load documents
    # ------------------------------------------------------------------------

    job_description = load_job_description(
        "data/job_description.txt"
    )

    resumes = load_resumes(
        "data/resumes"
    )

    print(
        f"\n📄 Resumes loaded: {len(resumes)}"
    )

    # ------------------------------------------------------------------------
    # Initialize matcher
    # ------------------------------------------------------------------------

    matcher = get_matcher()

    # ------------------------------------------------------------------------
    # Calculate semantic matches
    # ------------------------------------------------------------------------

    results = matcher.match_batch(
        job_description=job_description.text,
        resumes=resumes,
    )

    # ------------------------------------------------------------------------
    # Rank candidates
    # ------------------------------------------------------------------------

    ranked_results = rank_candidates(results)

    # ------------------------------------------------------------------------
    # Display results
    # ------------------------------------------------------------------------

    print("\n" + "=" * 70)
    print("🏆 CANDIDATE RELEVANCE RANKING")
    print("=" * 70)

    for rank, result in enumerate(
        ranked_results,
        start=1,
    ):
        print(
            f"{rank:02d}. "
            f"{result.candidate_name:<25} "
            f"{result.relevance_score:>6.2f}%"
        )

    print("\n" + "=" * 70)
    print("✅ NLP MATCHING COMPLETED")
    print("=" * 70)