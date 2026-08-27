"""
Resume Screening Agent
======================

Candidate Scoring Engine

Converts NLP matching results into an explainable candidate score.

Scoring:
    Semantic Similarity   : 40%
    Required Skills       : 35%
    Preferred Skills      : 10%
    Experience            : 10%
    Education             : 5%

The scoring layer is kept separate from the NLP matcher so that
the scoring logic remains transparent and easy to modify.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Sequence

from matcher import MatchResult


# ============================================================================
# LOGGING
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# SCORING CONFIGURATION
# ============================================================================

SEMANTIC_WEIGHT = 0.40
REQUIRED_SKILLS_WEIGHT = 0.35
PREFERRED_SKILLS_WEIGHT = 0.10
EXPERIENCE_WEIGHT = 0.10
EDUCATION_WEIGHT = 0.05


# ============================================================================
# REQUIRED SKILLS
# ============================================================================

REQUIRED_SKILLS: dict[str, list[str]] = {
    "Python": [
        r"\bpython\b",
    ],
    "Backend Framework": [
        r"\bflask\b",
        r"\bfastapi\b",
    ],
    "REST API": [
        r"\brestful api\b",
        r"\brest api\b",
        r"\brest apis\b",
        r"\bapi development\b",
    ],
    "SQL": [
        r"\bsql\b",
    ],
    "Relational Database": [
        r"\bmysql\b",
        r"\bpostgresql\b",
        r"\bpostgres\b",
    ],
    "Git": [
        r"\bgit\b",
        r"\bgithub\b",
    ],
    "Object-Oriented Programming": [
        r"\bobject[- ]oriented programming\b",
        r"\boop\b",
    ],
    "Data Structures & Algorithms": [
        r"\bdata structures\b",
        r"\bdata structures and algorithms\b",
        r"\balgorithms\b",
    ],
    "Exception Handling": [
        r"\bexception handling\b",
        r"\berror handling\b",
    ],
    "JWT Authentication": [
        r"\bjwt\b",
        r"\bjson web token\b",
    ],
}


# ============================================================================
# PREFERRED SKILLS
# ============================================================================

PREFERRED_SKILLS: dict[str, list[str]] = {
    "Docker": [
        r"\bdocker\b",
        r"\bcontainerization\b",
    ],
    "Cloud": [
        r"\baws\b",
        r"\bazure\b",
        r"\bgcp\b",
        r"\bcloud\b",
    ],
    "MongoDB": [
        r"\bmongodb\b",
        r"\bmongo\b",
    ],
    "Redis": [
        r"\bredis\b",
        r"\bcaching\b",
    ],
    "Celery": [
        r"\bcelery\b",
        r"\bbackground task\b",
    ],
    "CI/CD": [
        r"\bci/cd\b",
        r"\bci cd\b",
        r"\bcontinuous integration\b",
        r"\bcontinuous deployment\b",
    ],
    "Linux": [
        r"\blinux\b",
    ],
    "Pytest": [
        r"\bpytest\b",
        r"\bunit testing\b",
        r"\bautomated testing\b",
    ],
}


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass(frozen=True)
class SkillResult:
    """Stores skill matching information for one candidate."""

    matched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    score: float = 0.0


@dataclass(frozen=True)
class CandidateScore:
    """
    Final explainable score for one candidate.

    Scores are represented as percentages from 0 to 100.
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

    # Human-readable explanation for the ranking.
    reason: str = ""


# ============================================================================
# EXCEPTIONS
# ============================================================================

class ScoringError(Exception):
    """Raised when candidate scoring fails."""


# ============================================================================
# TEXT UTILITIES
# ============================================================================

def normalize_text(text: str) -> str:
    """
    Normalize resume text for consistent skill matching.
    """

    if not isinstance(text, str):
        raise TypeError("Resume text must be a string.")

    return re.sub(
        r"\s+",
        " ",
        text.lower(),
    ).strip()


def contains_pattern(
    text: str,
    patterns: Sequence[str],
) -> bool:
    """
    Return True when at least one pattern matches the text.
    """

    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )


