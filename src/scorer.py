"""
Resume Screening Agent
======================

Candidate Scoring Engine

This module converts semantic matching results into an explainable
candidate score by combining:

    1. Semantic similarity
    2. Required technical skills
    3. Preferred technical skills
    4. Backend development experience
    5. Relevant professional experience
    6. Education

The scoring layer is intentionally separate from the NLP matcher
so that the ranking logic remains transparent and configurable.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Sequence

from matcher import MatchResult


# ============================================================================
# Logging
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

SEMANTIC_WEIGHT = 0.40
REQUIRED_SKILLS_WEIGHT = 0.35
PREFERRED_SKILLS_WEIGHT = 0.10
EXPERIENCE_WEIGHT = 0.10
EDUCATION_WEIGHT = 0.05


REQUIRED_SKILLS = {
    "python": [
        r"\bpython\b",
    ],
    "backend_framework": [
        r"\bflask\b",
        r"\bfastapi\b",
    ],
    "rest_api": [
        r"\brestful api\b",
        r"\brest api\b",
        r"\brest apis\b",
        r"\bapi development\b",
    ],
    "sql": [
        r"\bsql\b",
    ],
    "relational_database": [
        r"\bmysql\b",
        r"\bpostgresql\b",
        r"\bpostgres\b",
    ],
    "git": [
        r"\bgit\b",
        r"\bgithub\b",
    ],
    "oop": [
        r"\bobject[- ]oriented programming\b",
        r"\boop\b",
    ],
    "dsa": [
        r"\bdata structures\b",
        r"\bdata structures and algorithms\b",
        r"\balgorithms\b",
    ],
    "exception_handling": [
        r"\bexception handling\b",
        r"\berror handling\b",
    ],
    "jwt": [
        r"\bjwt\b",
        r"\bjson web token\b",
        r"\bauthentication\b",
    ],
}


PREFERRED_SKILLS = {
    "docker": [
        r"\bdocker\b",
        r"\bcontainerization\b",
    ],
    "cloud": [
        r"\baws\b",
        r"\bazure\b",
        r"\bgcp\b",
        r"\bcloud\b",
    ],
    "mongodb": [
        r"\bmongodb\b",
        r"\bmongo\b",
    ],
    "redis": [
        r"\bredis\b",
        r"\bcaching\b",
    ],
    "celery": [
        r"\bcelery\b",
        r"\bbackground task\b",
    ],
    "cicd": [
        r"\bci/cd\b",
        r"\bci cd\b",
        r"\bcontinuous integration\b",
        r"\bcontinuous deployment\b",
    ],
    "linux": [
        r"\blinux\b",
    ],
    "pytest": [
        r"\bpytest\b",
        r"\bunit testing\b",
        r"\bautomated testing\b",
    ],
}


# ============================================================================
# Data Models
# ============================================================================

@dataclass(frozen=True)
class SkillResult:
    """
    Represents skill matching information for a candidate.
    """

    matched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    score: float = 0.0


@dataclass(frozen=True)
class CandidateScore:
    """
    Final explainable candidate score.

    Attributes:
        candidate_name:
            Resume filename.

        semantic_score:
            NLP semantic similarity score.

        required_skill_score:
            Percentage of required skill categories matched.

        preferred_skill_score:
            Percentage of preferred skills matched.

        experience_score:
            Experience relevance score.

        education_score:
            Education relevance score.

        final_score:
            Weighted final score.

        required_skills:
            Skill matching details.

        preferred_skills:
            Preferred skill matching details.

        recommendation:
            Human-readable screening recommendation.
    """

    candidate_name: str
    semantic_score: float
    required_skill_score: float
    preferred_skill_score: float
    experience_score: float
    education_score: float
    final_score: float
    required_skills: SkillResult
    preferred_skills: SkillResult
    recommendation: str


# ============================================================================
# Exceptions
# ============================================================================

class ScoringError(Exception):
    """Base exception for scoring failures."""


# ============================================================================
# Text Utilities
# ============================================================================

def normalize_resume_text(text: str) -> str:
    """
    Normalize resume text before skill detection.
    """

    if not isinstance(text, str):
        raise TypeError("Resume text must be a string.")

    return re.sub(
        r"\s+",
        " ",
        text.lower(),
    ).strip()


def contains_skill(
    text: str,
    patterns: Sequence[str],
) -> bool:
    """
    Check whether any pattern exists in the resume text.
    """

    return any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in patterns
    )


# ============================================================================
# Skill Analysis
# ============================================================================

def evaluate_skills(
    resume_text: str,
    skill_definitions: dict[str, list[str]],
) -> SkillResult:
    """
    Evaluate a resume against a skill dictionary.

    Args:
        resume_text:
            Candidate resume content.

        skill_definitions:
            Skill categories and matching expressions.

    Returns:
        SkillResult containing matched/missing skills and score.
    """

    text = normalize_resume_text(resume_text)

    matched: list[str] = []
    missing: list[str] = []

    for skill_name, patterns in skill_definitions.items():

        if contains_skill(text, patterns):
            matched.append(skill_name)
        else:
            missing.append(skill_name)

    total_skills = len(skill_definitions)

    score = (
        len(matched) / total_skills * 100
        if total_skills
        else 0.0
    )

    return SkillResult(
        matched=matched,
        missing=missing,
        score=round(score, 2),
    )


# ============================================================================
# Experience Analysis
# ============================================================================

def calculate_experience_score(
    resume_text: str,
) -> float:
    """
    Estimate experience relevance.

    Strong signals:
        - Backend development
        - Python development
        - Software engineering
        - REST API development
        - Relevant years of experience
    """

    text = normalize_resume_text(resume_text)

    score = 0.0

    backend_signals = [
        "backend developer",
        "backend engineer",
        "backend development",
        "python developer",
        "python backend",
        "software engineer",
        "software developer",
        "rest api",
        "restful api",
    ]

    signal_count = sum(
        1
        for signal in backend_signals
        if signal in text
    )

    # Up to 70 points for relevant role signals.
    score += min(
        signal_count * 10,
        70,
    )

    # Detect professional experience duration.
    experience_matches = re.findall(
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
        text,
        flags=re.IGNORECASE,
    )

    if experience_matches:

        try:
            max_years = max(
                float(value)
                for value in experience_matches
            )

            if max_years >= 2:
                score += 30

            elif max_years >= 1:
                score += 20

            elif max_years > 0:
                score += 10

        except ValueError:
            pass

    return round(
        min(score, 100),
        2,
    )


# ============================================================================
# Education Analysis
# ============================================================================

def calculate_education_score(
    resume_text: str,
) -> float:
    """
    Evaluate whether the resume contains a relevant bachelor's degree.
    """

    text = normalize_resume_text(resume_text)

    degree_signals = [
        "bachelor",
        "b.tech",
        "btech",
        "b.e.",
        "b.e",
        "computer science",
        "information technology",
        "software engineering",
    ]

    matches = sum(
        1
        for signal in degree_signals
        if signal in text
    )

    if matches >= 2:
        return 100.0

    if matches == 1:
        return 75.0

    return 0.0


# ============================================================================
# Recommendation
# ============================================================================

def generate_recommendation(
    final_score: float,
    required_skill_score: float,
) -> str:
    """
    Convert the numerical score into a screening recommendation.
    """

    if final_score >= 80 and required_skill_score >= 70:
        return "Strong Match"

    if final_score >= 70 and required_skill_score >= 60:
        return "Good Match"

    if final_score >= 60 and required_skill_score >= 50:
        return "Moderate Match"

    return "Weak Match"


# ============================================================================
# Candidate Scoring Engine
# ============================================================================

class CandidateScorer:
    """
    Explainable candidate scoring engine.

    Combines NLP similarity with rule-based skill and experience analysis.
    """

    def score_candidate(
        self,
        match_result: MatchResult,
        resume_text: str,
    ) -> CandidateScore:
        """
        Generate a final score for one candidate.
        """

        if not resume_text.strip():
            raise ScoringError(
                f"Empty resume content: {match_result.candidate_name}"
            )

        required = evaluate_skills(
            resume_text,
            REQUIRED_SKILLS,
        )

        preferred = evaluate_skills(
            resume_text,
            PREFERRED_SKILLS,
        )

        experience_score = calculate_experience_score(
            resume_text
        )

        education_score = calculate_education_score(
            resume_text
        )

        semantic_score = match_result.relevance_score

        final_score = (
            semantic_score * SEMANTIC_WEIGHT
            + required.score * REQUIRED_SKILLS_WEIGHT
            + preferred.score * PREFERRED_SKILLS_WEIGHT
            + experience_score * EXPERIENCE_WEIGHT
            + education_score * EDUCATION_WEIGHT
        )

        final_score = round(
            min(max(final_score, 0), 100),
            2,
        )

        recommendation = generate_recommendation(
            final_score,
            required.score,
        )

        return CandidateScore(
            candidate_name=match_result.candidate_name,
            semantic_score=semantic_score,
            required_skill_score=required.score,
            preferred_skill_score=preferred.score,
            experience_score=experience_score,
            education_score=education_score,
            final_score=final_score,
            required_skills=required,
            preferred_skills=preferred,
            recommendation=recommendation,
        )


# ============================================================================
# Batch Scoring
# ============================================================================

def score_candidates(
    match_results: Sequence[MatchResult],
    resumes: Sequence,
) -> list[CandidateScore]:
    """
    Score all matched candidates.

    Args:
        match_results:
            NLP matching results.

        resumes:
            Parsed resume documents.

    Returns:
        CandidateScore objects sorted by final score.
    """

    resume_lookup = {
        resume.filename: resume.text
        for resume in resumes
    }

    scorer = CandidateScorer()

    scored_candidates: list[CandidateScore] = []

    for result in match_results:

        resume_text = resume_lookup.get(
            result.candidate_name
        )

        if resume_text is None:
            logger.warning(
                "Resume text not found for %s",
                result.candidate_name,
            )
            continue

        try:
            score = scorer.score_candidate(
                match_result=result,
                resume_text=resume_text,
            )

            scored_candidates.append(score)

        except ScoringError as exc:
            logger.error(
                "Scoring failed for %s: %s",
                result.candidate_name,
                exc,
            )

    return sorted(
        scored_candidates,
        key=lambda candidate: candidate.final_score,
        reverse=True,
    )


# ============================================================================
# Display Utility
# ============================================================================

def display_results(
    results: Sequence[CandidateScore],
) -> None:
    """
    Display professional candidate ranking.
    """

    print("\n" + "=" * 90)
    print("🏆 FINAL CANDIDATE SCREENING RESULTS")
    print("=" * 90)

    print(
        f"{'Rank':<6}"
        f"{'Candidate':<25}"
        f"{'Semantic':>12}"
        f"{'Required':>12}"
        f"{'Preferred':>12}"
        f"{'Final':>12}"
    )

    print("-" * 90)

    for rank, result in enumerate(results, start=1):

        print(
            f"{rank:<6}"
            f"{result.candidate_name:<25}"
            f"{result.semantic_score:>10.2f}%"
            f"{result.required_skill_score:>10.2f}%"
            f"{result.preferred_skill_score:>10.2f}%"
            f"{result.final_score:>10.2f}%"
        )

    print("=" * 90)

    print("\n📋 Candidate Recommendations")

    for rank, result in enumerate(results, start=1):

        print(
            f"\n{rank}. {result.candidate_name}"
        )

        print(
            f"   Final Score : {result.final_score:.2f}%"
        )

        print(
            f"   Decision    : {result.recommendation}"
        )

        print(
            f"   Required    : "
            f"{result.required_skill_score:.2f}%"
        )

        print(
            f"   Matched     : "
            f"{', '.join(result.required_skills.matched)}"
        )

        if result.required_skills.missing:
            print(
                f"   Missing     : "
                f"{', '.join(result.required_skills.missing)}"
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

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    print("\n" + "=" * 90)
    print("🤖 RESUME SCREENING AGENT")
    print("📊 EXPLAINABLE CANDIDATE SCORING ENGINE")
    print("=" * 90)

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
    # Final scoring
    # ------------------------------------------------------------------------

    final_results = score_candidates(
        match_results=match_results,
        resumes=resumes,
    )

    # ------------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------------

    display_results(final_results)

    print("\n" + "=" * 90)
    print("✅ CANDIDATE SCORING COMPLETED")
    print("=" * 90)