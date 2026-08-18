# ScreenAI — AI Resume Screening Platform

> An AI-powered resume screening and candidate intelligence platform that analyzes candidate resumes against job descriptions, calculates relevance scores, ranks candidates, and generates screening reports.

---

## 📌 Overview

ScreenAI is a Python and Flask-based resume screening platform designed to simplify the initial candidate evaluation process.

Recruiters can upload a **Job Description (JD)** and one or more **candidate resumes**. The system extracts the document content, performs semantic matching using an AI embedding model, calculates candidate scores, ranks candidates, and generates structured screening reports.

### Key Capabilities

- Job Description upload
- Multiple resume upload
- PDF, DOCX, and TXT document parsing
- AI-based semantic resume matching
- Candidate scoring
- Candidate ranking
- Shortlisting based on configurable score threshold
- Screening reports in JSON, CSV, and TXT formats
- REST API
- API health monitoring
- Recruiter-friendly web dashboard

---

## ✨ Features

### 🤖 AI Resume Matching

ScreenAI uses the **Sentence Transformers `all-MiniLM-L6-v2`** model to generate semantic embeddings and compare the Job Description with candidate resumes.

### 📄 Document Processing

Supports commonly used recruitment documents:

- PDF
- DOCX
- TXT

### 📊 Candidate Scoring

Candidates receive a relevance score based on their semantic similarity to the provided Job Description.

### 🏆 Candidate Ranking

Candidates are ranked according to their screening scores, allowing recruiters to quickly identify stronger matches.

### 🎯 Shortlisting

Recruiters can configure:

- Maximum shortlist size
- Minimum candidate score

Candidates meeting the configured threshold can be selected for further consideration.

### 📑 Automated Reports

After screening, ScreenAI generates:

```text
screening_report.json
candidate_ranking.csv
screening_report.txt