# ============================================================================
# SKILL ANALYSIS
# ============================================================================

def evaluate_skills(
    resume_text: str,
    skill_definitions: dict[str, list[str]],
) -> SkillResult:
    """
    Match a resume against a skill dictionary.

    Each skill category contributes equally to the skill score.
    """

    text = normalize_text(resume_text)

    matched: list[str] = []
    missing: list[str] = []

    for skill_name, patterns in skill_definitions.items():

        if contains_pattern(text, patterns):
            matched.append(skill_name)
        else:
            missing.append(skill_name)

    total_skills = len(skill_definitions)

    score = (
        (len(matched) / total_skills) * 100
        if total_skills
        else 0.0
    )

    return SkillResult(
        matched=matched,
        missing=missing,
        score=round(score, 2),
    )


# ============================================================================
# EXPERIENCE ANALYSIS
# ============================================================================

def calculate_experience_score(
    resume_text: str,
) -> float:
    """
    Estimate experience relevance.

    Signals considered:
        - Backend development
        - Python development
        - Software development
        - REST API development
        - Relevant years of experience
    """

    text = normalize_text(resume_text)

    score = 0.0

    role_signals = [
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

    matched_signals = sum(
        1
        for signal in role_signals
        if signal in text
    )

    # Maximum 70 points for role relevance.
    score += min(
        matched_signals * 10,
        70,
    )

    # Detect experience such as:
    # "2 years experience"
    # "1.5 years"
    # "3 yrs"
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
            logger.warning(
                "Unable to parse experience duration."
            )

    return round(
        min(score, 100),
        2,
    )


# ============================================================================
# EDUCATION ANALYSIS
# ============================================================================

def calculate_education_score(
    resume_text: str,
) -> float:
    """
    Estimate education relevance.

    Strong signals include:
        - Bachelor's degree
        - B.Tech / B.E.
        - Computer Science
        - Information Technology
        - Software Engineering
    """

    text = normalize_text(resume_text)

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
# RECOMMENDATION
# ============================================================================

def generate_recommendation(
    final_score: float,
    required_skill_score: float,
) -> str:
    """
    Convert numerical scores into a screening recommendation.
    """

    if (
        final_score >= 80
        and required_skill_score >= 70
    ):
        return "Strong Match"

    if (
        final_score >= 70
        and required_skill_score >= 60
    ):
        return "Good Match"

    if (
        final_score >= 60
        and required_skill_score >= 50
    ):
        return "Moderate Match"

    return "Weak Match"


# ============================================================================
# EXPLAINABLE REASONING
# ============================================================================

def generate_reason(
    required_skills: SkillResult,
    preferred_skills: SkillResult,
    experience_score: float,
    education_score: float,
    semantic_score: float,
    final_score: float,
) -> str:
    """
    Generate a concise human-readable explanation
    for the candidate's score.
    """

    strengths: list[str] = []
    gaps: list[str] = []

    # ------------------------------------------------------------
    # Strengths
    # ------------------------------------------------------------

    if semantic_score >= 75:
        strengths.append("strong semantic alignment with the job description")
    elif semantic_score >= 60:
        strengths.append("good semantic alignment with the job description")

    if required_skills.score >= 70:
        strengths.append("strong coverage of required skills")
    elif required_skills.score >= 50:
        strengths.append("reasonable coverage of required skills")

    if experience_score >= 70:
        strengths.append("relevant development experience")

    if education_score >= 75:
        strengths.append("relevant educational background")

    # ------------------------------------------------------------
    # Gaps
    # ------------------------------------------------------------

    if required_skills.missing:
        gaps.append(
            "missing required skills: "
            + ", ".join(required_skills.missing)
        )

    if preferred_skills.missing:
        gaps.append(
            "missing preferred skills: "
            + ", ".join(preferred_skills.missing)
        )

    # ------------------------------------------------------------
    # Build explanation
    # ------------------------------------------------------------

    if strengths:
        reason = (
            f"Final score is {final_score:.2f}%. "
            f"The candidate shows "
            + "; ".join(strengths)
            + "."
        )
    else:
        reason = (
            f"Final score is {final_score:.2f}%. "
            "The candidate has limited alignment with the role."
        )

    if gaps:
        reason += " Key gaps include " + "; ".join(gaps) + "."

    return reason


# ============================================================================
# CANDIDATE SCORER
# ============================================================================

class CandidateScorer:
    """
    Explainable candidate scoring engine.

    Combines:
        - NLP semantic similarity
        - Required skills
        - Preferred skills
        - Experience
        - Education
    """

    def score_candidate(
        self,
        match_result: MatchResult,
        resume_text: str,
    ) -> CandidateScore:
        """
        Calculate the final score for one candidate.
        """

        if not isinstance(resume_text, str):
            raise ScoringError(
                f"Invalid resume content: "
                f"{match_result.candidate_name}"
            )

        if not resume_text.strip():
            raise ScoringError(
                f"Empty resume content: "
                f"{match_result.candidate_name}"
            )

        # ------------------------------------------------------------
        # Skill analysis
        # ------------------------------------------------------------

        required_skills = evaluate_skills(
            resume_text,
            REQUIRED_SKILLS,
        )

        preferred_skills = evaluate_skills(
            resume_text,
            PREFERRED_SKILLS,
        )

        # ------------------------------------------------------------
        # Experience and education
        # ------------------------------------------------------------

        experience_score = calculate_experience_score(
            resume_text
        )

        education_score = calculate_education_score(
            resume_text
        )

        # ------------------------------------------------------------
        # Semantic similarity
        # ------------------------------------------------------------

        semantic_score = float(
            match_result.relevance_score
        )

        semantic_score = round(
            max(
                0.0,
                min(
                    semantic_score,
                    100.0,
                ),
            ),
            2,
        )

        # ------------------------------------------------------------
        # Weighted final score
        # ------------------------------------------------------------

        final_score = (
            semantic_score * SEMANTIC_WEIGHT
            + required_skills.score * REQUIRED_SKILLS_WEIGHT
            + preferred_skills.score * PREFERRED_SKILLS_WEIGHT
            + experience_score * EXPERIENCE_WEIGHT
            + education_score * EDUCATION_WEIGHT
        )

        final_score = round(
            max(
                0.0,
                min(
                    final_score,
                    100.0,
                ),
            ),
            2,
        )

        # ------------------------------------------------------------
        # Recommendation
        # ------------------------------------------------------------

        recommendation = generate_recommendation(
            final_score=final_score,
            required_skill_score=required_skills.score,
        )

        # ------------------------------------------------------------
        # Explanation
        # ------------------------------------------------------------

        reason = generate_reason(
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            experience_score=experience_score,
            education_score=education_score,
            semantic_score=semantic_score,
            final_score=final_score,
        )

        return CandidateScore(
            candidate_name=match_result.candidate_name,
            semantic_score=semantic_score,
            required_skill_score=required_skills.score,
            preferred_skill_score=preferred_skills.score,
            experience_score=experience_score,
            education_score=education_score,
            final_score=final_score,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            recommendation=recommendation,
            reason=reason,
        )


# ============================================================================
# BATCH SCORING
# ============================================================================

def score_candidates(
    match_results: Sequence[MatchResult],
    resumes: Sequence,
) -> list[CandidateScore]:
    """
    Score all candidates and return them sorted by final score.

    Args:
        match_results:
            Semantic matching results.

        resumes:
            Parsed resume documents.

    Returns:
        Candidates sorted from highest to lowest score.
    """

    if not match_results:
        logger.warning(
            "No matching results were provided."
        )
        return []

    if not resumes:
        logger.warning(
            "No resumes were provided."
        )
        return []

    # Create quick lookup:
    # resume filename → resume text
    resume_lookup = {
        resume.filename: resume.text
        for resume in resumes
        if getattr(resume, "filename", None)
    }

    scorer = CandidateScorer()

    scored_candidates: list[CandidateScore] = []

    for match_result in match_results:

        candidate_name = match_result.candidate_name

        resume_text = resume_lookup.get(
            candidate_name
        )

        if resume_text is None:
            logger.warning(
                "Resume text not found for: %s",
                candidate_name,
            )
            continue

        try:

            result = scorer.score_candidate(
                match_result=match_result,
                resume_text=resume_text,
            )

            scored_candidates.append(result)

        except ScoringError as exc:

            logger.error(
                "Scoring failed for %s: %s",
                candidate_name,
                exc,
            )

    # Highest score first.
    scored_candidates.sort(
        key=lambda candidate: (
            candidate.final_score,
            candidate.semantic_score,
        ),
        reverse=True,
    )

    return scored_candidates


# ============================================================================
# TERMINAL DISPLAY
# ============================================================================

def display_results(
    results: Sequence[CandidateScore],
) -> None:
    """
    Display candidate ranking in the terminal.
    """

    print("\n" + "=" * 105)
    print("🏆 FINAL CANDIDATE SCREENING RESULTS")
    print("=" * 105)

    if not results:
        print("No candidates were successfully scored.")
        print("=" * 105)
        return

    print(
        f"{'Rank':<6}"
        f"{'Candidate':<28}"
        f"{'Semantic':>12}"
        f"{'Required':>12}"
        f"{'Preferred':>12}"
        f"{'Final':>12}"
    )

    print("-" * 105)

    for rank, result in enumerate(
        results,
        start=1,
    ):
        print(
            f"{rank:<6}"
            f"{result.candidate_name:<28}"
            f"{result.semantic_score:>10.2f}%"
            f"{result.required_skill_score:>10.2f}%"
            f"{result.preferred_skill_score:>10.2f}%"
            f"{result.final_score:>10.2f}%"
        )

    print("=" * 105)

    print("\n📋 CANDIDATE RECOMMENDATIONS")
    print("-" * 105)

    for rank, result in enumerate(
        results,
        start=1,
    ):

        print(
            f"\n{rank}. {result.candidate_name}"
        )

        print(
            f"   Final Score : "
            f"{result.final_score:.2f}%"
        )

        print(
            f"   Decision    : "
            f"{result.recommendation}"
        )

        print(
            f"   Semantic    : "
            f"{result.semantic_score:.2f}%"
        )

        print(
            f"   Required    : "
            f"{result.required_skill_score:.2f}%"
        )

        if result.required_skills.matched:
            print(
                "   Matched     : "
                + ", ".join(
                    result.required_skills.matched
                )
            )

        if result.required_skills.missing:
            print(
                "   Missing     : "
                + ", ".join(
                    result.required_skills.missing
                )
            )

        print(
            f"   Reason      : "
            f"{result.reason}"
        )


# ============================================================================
# LOCAL TEST
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

    print("\n" + "=" * 105)
    print("🤖 RESUME SCREENING AGENT")
    print("📊 EXPLAINABLE CANDIDATE SCORING ENGINE")
    print("=" * 105)

    # ------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------

    job_description_path = "data/job_description.pdf"
    resumes_path = "data/resumes"

    # ------------------------------------------------------------
    # Load documents
    # ------------------------------------------------------------

    job_description = load_job_description(
        job_description_path
    )

    resumes = load_resumes(
        resumes_path
    )

    print(
        f"\n📄 Resumes loaded: {len(resumes)}"
    )

    if len(resumes) < 10:
        print(
            "⚠️ Warning: fewer than 10 resumes "
            "were loaded."
        )

    # ------------------------------------------------------------
    # NLP matching
    # ------------------------------------------------------------

    matcher = get_matcher()

    match_results = matcher.match_batch(
        job_description=job_description.text,
        resumes=resumes,
    )

    # ------------------------------------------------------------
    # Candidate scoring
    # ------------------------------------------------------------

    final_results = score_candidates(
        match_results=match_results,
        resumes=resumes,
    )

    # ------------------------------------------------------------
    # Display
    # ------------------------------------------------------------

    display_results(
        final_results
    )

    print("\n" + "=" * 105)
    print("✅ CANDIDATE SCORING COMPLETED")
    print("=" * 105)