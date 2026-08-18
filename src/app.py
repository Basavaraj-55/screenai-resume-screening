"""
ScreenAI - Resume Intelligence Platform
=======================================

Production-oriented Flask API for:
- Health checks
- Job description upload
- Resume upload
- AI resume screening
- Candidate ranking
- Report downloads
- Workspace reset
- Frontend serving

Run:
    python src/app.py
"""

from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_file, send_from_directory
from werkzeug.utils import secure_filename


# =============================================================================
# Project Paths
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# Internal Modules
# =============================================================================

from matcher import get_matcher
from parser import load_job_description, load_resumes
from ranker import CandidateRanker
from reporter import ScreeningReporter
from scorer import score_candidates


# =============================================================================
# Flask Application
# =============================================================================

app = Flask(
    __name__,
    static_folder=None,
)

app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024


# =============================================================================
# Configuration
# =============================================================================

DATA_DIR = PROJECT_ROOT / "data"
RESUMES_DIR = DATA_DIR / "resumes"
ACTIVE_RESUMES_DIR = DATA_DIR / "active_resumes"
OUTPUT_DIR = PROJECT_ROOT / "output"
UPLOAD_DIR = PROJECT_ROOT / "uploads"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

TOP_K = 5
SCORE_THRESHOLD = 70.0

ALLOWED_EXTENSIONS = {"txt", "pdf", "docx"}

# The active JD is stored with its real extension so parser.py can correctly
# select TXT/PDF/DOCX extraction.
ACTIVE_JD_PREFIX = "job_description"


# =============================================================================
# Logging
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)

logger = logging.getLogger("screenai")


# =============================================================================
# Directory Initialization
# =============================================================================

def initialize_directories() -> None:
    """Create all directories required by the application."""
    for directory in (
        DATA_DIR,
        RESUMES_DIR,
        ACTIVE_RESUMES_DIR,
        OUTPUT_DIR,
        UPLOAD_DIR,
        FRONTEND_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)


initialize_directories()


# =============================================================================
# Utility Functions
# =============================================================================

def allowed_file(filename: str) -> bool:
    """Return True when the filename has a supported extension."""
    if not filename or "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS


def get_extension(filename: str) -> str:
    """Return a normalized file extension without the leading dot."""
    return filename.rsplit(".", 1)[1].lower()


def json_error(message: str, status_code: int = 400):
    """Return a consistent JSON API error response."""
    return jsonify(
        {
            "success": False,
            "error": message,
        }
    ), status_code


def candidate_to_dict(candidate) -> dict[str, Any]:
    """Convert a RankedCandidate object into JSON-safe data."""
    return {
        "rank": candidate.rank,
        "candidate_name": candidate.candidate_name,
        "final_score": candidate.final_score,
        "recommendation": candidate.recommendation,
        "semantic_score": candidate.semantic_score,
        "required_skill_score": candidate.required_skill_score,
        "preferred_skill_score": candidate.preferred_skill_score,
        "experience_score": candidate.experience_score,
        "education_score": candidate.education_score,
        "matched_skills": candidate.matched_skills,
        "missing_skills": candidate.missing_skills,
    }


def find_active_job_description() -> Path | None:
    """
    Find the currently active Job Description.

    The application supports TXT, PDF, and DOCX. We deliberately search for
    the active file instead of hard-coding job_description.txt.
    """
    candidates = [
        path
        for path in DATA_DIR.iterdir()
        if path.is_file()
        and path.stem.lower() == ACTIVE_JD_PREFIX
        and path.suffix.lower().lstrip(".") in ALLOWED_EXTENSIONS
    ]

    if not candidates:
        return None

    # Prefer the most recently modified JD.
    return max(candidates, key=lambda path: path.stat().st_mtime)


def remove_previous_job_descriptions() -> None:
    """
    Remove old active Job Description files.

    A locked file is reported clearly instead of producing an opaque 500.
    """
    for path in DATA_DIR.iterdir():
        if not path.is_file():
            continue

        if path.stem.lower() != ACTIVE_JD_PREFIX:
            continue

        if path.suffix.lower().lstrip(".") not in ALLOWED_EXTENSIONS:
            continue

        try:
            path.unlink()
        except PermissionError as exc:
            raise RuntimeError(
                f"Job Description '{path.name}' is currently in use. "
                "Close the PDF/TXT/DOCX in any application or preview window "
                "and try again."
            ) from exc


