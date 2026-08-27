"""
Resume Screening Agent
======================

Main application controller for the Resume Screening Agent.

Pipeline:
    1. Document Ingestion
    2. NLP Semantic Matching
    3. Candidate Scoring
    4. Candidate Ranking
    5. Report Generation

Run:
    python src/agent.py
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any


# ============================================================================
# PROJECT PATH CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# Make project modules importable when running:
# python src/agent.py
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# ============================================================================
# INTERNAL MODULES
# ============================================================================

from parser import load_job_description, load_resumes
from matcher import get_matcher
from scorer import score_candidates
from ranker import CandidateRanker
from reporter import ScreeningReporter


# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

DATA_DIR = PROJECT_ROOT / "data"

# Sample/input files
JOB_DESCRIPTION_PATH = DATA_DIR / "job_description.pdf"
RESUMES_DIR = DATA_DIR / "resumes"

# Generated reports
OUTPUT_DIR = PROJECT_ROOT / "output"

# Ranking configuration
TOP_K = 5
SCORE_THRESHOLD = 70.0

# Rooman challenge requirement
MIN_REQUIRED_RESUMES = 10


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================================
# RESUME SCREENING AGENT
# ============================================================================


class ResumeScreeningAgent:
    """
    Orchestrates the complete resume screening pipeline.

    The agent coordinates:
        - Resume and JD ingestion
        - NLP semantic matching
        - Candidate scoring
        - Candidate ranking
        - Report generation

    Business logic remains inside the individual modules.
    """

    def __init__(
        self,
        job_description_path: Path = JOB_DESCRIPTION_PATH,
        resumes_dir: Path = RESUMES_DIR,
        output_dir: Path = OUTPUT_DIR,
    ) -> None:
        self.job_description_path = Path(job_description_path)
        self.resumes_dir = Path(resumes_dir)
        self.output_dir = Path(output_dir)

    # ------------------------------------------------------------------------
    # STEP 0 — VALIDATE ENVIRONMENT
    # ------------------------------------------------------------------------

    def validate_environment(self) -> None:
        """Validate required files and directories."""

        logger.info("Validating project environment...")

        if not self.job_description_path.exists():
            raise FileNotFoundError(
                f"Job Description not found:\n"
                f"  {self.job_description_path}"
            )

        if not self.job_description_path.is_file():
            raise ValueError(
                f"Job Description path is not a file:\n"
                f"  {self.job_description_path}"
            )

        if not self.resumes_dir.exists():
            raise FileNotFoundError(
                f"Resume directory not found:\n"
                f"  {self.resumes_dir}"
            )

        if not self.resumes_dir.is_dir():
            raise ValueError(
                f"Resume path is not a directory:\n"
                f"  {self.resumes_dir}"
            )

        # Create output directory automatically.
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        logger.info("Environment validation completed.")


    # ------------------------------------------------------------------------
    # STEP 1 — DOCUMENT INGESTION
    # ------------------------------------------------------------------------

    def ingest_documents(self) -> tuple[Any, list[Any]]:
        """
        Load the job description and candidate resumes.

        Returns:
            tuple:
                job_description
                resumes
        """

        logger.info("STEP 1/5 | Document Ingestion")

        # Load Job Description
        job_description = load_job_description(
            str(self.job_description_path)
        )

        # Load Resumes
        resumes = load_resumes(
            str(self.resumes_dir)
        )

        if not resumes:
            raise RuntimeError(
                "No readable resumes were found."
            )

        # Rooman challenge expects 10+ resumes.
        if len(resumes) < MIN_REQUIRED_RESUMES:
            logger.warning(
                "Only %d resume(s) found. "
                "The challenge requires demonstrating 10+ resumes.",
                len(resumes),
            )

        logger.info(
            "Loaded %d resume(s) successfully.",
            len(resumes),
        )

        return job_description, resumes


    # ------------------------------------------------------------------------
    # STEP 2 — NLP SEMANTIC MATCHING
    # ------------------------------------------------------------------------

    def perform_matching(
        self,
        job_description: Any,
        resumes: list[Any],
    ) -> list[Any]:
        """
        Calculate semantic similarity between the JD and resumes.
        """

        logger.info("STEP 2/5 | NLP Semantic Matching")

        matcher = get_matcher()

        match_results = matcher.match_batch(
            job_description=job_description.text,
            resumes=resumes,
        )

        if not match_results:
            raise RuntimeError(
                "No semantic matching results were generated."
            )

        logger.info(
            "Generated %d semantic match result(s).",
            len(match_results),
        )

        return match_results


    # ------------------------------------------------------------------------
    # STEP 3 — CANDIDATE SCORING
    # ------------------------------------------------------------------------

    def perform_scoring(
        self,
        match_results: list[Any],
        resumes: list[Any],
    ) -> list[Any]:
        """
        Generate explainable candidate scores.
        """

        logger.info("STEP 3/5 | Candidate Scoring")

        scored_candidates = score_candidates(
            match_results=match_results,
            resumes=resumes,
        )

        if not scored_candidates:
            raise RuntimeError(
                "No candidates were successfully scored."
            )

        logger.info(
            "Scored %d candidate(s).",
            len(scored_candidates),
        )

        return scored_candidates


    # ------------------------------------------------------------------------
    # STEP 4 — CANDIDATE RANKING
    # ------------------------------------------------------------------------

    def perform_ranking(
        self,
        scored_candidates: list[Any],
    ) -> tuple[Any, list[Any], list[Any], Any]:
        """
        Rank candidates and select the top candidates.
        """

        logger.info("STEP 4/5 | Candidate Ranking")

        ranker = CandidateRanker(
            top_k=TOP_K,
            score_threshold=SCORE_THRESHOLD,
        )

        # Rank every candidate.
        ranked_candidates = ranker.rank(
            scored_candidates
        )

        if not ranked_candidates:
            raise RuntimeError(
                "Candidate ranking returned no results."
            )

        # Select candidates above the configured threshold.
        top_candidates = ranker.select_top_candidates(
            ranked_candidates
        )

        # Generate summary statistics.
        summary = ranker.create_summary(
            ranked_candidates=ranked_candidates,
            selected_candidates=top_candidates,
        )

        logger.info(
            "Ranked %d candidate(s).",
            len(ranked_candidates),
        )

        logger.info(
            "Selected %d candidate(s) for shortlist.",
            len(top_candidates),
        )

        return (
            ranker,
            ranked_candidates,
            top_candidates,
            summary,
        )


    # ------------------------------------------------------------------------
    # STEP 5 — REPORT GENERATION
    # ------------------------------------------------------------------------

    def generate_reports(
        self,
        ranked_candidates: list[Any],
        summary: Any,
    ) -> dict[str, Any]:
        """
        Generate CSV, JSON and TXT screening reports.
        """

        logger.info("STEP 5/5 | Report Generation")

        reporter = ScreeningReporter(
            output_dir=self.output_dir
        )

        report_files = reporter.export_all(
            ranked_candidates=ranked_candidates,
            summary=summary,
        )

        logger.info(
            "Generated %d report file(s).",
            len(report_files),
        )

        return report_files


    # ------------------------------------------------------------------------
    # DISPLAY FINAL RESULTS
    # ------------------------------------------------------------------------

    @staticmethod
    def display_final_results(
        ranked_candidates: list[Any],
        top_candidates: list[Any],
        summary: Any,
        report_files: dict[str, Any],
    ) -> None:
        """Display screening results in the terminal."""

        print("\n" + "=" * 100)
        print("🤖 RESUME SCREENING AGENT")
        print("=" * 100)

        print("\n🏆 FINAL RANKING")
        print("-" * 100)

        print(
            f"{'Rank':<7}"
            f"{'Candidate':<30}"
            f"{'Score':>12}"
            f"{'Decision':>30}"
        )

        print("-" * 100)

        for candidate in ranked_candidates:
            print(
                f"{candidate.rank:<7}"
                f"{candidate.candidate_name:<30}"
                f"{candidate.final_score:>10.2f}%"
                f"{candidate.recommendation:>30}"
            )

        print("-" * 100)

        # ------------------------------------------------------------
        # SHORTLIST
        # ------------------------------------------------------------

        print("\n⭐ SHORTLIST")
        print("-" * 100)

        if top_candidates:
            for candidate in top_candidates:
                print(
                    f"#{candidate.rank} "
                    f"{candidate.candidate_name} "
                    f"→ {candidate.final_score:.2f}% "
                    f"({candidate.recommendation})"
                )
        else:
            print("No candidates met the shortlist criteria.")

        # ------------------------------------------------------------
        # SUMMARY
        # ------------------------------------------------------------

        print("\n📊 SCREENING SUMMARY")
        print("-" * 100)

        print(
            f"Total Candidates : {summary.total_candidates}"
        )

        print(
            f"Shortlisted      : {summary.selected_candidates}"
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

        # ------------------------------------------------------------
        # REPORT FILES
        # ------------------------------------------------------------

        print("\n📁 GENERATED REPORTS")
        print("-" * 100)

        for report_type, path in report_files.items():
            print(
                f"{report_type.upper():<12}: {path}"
            )

        print("=" * 100)


    # ------------------------------------------------------------------------
    # COMPLETE PIPELINE
    # ------------------------------------------------------------------------

    def run(self) -> dict[str, Any]:
        """
        Execute the complete end-to-end screening pipeline.

        Returns:
            Dictionary containing:
                - status
                - total_candidates
                - ranked_candidates
                - shortlisted_candidates
                - summary
                - reports
                - processing_time
        """

        start_time = time.perf_counter()

        print("\n" + "=" * 100)
        print("🤖 RESUME SCREENING AGENT")
        print("🚀 END-TO-END SCREENING PIPELINE")
        print("=" * 100)

        try:
            # --------------------------------------------------------
            # Environment validation
            # --------------------------------------------------------

            self.validate_environment()

            # --------------------------------------------------------
            # Step 1 — Document ingestion
            # --------------------------------------------------------

            job_description, resumes = (
                self.ingest_documents()
            )

            # --------------------------------------------------------
            # Step 2 — NLP matching
            # --------------------------------------------------------

            match_results = self.perform_matching(
                job_description=job_description,
                resumes=resumes,
            )

            # --------------------------------------------------------
            # Step 3 — Candidate scoring
            # --------------------------------------------------------

            scored_candidates = self.perform_scoring(
                match_results=match_results,
                resumes=resumes,
            )

            # --------------------------------------------------------
            # Step 4 — Candidate ranking
            # --------------------------------------------------------

            (
                _ranker,
                ranked_candidates,
                top_candidates,
                summary,
            ) = self.perform_ranking(
                scored_candidates=scored_candidates,
            )

            # --------------------------------------------------------
            # Step 5 — Report generation
            # --------------------------------------------------------

            report_files = self.generate_reports(
                ranked_candidates=ranked_candidates,
                summary=summary,
            )

            # --------------------------------------------------------
            # Display results
            # --------------------------------------------------------

            self.display_final_results(
                ranked_candidates=ranked_candidates,
                top_candidates=top_candidates,
                summary=summary,
                report_files=report_files,
            )

            # --------------------------------------------------------
            # Processing time
            # --------------------------------------------------------

            elapsed_time = (
                time.perf_counter() - start_time
            )

            print("\n" + "=" * 100)
            print(
                f"⏱️ Processing Time: "
                f"{elapsed_time:.2f} seconds"
            )
            print(
                "✅ RESUME SCREENING COMPLETED SUCCESSFULLY"
            )
            print("=" * 100)

            return {
                "status": "success",
                "total_candidates": len(resumes),
                "ranked_candidates": ranked_candidates,
                "shortlisted_candidates": top_candidates,
                "summary": summary,
                "reports": report_files,
                "processing_time": elapsed_time,
            }

        except Exception as exc:
            elapsed_time = (
                time.perf_counter() - start_time
            )

            logger.exception(
                "Resume screening pipeline failed."
            )

            print("\n" + "=" * 100)
            print("❌ SCREENING PIPELINE FAILED")
            print("=" * 100)
            print(f"Error: {exc}")
            print(
                f"Processing Time: "
                f"{elapsed_time:.2f} seconds"
            )
            print("=" * 100)

            # Re-raise the error so that:
            # - CLI exits with failure
            # - automated systems can detect failure
            # - debugging remains straightforward
            raise


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================


def main() -> None:
    """Application entry point."""

    agent = ResumeScreeningAgent()
    agent.run()


if __name__ == "__main__":
    main()