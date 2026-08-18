"""
Resume Screening Agent
======================

Candidate Reporting Engine

Responsibilities:
    - Generate a professional screening report.
    - Export results to JSON.
    - Export results to CSV.
    - Save a human-readable TXT report.
    - Include ranking, scores, matched skills, missing skills,
      recommendations, and screening statistics.

This module does NOT perform matching or scoring.
It consumes the output of ranker.py.
"""

from __future__ import annotations

import csv
import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Sequence

from ranker import RankedCandidate, RankingSummary


# ============================================================================
# Logging
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

DEFAULT_OUTPUT_DIR = Path("output")


# ============================================================================
# Reporter
# ============================================================================

class ScreeningReporter:
    """
    Generates and exports professional resume screening reports.
    """

    def __init__(
        self,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        logger.info(
            "Report output directory: %s",
            self.output_dir.resolve(),
        )

    # ------------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------------

    @staticmethod
    def _report_metadata() -> dict:
        """
        Generate report metadata.
        """

        return {
            "report_title": "Resume Screening Report",
            "generated_at": datetime.now().isoformat(
                timespec="seconds"
            ),
            "system": "Resume Screening Agent",
        }

    # ------------------------------------------------------------------------
    # JSON Report
    # ------------------------------------------------------------------------

    def export_json(
        self,
        ranked_candidates: Sequence[RankedCandidate],
        summary: RankingSummary,
        filename: str = "screening_report.json",
    ) -> Path:
        """
        Export complete screening results as JSON.
        """

        report = {
            "metadata": self._report_metadata(),

            "summary": asdict(summary),

            "candidates": [
                asdict(candidate)
                for candidate in ranked_candidates
            ],
        }

        output_path = self.output_dir / filename

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                report,
                file,
                indent=4,
                ensure_ascii=False,
            )

        logger.info(
            "JSON report created: %s",
            output_path,
        )

        return output_path

    # ------------------------------------------------------------------------
    # CSV Report
    # ------------------------------------------------------------------------

    def export_csv(
        self,
        ranked_candidates: Sequence[RankedCandidate],
        filename: str = "candidate_ranking.csv",
    ) -> Path:
        """
        Export candidate ranking to CSV.
        """

        output_path = self.output_dir / filename

        fieldnames = [
            "rank",
            "candidate_name",
            "final_score",
            "recommendation",
            "semantic_score",
            "required_skill_score",
            "preferred_skill_score",
            "experience_score",
            "education_score",
            "matched_skills",
            "missing_skills",
        ]

        with output_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
            )

            writer.writeheader()

            for candidate in ranked_candidates:

                writer.writerow(
                    {
                        "rank": candidate.rank,
                        "candidate_name": (
                            candidate.candidate_name
                        ),
                        "final_score": (
                            candidate.final_score
                        ),
                        "recommendation": (
                            candidate.recommendation
                        ),
                        "semantic_score": (
                            candidate.semantic_score
                        ),
                        "required_skill_score": (
                            candidate.required_skill_score
                        ),
                        "preferred_skill_score": (
                            candidate.preferred_skill_score
                        ),
                        "experience_score": (
                            candidate.experience_score
                        ),
                        "education_score": (
                            candidate.education_score
                        ),
                        "matched_skills": (
                            ", ".join(
                                candidate.matched_skills
                            )
                        ),
                        "missing_skills": (
                            ", ".join(
                                candidate.missing_skills
                            )
                        ),
                    }
                )

        logger.info(
            "CSV report created: %s",
            output_path,
        )

        return output_path

    # ------------------------------------------------------------------------
    # Human-Readable TXT Report
    # ------------------------------------------------------------------------

    def export_text(
        self,
        ranked_candidates: Sequence[RankedCandidate],
        summary: RankingSummary,
        filename: str = "screening_report.txt",
    ) -> Path:
        """
        Generate a human-readable screening report.
        """

        output_path = self.output_dir / filename

        lines: list[str] = []

        separator = "=" * 90

        lines.append(separator)
        lines.append(
            "RESUME SCREENING AGENT"
        )
        lines.append(
            "PROFESSIONAL CANDIDATE SCREENING REPORT"
        )
        lines.append(separator)

        lines.append("")

        lines.append(
            f"Generated At     : "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        lines.append(
            f"Total Candidates : "
            f"{summary.total_candidates}"
        )

        lines.append(
            f"Shortlisted      : "
            f"{summary.selected_candidates}"
        )

        lines.append(
            f"Average Score    : "
            f"{summary.average_score:.2f}%"
        )

        lines.append(
            f"Highest Score    : "
            f"{summary.highest_score:.2f}%"
        )

        lines.append(
            f"Lowest Score     : "
            f"{summary.lowest_score:.2f}%"
        )

        lines.append("")

        lines.append(separator)
        lines.append("CANDIDATE RANKING")
        lines.append(separator)

        for candidate in ranked_candidates:

            lines.append("")

            lines.append(
                f"Rank #{candidate.rank} | "
                f"{candidate.candidate_name}"
            )

            lines.append("-" * 70)

            lines.append(
                f"Final Score       : "
                f"{candidate.final_score:.2f}%"
            )

            lines.append(
                f"Recommendation     : "
                f"{candidate.recommendation}"
            )

            lines.append(
                f"Semantic Score     : "
                f"{candidate.semantic_score:.2f}%"
            )

            lines.append(
                f"Required Skills    : "
                f"{candidate.required_skill_score:.2f}%"
            )

            lines.append(
                f"Preferred Skills   : "
                f"{candidate.preferred_skill_score:.2f}%"
            )

            lines.append(
                f"Experience Score   : "
                f"{candidate.experience_score:.2f}%"
            )

            lines.append(
                f"Education Score    : "
                f"{candidate.education_score:.2f}%"
            )

            lines.append(
                "Matched Skills     : "
                + (
                    ", ".join(
                        candidate.matched_skills
                    )
                    if candidate.matched_skills
                    else "None"
                )
            )

            lines.append(
                "Missing Skills     : "
                + (
                    ", ".join(
                        candidate.missing_skills
                    )
                    if candidate.missing_skills
                    else "None"
                )
            )

        lines.append("")
        lines.append(separator)
        lines.append("SCREENING SUMMARY")
        lines.append(separator)

        lines.append(
            f"Strong Matches     : "
            f"{summary.strong_matches}"
        )

        lines.append(
            f"Good Matches       : "
            f"{summary.good_matches}"
        )

        lines.append(
            f"Moderate Matches   : "
            f"{summary.moderate_matches}"
        )

        lines.append(
            f"Weak Matches       : "
            f"{summary.weak_matches}"
        )

        lines.append("")
        lines.append(separator)
        lines.append(
            "END OF SCREENING REPORT"
        )
        lines.append(separator)

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as file:

            file.write(
                "\n".join(lines)
            )

        logger.info(
            "Text report created: %s",
            output_path,
        )

        return output_path

    # ------------------------------------------------------------------------
    # Export All Reports
    # ------------------------------------------------------------------------

    def export_all(
        self,
        ranked_candidates: Sequence[RankedCandidate],
        summary: RankingSummary,
    ) -> dict[str, Path]:
        """
        Generate JSON, CSV, and TXT reports.
        """

        logger.info(
            "Generating complete screening report package..."
        )

        json_path = self.export_json(
            ranked_candidates,
            summary,
        )

        csv_path = self.export_csv(
            ranked_candidates,
        )

        text_path = self.export_text(
            ranked_candidates,
            summary,
        )

        logger.info(
            "All screening reports generated successfully."
        )

        return {
            "json": json_path,
            "csv": csv_path,
            "text": text_path,
        }


# ============================================================================
# Display Report Files
# ============================================================================

def display_report_files(
    report_files: dict[str, Path],
) -> None:
    """
    Display generated report locations.
    """

    print("\n" + "=" * 90)
    print("📁 GENERATED REPORTS")
    print("=" * 90)

    for report_type, path in report_files.items():

        print(
            f"{report_type.upper():<10} : "
            f"{path}"
        )

    print("=" * 90)


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
    from ranker import CandidateRanker

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    print("\n" + "=" * 90)
    print("🤖 RESUME SCREENING AGENT")
    print("📄 PROFESSIONAL REPORTING ENGINE")
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
    # NLP Matching
    # ------------------------------------------------------------------------

    matcher = get_matcher()

    match_results = matcher.match_batch(
        job_description=job_description.text,
        resumes=resumes,
    )

    # ------------------------------------------------------------------------
    # Candidate Scoring
    # ------------------------------------------------------------------------

    scored_candidates = score_candidates(
        match_results=match_results,
        resumes=resumes,
    )

    # ------------------------------------------------------------------------
    # Candidate Ranking
    # ------------------------------------------------------------------------

    ranker = CandidateRanker(
        top_k=5,
        score_threshold=70.0,
    )

    ranked_candidates = ranker.rank(
        scored_candidates
    )

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
    # Generate Reports
    # ------------------------------------------------------------------------

    reporter = ScreeningReporter(
        output_dir="output"
    )

    report_files = reporter.export_all(
        ranked_candidates=ranked_candidates,
        summary=summary,
    )

    # ------------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------------

    display_report_files(
        report_files
    )

    print("\n" + "=" * 90)
    print("✅ REPORT GENERATION COMPLETED")
    print("=" * 90)