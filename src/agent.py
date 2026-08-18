"""
Resume Screening Agent
======================

Main Application Controller

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

# ============================================================================
# Project Path Configuration
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# Internal Modules
# ============================================================================

from parser import load_job_description, load_resumes
from matcher import get_matcher
from scorer import score_candidates
from ranker import CandidateRanker
from reporter import ScreeningReporter


# ============================================================================
# Configuration
# ============================================================================

DATA_DIR = PROJECT_ROOT / "data"
RESUMES_DIR = DATA_DIR / "resumes"
JOB_DESCRIPTION_PATH = DATA_DIR / "job_description.txt"
OUTPUT_DIR = PROJECT_ROOT / "output"

TOP_K = 5
SCORE_THRESHOLD = 70.0


# ============================================================================
# Logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================================
# Application
# ============================================================================

class ResumeScreeningAgent:
    """
    Main orchestration layer for the Resume Screening Agent.

    This class coordinates all components without implementing their
    internal business logic.
    """

    def __init__(
        self,
        job_description_path: Path = JOB_DESCRIPTION_PATH,
        resumes_dir: Path = RESUMES_DIR,
        output_dir: Path = OUTPUT_DIR,
    ) -> None:

        self.job_description_path = job_description_path
        self.resumes_dir = resumes_dir
        self.output_dir = output_dir

    # ------------------------------------------------------------------------
    # Validate Environment
    # ------------------------------------------------------------------------

    def validate_environment(self) -> None:
        """
        Validate required project files and directories.
        """

        if not self.job_description_path.exists():
            raise FileNotFoundError(
                f"Job Description not found: "
                f"{self.job_description_path}"
            )

        if not self.resumes_dir.exists():
            raise FileNotFoundError(
                f"Resume directory not found: "
                f"{self.resumes_dir}"
            )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ------------------------------------------------------------------------
    # Step 1 — Document Ingestion
    # ------------------------------------------------------------------------

    def ingest_documents(self):
        """
        Load Job Description and candidate resumes.
        """

        logger.info(
            "STEP 1/5 | Document Ingestion"
        )

        job_description = load_job_description(
            str(self.job_description_path)
        )

        resumes = load_resumes(
            str(self.resumes_dir)
        )

        if not resumes:
            raise RuntimeError(
                "No readable resumes were found."
            )

        logger.info(
            "Loaded %d resumes successfully.",
            len(resumes),
        )

        return job_description, resumes

    # ------------------------------------------------------------------------
    # Step 2 — NLP Matching
    # ------------------------------------------------------------------------

    def perform_matching(
        self,
        job_description,
        resumes,
    ):
        """
        Generate semantic similarity scores.
        """

        logger.info(
            "STEP 2/5 | NLP Semantic Matching"
        )

        matcher = get_matcher()

        match_results = matcher.match_batch(
            job_description=job_description.text,
            resumes=resumes,
        )

        logger.info(
            "Generated %d semantic match results.",
            len(match_results),
        )

        return match_results

    # ------------------------------------------------------------------------
    # Step 3 — Candidate Scoring
    # ------------------------------------------------------------------------

    def perform_scoring(
        self,
        match_results,
        resumes,
    ):
        """
        Generate explainable candidate scores.
        """

        logger.info(
            "STEP 3/5 | Candidate Scoring"
        )

        scored_candidates = score_candidates(
            match_results=match_results,
            resumes=resumes,
        )

        logger.info(
            "Scored %d candidates.",
            len(scored_candidates),
        )

        return scored_candidates

    # ------------------------------------------------------------------------
    # Step 4 — Candidate Ranking
    # ------------------------------------------------------------------------

    def perform_ranking(
        self,
        scored_candidates,
    ):
        """
        Rank candidates and select Top-K.
        """

        logger.info(
            "STEP 4/5 | Candidate Ranking"
        )

        ranker = CandidateRanker(
            top_k=TOP_K,
            score_threshold=SCORE_THRESHOLD,
        )

        ranked_candidates = ranker.rank(
            scored_candidates
        )

        top_candidates = ranker.select_top_candidates(
            ranked_candidates
        )

        summary = ranker.create_summary(
            ranked_candidates=ranked_candidates,
            selected_candidates=top_candidates,
        )

        logger.info(
            "Top %d candidates selected.",
            len(top_candidates),
        )

        return (
            ranker,
            ranked_candidates,
            top_candidates,
            summary,
        )

    # ------------------------------------------------------------------------
    # Step 5 — Report Generation
    # ------------------------------------------------------------------------

    def generate_reports(
        self,
        ranked_candidates,
        summary,
    ):
        """
        Generate JSON, CSV, and TXT reports.
        """

        logger.info(
            "STEP 5/5 | Report Generation"
        )

        reporter = ScreeningReporter(
            output_dir=self.output_dir
        )

        report_files = reporter.export_all(
            ranked_candidates=ranked_candidates,
            summary=summary,
        )

        return report_files

    # ------------------------------------------------------------------------
    # Display Final Results
    # ------------------------------------------------------------------------

    @staticmethod
    def display_final_results(
        ranked_candidates,
        top_candidates,
        summary,
        report_files,
    ) -> None:
        """
        Display final screening results.
        """

        print("\n" + "=" * 100)
        print("🏆 FINAL RESUME SCREENING RESULTS")
        print("=" * 100)

        print(
            f"{'Rank':<7}"
            f"{'Candidate':<25}"
            f"{'Score':>12}"
            f"{'Decision':>25}"
        )

        print("-" * 100)

        for candidate in ranked_candidates:

            print(
                f"{candidate.rank:<7}"
                f"{candidate.candidate_name:<25}"
                f"{candidate.final_score:>10.2f}%"
                f"{candidate.recommendation:>25}"
            )

        print("=" * 100)

        print("\n⭐ SHORTLIST")

        for candidate in top_candidates:

            print(
                f"#{candidate.rank} "
                f"{candidate.candidate_name} "
                f"→ {candidate.final_score:.2f}% "
                f"({candidate.recommendation})"
            )

        print("\n📊 SCREENING SUMMARY")

        print(
            f"Total Candidates : "
            f"{summary.total_candidates}"
        )

        print(
            f"Shortlisted      : "
            f"{summary.selected_candidates}"
        )

        print(
            f"Average Score    : "
            f"{summary.average_score:.2f}%"
        )

        print(
            f"Highest Score    : "
            f"{summary.highest_score:.2f}%"
        )

        print(
            f"Lowest Score     : "
            f"{summary.lowest_score:.2f}%"
        )

        print("\n📁 REPORT FILES")

        for report_type, path in report_files.items():

            print(
                f"{report_type.upper():<10}: "
                f"{path}"
            )

    # ------------------------------------------------------------------------
    # Run Complete Pipeline
    # ------------------------------------------------------------------------

    def run(self) -> dict:
        """
        Execute the complete resume screening pipeline.
        """

        start_time = time.perf_counter()

        print("\n" + "=" * 100)
        print("🤖 RESUME SCREENING AGENT")
        print("🚀 END-TO-END SCREENING PIPELINE")
        print("=" * 100)

        try:

            # Environment validation.
            self.validate_environment()

            # Step 1.
            job_description, resumes = (
                self.ingest_documents()
            )

            # Step 2.
            match_results = self.perform_matching(
                job_description,
                resumes,
            )

            # Step 3.
            scored_candidates = self.perform_scoring(
                match_results,
                resumes,
            )

            # Step 4.
            (
                ranker,
                ranked_candidates,
                top_candidates,
                summary,
            ) = self.perform_ranking(
                scored_candidates
            )

            # Step 5.
            report_files = self.generate_reports(
                ranked_candidates,
                summary,
            )

            # Display.
            self.display_final_results(
                ranked_candidates=ranked_candidates,
                top_candidates=top_candidates,
                summary=summary,
                report_files=report_files,
            )

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
                "total_candidates": (
                    len(resumes)
                ),
                "ranked_candidates": (
                    ranked_candidates
                ),
                "shortlisted_candidates": (
                    top_candidates
                ),
                "summary": summary,
                "reports": report_files,
                "processing_time": elapsed_time,
            }

        except Exception as exc:

            logger.exception(
                "Resume screening pipeline failed."
            )

            print("\n" + "=" * 100)
            print("❌ SCREENING PIPELINE FAILED")
            print("=" * 100)
            print(f"Error: {exc}")

            raise


# ============================================================================
# Application Entry Point
# ============================================================================

def main() -> None:
    """
    Application entry point.
    """

    agent = ResumeScreeningAgent()

    agent.run()


if __name__ == "__main__":
    main()