def save_active_job_description(file_storage) -> Path:
    """
    Save the uploaded JD as data/job_description.<extension>.

    This gives the screening pipeline one predictable active JD while
    preserving the original document format for parser.py.
    """
    safe_name = secure_filename(file_storage.filename or "")

    if not safe_name or not allowed_file(safe_name):
        raise ValueError("Unsupported Job Description file.")

    extension = get_extension(safe_name)
    destination = DATA_DIR / f"{ACTIVE_JD_PREFIX}.{extension}"

    remove_previous_job_descriptions()

    try:
        file_storage.save(destination)
    except PermissionError as exc:
        raise RuntimeError(
            f"Unable to save '{safe_name}' because the destination is locked. "
            "Close the file if it is open and try again."
        ) from exc

    return destination


def clear_active_resumes() -> None:
    """Clear only the current screening batch.

    Legacy files in data/resumes are never touched. This prevents the
    Windows/OneDrive file-lock problem from affecting new uploads.
    """
    locked: list[str] = []

    ACTIVE_RESUMES_DIR.mkdir(parents=True, exist_ok=True)

    for path in ACTIVE_RESUMES_DIR.iterdir():
        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
        except PermissionError:
            locked.append(path.name)

    if locked:
        raise RuntimeError(
            "The previous active resume batch is still in use: "
            + ", ".join(locked)
            + ". Close any PDF/preview window and try again."
        )


def save_resume_batch(files) -> list[str]:
    """Replace the active batch with the newly uploaded resumes."""
    valid_files = []

    for file in files:
        safe_name = secure_filename(file.filename or "")
        if not safe_name:
            continue
        if not allowed_file(safe_name):
            logger.warning("Skipped unsupported resume: %s", safe_name)
            continue
        valid_files.append((file, safe_name))

    if not valid_files:
        raise ValueError(
            "No supported resume files were uploaded. Use TXT, PDF, or DOCX."
        )

    # A single upload request represents one screening batch.
    clear_active_resumes()

    saved: list[str] = []
    used: set[str] = set()

    for file, safe_name in valid_files:
        destination_name = safe_name
        stem = Path(safe_name).stem
        suffix = Path(safe_name).suffix
        counter = 2

        while destination_name.lower() in used:
            destination_name = f"{stem}_{counter}{suffix}"
            counter += 1

        used.add(destination_name.lower())
        destination = ACTIVE_RESUMES_DIR / destination_name

        try:
            file.save(destination)
        except PermissionError as exc:
            raise RuntimeError(
                f"Unable to save resume '{safe_name}'. The destination is locked."
            ) from exc

        saved.append(destination_name)

    return saved


def build_screening_summary(summary) -> dict[str, Any]:
    """Convert the ranker summary object into a JSON response."""
    return {
        "total_candidates": summary.total_candidates,
        "shortlisted": summary.selected_candidates,
        "average_score": summary.average_score,
        "highest_score": summary.highest_score,
        "lowest_score": summary.lowest_score,
        "strong_matches": summary.strong_matches,
        "good_matches": summary.good_matches,
        "moderate_matches": summary.moderate_matches,
        "weak_matches": summary.weak_matches,
    }


# =============================================================================
# Frontend
# =============================================================================

@app.get("/")
def frontend_index():
    """Serve the ScreenAI dashboard."""
    index_file = FRONTEND_DIR / "index.html"

    if not index_file.exists():
        return json_error(
            "Frontend index.html was not found.",
            404,
        )

    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:filename>")
def frontend_assets(filename: str):
    """
    Serve frontend assets such as:
        /style.css
        /app.js
    """
    requested = FRONTEND_DIR / filename

    if not requested.is_file():
        # Allow API 404 handling to remain JSON.
        if filename.startswith("api/"):
            return json_error("API endpoint not found.", 404)

        return json_error("Frontend resource not found.", 404)

    return send_from_directory(FRONTEND_DIR, filename)


# =============================================================================
# Health & API Information
# =============================================================================

@app.get("/api/health")
def health_check():
    """Return application health status."""
    return jsonify(
        {
            "success": True,
            "status": "healthy",
            "service": "Resume Screening Agent",
            "version": "1.0.0",
        }
    )


@app.get("/api")
def api_info():
    """Return available API endpoints."""
    return jsonify(
        {
            "success": True,
            "application": "Resume Screening Agent",
            "version": "1.0.0",
            "endpoints": {
                "health": "/api/health",
                "screen": "/api/screen",
                "upload_job_description": "/api/upload/job-description",
                "upload_resumes": "/api/upload/resumes",
                "reports": "/api/reports/<filename>",
                "reset": "/api/reset",
            },
        }
    )


# =============================================================================
# Job Description Upload
# =============================================================================

