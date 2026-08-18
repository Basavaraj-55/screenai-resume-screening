"""
Resume Screening Agent
======================

Candidate Ranking Engine

Responsibilities:
    - Sort candidates by final score.
    - Assign stable ranking positions.
    - Select Top-K candidates.
    - Handle score ties consistently.
    - Provide ranking summaries.
    - Prepare structured data for reporting.

This module does NOT calculate candidate scores.
Scoring is handled by scorer.py.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Sequence

from scorer import CandidateScore


# ============================================================================
# Logging
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

DEFAULT_TOP_K = 5
DEFAULT_SCORE_THRESHOLD = 70.0


# ============================================================================
# Data Models
# ============================================================================

@dataclass(frozen=True)
class RankedCandidate:
    """
    Represents a candidate with an assigned ranking position.
    """

    rank: int
    candidate_name: str
    final_score: float
    recommendation: str
    semantic_score: float
    required_skill_score: float
    preferred_skill_score: float
    experience_score: float
    education_score: float
    matched_skills: list[str]
    missing_skills: list[str]


@dataclass(frozen=True)
class RankingSummary:
    """
    Summary of the complete candidate ranking.
    """

    total_candidates: int
    selected_candidates: int
    strong_matches: int
    good_matches: int
    moderate_matches: int
    weak_matches: int
    average_score: float
    highest_score: float
    lowest_score: float


# ============================================================================
# Exceptions
# ============================================================================

class RankingError(Exception):
    """Base exception for ranking-related failures."""


# ============================================================================
# Ranking Engine
# ============================================================================

class CandidateRanker:
    """
    Professional ranking engine for screened candidates.

    The ranker receives already-scored candidates and transforms them
    into an ordered ranking.
    """

    def __init__(
        self,
        top_k: int = DEFAULT_TOP_K,
        score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    ) -> None:

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        if not 0 <= score_threshold <= 100:
            raise ValueError(
                "score_threshold must be between 0 and 100."
            )

        self.top_k = top_k
        self.score_threshold = score_threshold

    # ------------------------------------------------------------------------
    # Sort Candidates
    # ------------------------------------------------------------------------

    @staticmethod
    def _sort_candidates(
        candidates: Sequence[CandidateScore],
    ) -> list[CandidateScore]:
        """
        Sort candidates by final score.

        Secondary sorting uses required skill score and semantic score
        to make ordering deterministic when final scores are equal.
        """

        return sorted(
            candidates,
            key=lambda candidate: (
                candidate.final_score,
                candidate.required_skill_score,
                candidate.semantic_score,
            ),
            reverse=True,
        )

    # ------------------------------------------------------------------------
    # Assign Ranks
    # ------------------------------------------------------------------------

    @staticmethod
    def _assign_ranks(
        candidates: Sequence[CandidateScore],
    ) -> list[RankedCandidate]:
        """
        Convert CandidateScore objects into RankedCandidate objects.
        """

        ranked_candidates: list[RankedCandidate] = []

        previous_score: float | None = None
        previous_rank: int = 0

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):

            # Competition ranking:
            #
            # 1 → 2 → 2 → 4
            #
            # Candidates with identical final scores share a rank.

            if (
                previous_score is not None
                and candidate.final_score == previous_score
            ):
                rank = previous_rank

            else:
                rank = index

            ranked_candidates.append(
                RankedCandidate(
                    rank=rank,
                    candidate_name=candidate.candidate_name,
                    final_score=candidate.final_score,
                    recommendation=candidate.recommendation,
                    semantic_score=candidate.semantic_score,
                    required_skill_score=(
                        candidate.required_skill_score
                    ),
                    preferred_skill_score=(
                        candidate.preferred_skill_score
                    ),
                    experience_score=(
                        candidate.experience_score
                    ),
                    education_score=(
                        candidate.education_score
                    ),
                    matched_skills=(
                        candidate.required_skills.matched
                    ),
                    missing_skills=(
                        candidate.required_skills.missing
                    ),
                )
            )

            previous_score = candidate.final_score
            previous_rank = rank

        return ranked_candidates

    # ------------------------------------------------------------------------
    # Full Ranking
    # ------------------------------------------------------------------------

    def rank(
        self,
        candidates: Sequence[CandidateScore],
    ) -> list[RankedCandidate]:
        """
        Rank all candidates.

        Args:
            candidates:
                Candidate scoring results.

        Returns:
            Ordered list of RankedCandidate objects.
        """

        if not candidates:
            logger.warning(
                "No candidates available for ranking."
            )
            return []

        logger.info(
            "Ranking %d candidates.",
            len(candidates),
        )

        sorted_candidates = self._sort_candidates(
            candidates
        )

        ranked_candidates = self._assign_ranks(
            sorted_candidates
        )

        logger.info(
            "Candidate ranking completed."
        )

        return ranked_candidates

    # ------------------------------------------------------------------------
    # Top-K Selection
    # ------------------------------------------------------------------------

    def select_top_candidates(
        self,
        ranked_candidates: Sequence[RankedCandidate],
    ) -> list[RankedCandidate]:
        """
        Select the Top-K candidates.

        Candidates must also meet the configured score threshold.
        """

        eligible_candidates = [
            candidate
            for candidate in ranked_candidates
            if candidate.final_score >= self.score_threshold
        ]

        selected = eligible_candidates[:self.top_k]

        logger.info(
            "Selected %d candidates from Top-K=%d.",
            len(selected),
            self.top_k,
        )

        return selected

    # ------------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------------

    @staticmethod
    def create_summary(
        ranked_candidates: Sequence[RankedCandidate],
        selected_candidates: Sequence[RankedCandidate],
    ) -> RankingSummary:
        """
        Generate ranking statistics.
        """

        if not ranked_candidates:
            return RankingSummary(
                total_candidates=0,
                selected_candidates=0,
                strong_matches=0,
                good_matches=0,
                moderate_matches=0,
                weak_matches=0,
                average_score=0.0,
                highest_score=0.0,
                lowest_score=0.0,
            )

        scores = [
            candidate.final_score
            for candidate in ranked_candidates
        ]

        strong_matches = sum(
            candidate.recommendation == "Strong Match"
            for candidate in ranked_candidates
        )

        good_matches = sum(
            candidate.recommendation == "Good Match"
            for candidate in ranked_candidates
        )

        moderate_matches = sum(
            candidate.recommendation == "Moderate Match"
            for candidate in ranked_candidates
        )

        weak_matches = sum(
            candidate.recommendation == "Weak Match"
            for candidate in ranked_candidates
        )

        return RankingSummary(
            total_candidates=len(ranked_candidates),
            selected_candidates=len(selected_candidates),
            strong_matches=strong_matches,
            good_matches=good_matches,
            moderate_matches=moderate_matches,
            weak_matches=weak_matches,
            average_score=round(
                sum(scores) / len(scores),
                2,
            ),
            highest_score=max(scores),
            lowest_score=min(scores),
        )


# ============================================================================
# Display Utilities
# ============================================================================

def display_ranking(
    ranked_candidates: Sequence[RankedCandidate],
) -> None:
    """
    Display the complete candidate ranking.
    """

    print("\n" + "=" * 100)
    print("🏆 FINAL CANDIDATE RANKING")
    print("=" * 100)

    print(
        f"{'Rank':<7}"
        f"{'Candidate':<25}"
        f"{'Final Score':>15}"
        f"{'Decision':>25}"
    )

    print("-" * 100)

    for candidate in ranked_candidates:

        print(
            f"{candidate.rank:<7}"
            f"{candidate.candidate_name:<25}"
            f"{candidate.final_score:>13.2f}%"
            f"{candidate.recommendation:>25}"
        )

    print("=" * 100)


def display_top_candidates(
    candidates: Sequence[RankedCandidate],
) -> None:
    """
    Display the selected Top-K candidates.
    """

    print("\n" + "=" * 100)
    print("⭐ TOP CANDIDATES FOR SHORTLIST")
    print("=" * 100)

    if not candidates:
        print(
            "\n⚠️ No candidates met the configured score threshold."
        )
        return

    for candidate in candidates:

        print(
            f"\n#{candidate.rank} "
            f"{candidate.candidate_name}"
        )

        print(
            f"   Final Score : {candidate.final_score:.2f}%"
        )

        print(
            f"   Decision    : {candidate.recommendation}"
        )

        print(
            f"   Required    : "
            f"{candidate.required_skill_score:.2f}%"
        )

        print(
            f"   Matched     : "
            f"{', '.join(candidate.matched_skills)}"
        )

        if candidate.missing_skills:

            print(
                f"   Missing     : "
                f"{', '.join(candidate.missing_skills)}"
            )

    print("\n" + "=" * 100)


def display_summary(
    summary: RankingSummary,
) -> None:
    """
    Display overall ranking statistics.
    """

    print("\n📊 SCREENING SUMMARY")
    print("-" * 50)

    print(
        f"Total Candidates : {summary.total_candidates}"
    )

    print(
        f"Shortlisted      : {summary.selected_candidates}"
    )

    print(
        f"Strong Matches   : {summary.strong_matches}"
    )

    print(
        f"Good Matches     : {summary.good_matches}"
    )

    print(
        f"Moderate Matches : {summary.moderate_matches}"
    )

    print(
        f"Weak Matches     : {summary.weak_matches}"
    )

    print(
        f"Average Score    : {summary.average_score:.2f}%"
    )

    print(
        f"Highest Score    : {summary.highest_score:.2f}%"
    )

    print(
        f"Lowest Score     : {summary.lowest_score:.2f}%"
    )


# ============================================================================
# Local Development Test
# ============================================================================

if __name__ == "__main__":

    from matcher import get_matcher
    from parser import (
        load_job_description,
        load_resumes,
    )
    from scorer import score_candidates

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    print("\n" + "=" * 100)
    print("🤖 RESUME SCREENING AGENT")
    print("🏆 CANDIDATE RANKING ENGINE")
    print("=" * 100)

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
    # NLP matching
    # ------------------------------------------------------------------------

    matcher = get_matcher()

    match_results = matcher.match_batch(
        job_description=job_description.text,
        resumes=resumes,
    )

    # ------------------------------------------------------------------------
    # Candidate scoring
    # ------------------------------------------------------------------------

    scored_candidates = score_candidates(
        match_results=match_results,
        resumes=resumes,
    )

    # ------------------------------------------------------------------------
    # Candidate ranking
    # ------------------------------------------------------------------------

    ranker = CandidateRanker(
        top_k=5,
        score_threshold=70.0,
    )

    ranked_candidates = ranker.rank(
        scored_candidates
    )

    # ------------------------------------------------------------------------
    # Top-K selection
    # ------------------------------------------------------------------------

    top_candidates = ranker.select_top_candidates(
        ranked_candidates
    )

    # ------------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------------

    summary = ranker.create_summary(
        ranked_candidates=ranked_candidates,
        selected_candidates=top_candidates,
    )

    # ------------------------------------------------------------------------
    # Display results
    # ------------------------------------------------------------------------

    display_ranking(
        ranked_candidates
    )

    display_top_candidates(
        top_candidates
    )

    display_summary(
        summary
    )

    print("\n" + "=" * 100)
    print("✅ RANKING PIPELINE COMPLETED")
    print("=" * 100)