@app.post("/api/upload/job-description")
def upload_job_description():
    """Upload and activate one Job Description."""
    if "file" not in request.files:
        return json_error("No Job Description file provided.")

    file = request.files["file"]

    if not file.filename:
        return json_error("Job Description filename is empty.")

    if not allowed_file(file.filename):
        return json_error(
            "Unsupported file type. Use TXT, PDF, or DOCX."
        )

    try:
        destination = save_active_job_description(file)

        logger.info(
            "Job Description activated: %s",
            destination.name,
        )

        return jsonify(
            {
                "success": True,
                "message": "Job Description uploaded successfully.",
                "filename": destination.name,
            }
        )

    except ValueError as exc:
        return json_error(str(exc), 400)

    except RuntimeError as exc:
        logger.warning("Job Description upload blocked: %s", exc)
        return json_error(str(exc), 409)

    except Exception as exc:
        logger.exception("Job Description upload failed.")
        return json_error(
            f"Upload failed: {exc}",
            500,
        )


# =============================================================================
# Resume Upload
# =============================================================================

@app.post("/api/upload/resumes")
def upload_resumes():
    """Upload a fresh candidate batch."""
    files = request.files.getlist("files")

    if not files:
        return json_error("No resume files provided.")

    try:
        uploaded_files = save_resume_batch(files)

        logger.info("Activated %d resume(s).", len(uploaded_files))

        return jsonify(
            {
                "success": True,
                "message": f"{len(uploaded_files)} resume(s) uploaded successfully.",
                "files": uploaded_files,
                "total_active_resumes": len(uploaded_files),
            }
        )

    except ValueError as exc:
        return json_error(str(exc), 400)

    except RuntimeError as exc:
        logger.warning("Resume upload blocked: %s", exc)
        return json_error(str(exc), 409)

    except Exception as exc:
        logger.exception("Resume upload failed.")
        return json_error(f"Upload failed: {exc}", 500)


# =============================================================================
# Screening Pipeline
# =============================================================================

@app.post("/api/screen")
def screen_candidates():
    """
    Run the complete AI screening pipeline.

    Pipeline:
        1. Document ingestion
        2. Semantic matching
        3. Candidate scoring
        4. Candidate ranking
        5. Report generation
    """
    try:
        payload = request.get_json(silent=True) or {}

        top_k = int(payload.get("top_k", TOP_K))
        threshold = float(
            payload.get("threshold", SCORE_THRESHOLD)
        )

        if top_k <= 0:
            return json_error(
                "top_k must be greater than zero."
            )

        if not 0 <= threshold <= 100:
            return json_error(
                "threshold must be between 0 and 100."
            )

        # ---------------------------------------------------------------------
        # Step 1 — Document ingestion
        # ---------------------------------------------------------------------

        active_jd = find_active_job_description()

        if active_jd is None:
            return json_error(
                "No active Job Description found. "
                "Upload a TXT, PDF, or DOCX Job Description first.",
                404,
            )

        logger.info(
            "Starting resume screening | top_k=%d | threshold=%.2f",
            top_k,
            threshold,
        )

        logger.info("Step 1/5: Loading documents...")

        job_description = load_job_description(
            str(active_jd)
        )

        resumes = load_resumes(
            str(ACTIVE_RESUMES_DIR)
        )

        if not resumes:
            return json_error(
                "No readable resumes found. Upload at least one resume.",
                404,
            )

        logger.info(
            "Loaded Job Description: %s",
            active_jd.name,
        )

        logger.info(
            "Loaded %d resume(s).",
            len(resumes),
        )

        # ---------------------------------------------------------------------
        # Step 2 — Semantic matching
        # ---------------------------------------------------------------------

        logger.info("Step 2/5: Semantic matching...")

        matcher = get_matcher()

        match_results = matcher.match_batch(
            job_description=job_description.text,
            resumes=resumes,
        )

        # ---------------------------------------------------------------------
        # Step 3 — Candidate scoring
        # ---------------------------------------------------------------------

        logger.info("Step 3/5: Candidate scoring...")

        scored_candidates = score_candidates(
            match_results=match_results,
            resumes=resumes,
        )

        # ---------------------------------------------------------------------
        # Step 4 — Candidate ranking
        # ---------------------------------------------------------------------

        logger.info("Step 4/5: Candidate ranking...")

        ranker = CandidateRanker(
            top_k=top_k,
            score_threshold=threshold,
        )

        ranked_candidates = ranker.rank(
            scored_candidates
        )

        # Normalize rank values so the API, dashboard and reports always use
        # sequential ranks: 1, 2, 3, ...
        for index, candidate in enumerate(ranked_candidates, start=1):
            try:
                candidate.rank = index
            except Exception:
                logger.warning(
                    "Could not update rank for candidate %s",
                    getattr(candidate, "candidate_name", "unknown"),
                )

        top_candidates = ranker.select_top_candidates(
            ranked_candidates
        )

        summary = ranker.create_summary(
            ranked_candidates=ranked_candidates,
            selected_candidates=top_candidates,
        )

        # ---------------------------------------------------------------------
        # Step 5 — Reports
        # ---------------------------------------------------------------------

        logger.info("Step 5/5: Generating reports...")

        reporter = ScreeningReporter(
            output_dir=OUTPUT_DIR
        )

        report_files = reporter.export_all(
            ranked_candidates=ranked_candidates,
            summary=summary,
        )

        response = {
            "success": True,
            "job_description": active_jd.name,
            "summary": build_screening_summary(summary),
            "candidates": [
                candidate_to_dict(candidate)
                for candidate in ranked_candidates
            ],
            "shortlist": [
                candidate_to_dict(candidate)
                for candidate in top_candidates
            ],
            "reports": {
                report_type: path.name
                for report_type, path in report_files.items()
            },
        }

        logger.info(
            "Screening completed successfully | candidates=%d | shortlisted=%d",
            summary.total_candidates,
            summary.selected_candidates,
        )

        return jsonify(response)

    except FileNotFoundError as exc:
        logger.exception("Required screening file not found.")
        return json_error(str(exc), 404)

    except UnicodeDecodeError:
        logger.exception("Unable to decode a screening document.")
        return json_error(
            "A text document could not be decoded as UTF-8. "
            "Use a UTF-8 TXT file or upload the Job Description as PDF/DOCX.",
            422,
        )

    except Exception as exc:
        logger.exception("Screening API failed.")
        return json_error(
            f"Screening failed: {exc}",
            500,
        )


# =============================================================================
# Reports
# =============================================================================

@app.get("/api/reports/<filename>")
def download_report(filename: str):
    """Download a generated screening report."""
    allowed_reports = {
        "screening_report.json",
        "candidate_ranking.csv",
        "screening_report.txt",
    }

    if filename not in allowed_reports:
        return json_error("Report not found.", 404)

    report_path = OUTPUT_DIR / filename

    if not report_path.exists():
        return json_error(
            "Report has not been generated yet.",
            404,
        )

    return send_file(
        report_path,
        as_attachment=True,
        download_name=filename,
    )


# =============================================================================
# Workspace Reset
# =============================================================================

@app.delete("/api/reset")
def reset_workspace():
    """Reset the active screening workspace."""
    try:
        clear_active_resumes()
        remove_previous_job_descriptions()

        for directory in (UPLOAD_DIR, OUTPUT_DIR):
            directory.mkdir(parents=True, exist_ok=True)
            for item in directory.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except PermissionError as exc:
                    raise RuntimeError(
                        f"File '{item.name}' is currently in use."
                    ) from exc

        logger.info("Workspace reset completed.")

        return jsonify(
            {
                "success": True,
                "message": "Workspace reset successfully.",
            }
        )

    except RuntimeError as exc:
        logger.warning("Workspace reset blocked: %s", exc)
        return json_error(str(exc), 409)

    except Exception as exc:
        logger.exception("Workspace reset failed.")
        return json_error(f"Reset failed: {exc}", 500)


# =============================================================================
# Error Handlers
# =============================================================================

@app.errorhandler(413)
def request_entity_too_large(_error):
    """Handle requests larger than the configured upload limit."""
    return json_error(
        "Uploaded files are too large. Maximum request size is 25 MB.",
        413,
    )


@app.errorhandler(404)
def not_found(_error):
    """Handle unknown routes."""
    return json_error(
        "API endpoint not found.",
        404,
    )


@app.errorhandler(500)
def internal_server_error(_error):
    """Handle unexpected server errors."""
    return json_error(
        "Internal server error.",
        500,
    )


# =============================================================================
# Development Server
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🤖 RESUME SCREENING AGENT")
    print("🌐 AI RESUME INTELLIGENCE PLATFORM")
    print("=" * 80)

    print("\nDashboard:")
    print("http://127.0.0.1:5000/")

    print("\nAPI:")
    print("http://127.0.0.1:5000/api")

    print("\nHealth Check:")
    print("http://127.0.0.1:5000/api/health")

    print("\nPress CTRL+C to stop the server.")
    print("=" * 80 + "\n")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False,
    )