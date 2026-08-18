/**
 * ============================================================================
 * ScreenAI - Resume Intelligence Platform
 * Frontend Application Controller
 * ============================================================================
 *
 * Backend:
 *   Flask API
 *
 * Frontend:
 *   Served directly by Flask
 *
 * ============================================================================
 */

"use strict";

/* ============================================================================
   CONFIGURATION
============================================================================ */

const API_BASE_URL = window.location.origin;

const API = {
    health: `${API_BASE_URL}/api/health`,
    screen: `${API_BASE_URL}/api/screen`,
    uploadJobDescription:
        `${API_BASE_URL}/api/upload/job-description`,
    uploadResumes:
        `${API_BASE_URL}/api/upload/resumes`,
    reports:
        `${API_BASE_URL}/api/reports`,
};


/* ============================================================================
   APPLICATION STATE
============================================================================ */

const state = {
    jobDescription: null,
    resumes: [],
    candidates: [],
    summary: null,

    apiOnline: false,
    screening: false,

    activeCandidate: null,
};


/* ============================================================================
   DOM HELPERS
============================================================================ */

const $ = (selector) =>
    document.querySelector(selector);

const $$ = (selector) =>
    [...document.querySelectorAll(selector)];

const setText = (element, value) => {
    if (element) {
        element.textContent = value ?? "0";
    }
};


/* ============================================================================
   DOM REFERENCES
============================================================================ */

const elements = {
    sidebar: $("#sidebar"),
    mobileMenuButton: $("#mobileMenuButton"),

    apiStatus: $("#apiStatus"),
    sidebarApiStatus: $("#sidebarApiStatus"),
    sidebarStatusIndicator: $("#sidebarStatusIndicator"),

    startScreeningButton:
        $("#startScreeningButton"),

    jobDescription:
        $("#jobDescription"),

    resumes:
        $("#resumes"),

    jobDropZone:
        $("#jobDropZone"),

    resumeDropZone:
        $("#resumeDropZone"),

    jobFilePreview:
        $("#jobFilePreview"),

    resumeFilePreview:
        $("#resumeFilePreview"),

    jobFileName:
        $("#jobFileName"),

    resumeFileName:
        $("#resumeFileName"),

    resumeFileCount:
        $("#resumeFileCount"),

    removeJobFile:
        $("#removeJobFile"),

    removeResumeFiles:
        $("#removeResumeFiles"),

    topK:
        $("#topK"),

    scoreThreshold:
        $("#scoreThreshold"),

    screenButton:
        $("#screenButton"),

    buttonIcon:
        $("#buttonIcon"),

    buttonLoader:
        $("#buttonLoader"),

    progressContainer:
        $("#progressContainer"),

    progressBar:
        $("#progressBar"),

    progressText:
        $("#progressText"),

    progressPercent:
        $("#progressPercent"),

    candidateTableBody:
        $("#candidateTableBody"),

    totalCandidates:
        $("#totalCandidates"),

    shortlistedCandidates:
        $("#shortlistedCandidates"),

    averageScore:
        $("#averageScore"),

    highestScore:
        $("#highestScore"),

    strongMatches:
        $("#strongMatches"),

    goodMatches:
        $("#goodMatches"),

    moderateMatches:
        $("#moderateMatches"),

    weakMatches:
        $("#weakMatches"),

    candidateModal:
        $("#candidateModal"),

    modalBackdrop:
        $("#modalBackdrop"),

    closeModal:
        $("#closeModal"),

    modalCandidateName:
        $("#modalCandidateName"),

    modalRecommendation:
        $("#modalRecommendation"),

    modalFinalScore:
        $("#modalFinalScore"),

    modalSemantic:
        $("#modalSemantic"),

    modalRequired:
        $("#modalRequired"),

    modalPreferred:
        $("#modalPreferred"),

    modalExperience:
        $("#modalExperience"),

    modalEducation:
        $("#modalEducation"),

    modalMatchedSkills:
        $("#modalMatchedSkills"),

    modalMissingSkills:
        $("#modalMissingSkills"),

    toast:
        $("#toast"),

    toastIcon:
        $("#toastIcon"),

    toastMessage:
        $("#toastMessage"),
};


/* ============================================================================
   INITIALIZATION
============================================================================ */

document.addEventListener(
    "DOMContentLoaded",
    initializeApplication
);


async function initializeApplication() {

    console.log(
        "ScreenAI frontend initializing..."
    );

    setupNavigation();
    setupMobileNavigation();
    setupFileInputs();
    setupDragAndDrop();
    setupScreening();
    setupReports();
    setupModal();
    setupKeyboardShortcuts();

    await checkApiHealth();

    console.log(
        "ScreenAI frontend initialized."
    );
}


/* ============================================================================
   API HEALTH
============================================================================ */

async function checkApiHealth() {

    setApiStatus(
        "checking",
        "Checking API"
    );

    try {

        const response = await fetch(
            API.health,
            {
                method: "GET",
                headers: {
                    Accept:
                        "application/json",
                },
            }
        );

        const data =
            await parseResponse(response);

        if (!data.success) {
            throw new Error(
                "API health check failed."
            );
        }

        state.apiOnline = true;

        setApiStatus(
            "online",
            "API Online"
        );

        console.log(
            "ScreenAI API is online."
        );

    } catch (error) {

        state.apiOnline = false;

        setApiStatus(
            "offline",
            "API Offline"
        );

        console.error(
            "API health check failed:",
            error
        );
    }
}


/* ============================================================================
   API STATUS UI
============================================================================ */

function setApiStatus(
    status,
    label
) {

    if (elements.apiStatus) {

        elements.apiStatus.className =
            `api-pill ${status}`;

        elements.apiStatus.innerHTML = `
            <span class="status-dot"></span>
            ${escapeHtml(label)}
        `;
    }


    if (elements.sidebarApiStatus) {

        const messages = {
            online: "System operational",
            checking: "Checking...",
            offline: "Backend unavailable",
        };

        elements.sidebarApiStatus.textContent =
            messages[status] ||
            "Unknown";
    }


    if (elements.sidebarStatusIndicator) {

        elements.sidebarStatusIndicator
            .className =
            "status-indicator";

        if (status === "online") {

            elements.sidebarStatusIndicator
                .classList
                .add("online");

        } else if (status === "offline") {

            elements.sidebarStatusIndicator
                .classList
                .add("offline");
        }
    }
}


/* ============================================================================
   NAVIGATION
============================================================================ */

function setupNavigation() {

    $$(".nav-link").forEach(
        (link) => {

            link.addEventListener(
                "click",
                () => {

                    $$(".nav-link")
                        .forEach(
                            item =>
                                item.classList
                                    .remove("active")
                        );

                    link.classList.add(
                        "active"
                    );

                    closeMobileSidebar();
                }
            );
        }
    );
}


function setupMobileNavigation() {

    if (!elements.mobileMenuButton) {
        return;
    }

    elements.mobileMenuButton.addEventListener(
        "click",
        () => {

            elements.sidebar?.classList
                .toggle("open");
        }
    );
}


function closeMobileSidebar() {

    if (
        elements.sidebar &&
        window.innerWidth <= 760
    ) {

        elements.sidebar.classList
            .remove("open");
    }
}


/* ============================================================================
   SCREENING NAVIGATION
============================================================================ */

function setupScreening() {

    elements.startScreeningButton
        ?.addEventListener(
            "click",
            () => {

                $("#screening")
                    ?.scrollIntoView({
                        behavior: "smooth",
                    });
            }
        );


    elements.screenButton
        ?.addEventListener(
            "click",
            handleScreening
        );
}


/* ============================================================================
   FILE INPUTS
============================================================================ */

function setupFileInputs() {

    elements.jobDescription
        ?.addEventListener(
            "change",
            handleJobDescription
        );


    elements.resumes
        ?.addEventListener(
            "change",
            handleResumes
        );


    elements.removeJobFile
        ?.addEventListener(
            "click",
            clearJobDescription
        );


    elements.removeResumeFiles
        ?.addEventListener(
            "click",
            clearResumes
        );
}


/* ============================================================================
   JOB DESCRIPTION
============================================================================ */

function handleJobDescription(event) {

    const file =
        event.target.files?.[0];

    if (!file) {
        return;
    }

    if (!isSupportedFile(file)) {

        showToast(
            "error",
            "Please select a TXT, PDF, or DOCX file."
        );

        event.target.value = "";

        return;
    }

    state.jobDescription = file;

    updateJobDescriptionPreview();

    showToast(
        "success",
        "Job Description selected."
    );
}


function updateJobDescriptionPreview() {

    if (elements.jobFileName) {

        elements.jobFileName.textContent =
            state.jobDescription?.name ||
            "—";
    }

    if (elements.jobFilePreview) {

        elements.jobFilePreview.hidden =
            !state.jobDescription;
    }
}


function clearJobDescription() {

    state.jobDescription = null;

    if (elements.jobDescription) {
        elements.jobDescription.value = "";
    }

    updateJobDescriptionPreview();
}


/* ============================================================================
   RESUMES
============================================================================ */

function handleResumes(event) {

    const files =
        [...event.target.files];

    if (!files.length) {
        return;
    }

    setResumes(files);
}


function setResumes(files) {

    const validFiles =
        files.filter(
            isSupportedFile
        );


    if (validFiles.length !== files.length) {

        showToast(
            "error",
            "Some files were skipped because they are unsupported."
        );
    }


    if (!validFiles.length) {

        clearResumes();

        return;
    }


    state.resumes = validFiles;

    updateResumePreview();


    showToast(
        "success",
        `${validFiles.length} resume(s) selected.`
    );
}


function updateResumePreview() {

    const count =
        state.resumes.length;


    if (elements.resumeFilePreview) {

        elements.resumeFilePreview.hidden =
            count === 0;
    }


    if (elements.resumeFileName) {

        elements.resumeFileName.textContent =
            count === 0
                ? "—"
                : count === 1
                    ? state.resumes[0].name
                    : `${count} candidate resumes`;
    }


    if (elements.resumeFileCount) {

        elements.resumeFileCount.textContent =
            `${count} file${count === 1 ? "" : "s"} selected`;
    }
}


function clearResumes() {

    state.resumes = [];

    if (elements.resumes) {
        elements.resumes.value = "";
    }

    updateResumePreview();
}


/* ============================================================================
   FILE VALIDATION
============================================================================ */

function isSupportedFile(file) {

    if (!file?.name) {
        return false;
    }

    const allowed =
        [
            ".txt",
            ".pdf",
            ".docx",
        ];


    const filename =
        file.name.toLowerCase();


    return allowed.some(
        extension =>
            filename.endsWith(extension)
    );
}


/* ============================================================================
   DRAG & DROP
============================================================================ */

function setupDragAndDrop() {

    setupDropZone(
        elements.jobDropZone,
        false
    );

    setupDropZone(
        elements.resumeDropZone,
        true
    );
}


function setupDropZone(
    zone,
    multiple
) {

    if (!zone) {
        return;
    }


    [
        "dragenter",
        "dragover",
    ].forEach(
        eventName => {

            zone.addEventListener(
                eventName,
                event => {

                    event.preventDefault();

                    zone.classList.add(
                        "dragover"
                    );
                }
            );
        }
    );


    [
        "dragleave",
        "drop",
    ].forEach(
        eventName => {

            zone.addEventListener(
                eventName,
                event => {

                    event.preventDefault();

                    zone.classList.remove(
                        "dragover"
                    );
                }
            );
        }
    );


    zone.addEventListener(
        "drop",
        event => {

            const files =
                [...event.dataTransfer.files];


            if (!files.length) {
                return;
            }


            if (multiple) {

                setResumes(files);

            } else {

                const file =
                    files[0];


                if (!isSupportedFile(file)) {

                    showToast(
                        "error",
                        "Unsupported file format."
                    );

                    return;
                }


                state.jobDescription =
                    file;

                updateJobDescriptionPreview();

                showToast(
                    "success",
                    "Job Description added."
                );
            }
        }
    );
}


/* ============================================================================
   MAIN SCREENING PIPELINE
============================================================================ */

async function handleScreening() {

    if (state.screening) {
        return;
    }


    if (!state.jobDescription) {

        showToast(
            "error",
            "Please select a Job Description."
        );

        return;
    }


    if (!state.resumes.length) {

        showToast(
            "error",
            "Please select at least one resume."
        );

        return;
    }


    if (!state.apiOnline) {

        await checkApiHealth();

        if (!state.apiOnline) {

            showToast(
                "error",
                "Flask API is offline."
            );

            return;
        }
    }


    const topK =
        Number(
            elements.topK?.value || 5
        );


    const threshold =
        Number(
            elements.scoreThreshold?.value || 70
        );


    if (
        !Number.isInteger(topK) ||
        topK < 1 ||
        topK > 100
    ) {

        showToast(
            "error",
            "Shortlist size must be between 1 and 100."
        );

        return;
    }


    if (
        Number.isNaN(threshold) ||
        threshold < 0 ||
        threshold > 100
    ) {

        showToast(
            "error",
            "Minimum score must be between 0 and 100."
        );

        return;
    }


    state.screening = true;

    setScreeningLoading(true);

    showProgress(
        5,
        "Preparing screening..."
    );


    try {

        // ------------------------------------------------------------
        // 1. Upload Job Description
        // ------------------------------------------------------------

        showProgress(
            20,
            "Uploading Job Description..."
        );

        await uploadJobDescription(
            state.jobDescription
        );


        // ------------------------------------------------------------
        // 2. Upload Resumes
        // ------------------------------------------------------------

        showProgress(
            35,
            "Uploading candidate resumes..."
        );

        await uploadResumes(
            state.resumes
        );


        // ------------------------------------------------------------
        // 3. Run AI Screening
        // ------------------------------------------------------------

        showProgress(
            50,
            "Running semantic AI matching..."
        );

        const result =
            await runScreening(
                topK,
                threshold
            );


        // ------------------------------------------------------------
        // 4. Render Results
        // ------------------------------------------------------------

        showProgress(
            85,
            "Preparing candidate rankings..."
        );

        processScreeningResult(
            result
        );


        showProgress(
            100,
            "Screening completed successfully."
        );


        showToast(
            "success",
            "AI screening completed successfully."
        );


        $("#candidates")
            ?.scrollIntoView({
                behavior: "smooth",
            });


    } catch (error) {

        console.error(
            "Screening error:",
            error
        );

        showToast(
            "error",
            getFriendlyError(error)
        );


    } finally {

        state.screening = false;

        setScreeningLoading(false);

        setTimeout(
            hideProgress,
            800
        );
    }
}


/* ============================================================================
   UPLOAD JOB DESCRIPTION
============================================================================ */

async function uploadJobDescription(file) {

    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );


    const response =
        await fetch(
            API.uploadJobDescription,
            {
                method: "POST",
                body: formData,
            }
        );


    const data =
        await parseResponse(
            response
        );


    if (!data.success) {

        throw new Error(
            data.error ||
            "Job Description upload failed."
        );
    }


    return data;
}


/* ============================================================================
   UPLOAD RESUMES
============================================================================ */

async function uploadResumes(files) {

    const formData =
        new FormData();


    files.forEach(
        file => {

            formData.append(
                "files",
                file
            );
        }
    );


    const response =
        await fetch(
            API.uploadResumes,
            {
                method: "POST",
                body: formData,
            }
        );


    const data =
        await parseResponse(
            response
        );


    if (!data.success) {

        throw new Error(
            data.error ||
            "Resume upload failed."
        );
    }


    return data;
}


/* ============================================================================
   RUN SCREENING
============================================================================ */

async function runScreening(
    topK,
    threshold
) {

    const response =
        await fetch(
            API.screen,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json",

                    Accept:
                        "application/json",
                },

                body: JSON.stringify({
                    top_k: topK,
                    threshold,
                }),
            }
        );


    const data =
        await parseResponse(
            response
        );


    if (!data.success) {

        throw new Error(
            data.error ||
            "Screening failed."
        );
    }


    return data;
}


/* ============================================================================
   API RESPONSE HANDLER
============================================================================ */

async function parseResponse(
    response
) {

    let data;


    try {

        data =
            await response.json();

    } catch {

        throw new Error(
            `Invalid server response (${response.status}).`
        );
    }


    if (!response.ok) {

        throw new Error(
            data.error ||
            `Server error: ${response.status}`
        );
    }


    return data;
}


/* ============================================================================
   PROCESS SCREENING RESULT
============================================================================ */

function processScreeningResult(
    result
) {

    state.candidates =
        Array.isArray(
            result.candidates
        )
            ? result.candidates
            : [];


    state.summary =
        result.summary ||
        null;


    renderSummary(
        state.summary
    );


    renderCandidates(
        state.candidates
    );
}


/* ============================================================================
   SUMMARY
============================================================================ */

function renderSummary(
    summary
) {

    if (!summary) {
        return;
    }


    setText(
        elements.totalCandidates,
        formatNumber(
            summary.total_candidates
        )
    );


    setText(
        elements.shortlistedCandidates,
        formatNumber(
            summary.shortlisted
        )
    );


    setText(
        elements.averageScore,
        formatScore(
            summary.average_score
        )
    );


    setText(
        elements.highestScore,
        formatScore(
            summary.highest_score
        )
    );


    setText(
        elements.strongMatches,
        formatNumber(
            summary.strong_matches
        )
    );


    setText(
        elements.goodMatches,
        formatNumber(
            summary.good_matches
        )
    );


    setText(
        elements.moderateMatches,
        formatNumber(
            summary.moderate_matches
        )
    );


    setText(
        elements.weakMatches,
        formatNumber(
            summary.weak_matches
        )
    );
}


/* ============================================================================
   CANDIDATE TABLE
============================================================================ */

function renderCandidates(
    candidates
) {

    if (!elements.candidateTableBody) {
        return;
    }


    if (!candidates.length) {

        elements.candidateTableBody.innerHTML = `
            <tr>
                <td
                    colspan="7"
                    class="table-empty"
                >
                    <div class="empty-state">
                        <div class="empty-icon">
                            —
                        </div>

                        <strong>
                            No screening results
                        </strong>

                        <span>
                            Run AI screening to view candidates.
                        </span>
                    </div>
                </td>
            </tr>
        `;

        return;
    }


    elements.candidateTableBody.innerHTML =
        candidates
            .map(
                (candidate, index) =>
                    createCandidateRow(
                        candidate,
                        index
                    )
            )
            .join("");


    attachCandidateEvents();
}


function createCandidateRow(
    candidate,
    index
) {

    const rank =
        candidate.rank ??
        index + 1;


    const score =
        Number(
            candidate.final_score || 0
        );


    const semantic =
        Number(
            candidate.semantic_score || 0
        );


    const skills =
        Number(
            candidate.required_skill_score || 0
        );


    const decision =
        candidate.recommendation ||
        getDecisionFromScore(
            score
        );


    const name =
        candidate.candidate_name ||
        `Candidate ${rank}`;


    return `
        <tr>

            <td>
                <span
                    class="table-rank ${
                        rank <= 3
                            ? "top-rank"
                            : ""
                    }"
                >
                    ${rank}
                </span>
            </td>

            <td>
                <span class="candidate-name">
                    ${escapeHtml(name)}
                </span>
            </td>

            <td>
                <span
                    class="score-cell ${getScoreClass(score)}"
                >
                    ${formatScore(score)}
                </span>
            </td>

            <td>
                ${formatScore(semantic)}
            </td>

            <td>
                ${formatScore(skills)}
            </td>

            <td>
                <span
                    class="decision-badge ${
                        getDecisionClass(decision)
                    }"
                >
                    ${escapeHtml(decision)}
                </span>
            </td>

            <td>
                <button
                    type="button"
                    class="details-button"
                    data-candidate-index="${index}"
                >
                    View
                </button>
            </td>

        </tr>
    `;
}


/* ============================================================================
   CANDIDATE DETAILS
============================================================================ */

function attachCandidateEvents() {

    $$(".details-button")
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        const index =
                            Number(
                                button.dataset
                                    .candidateIndex
                            );


                        const candidate =
                            state.candidates[index];


                        if (candidate) {

                            openCandidateModal(
                                candidate
                            );
                        }
                    }
                );
            }
        );
}


/* ============================================================================
   MODAL
============================================================================ */

function setupModal() {

    elements.closeModal
        ?.addEventListener(
            "click",
            closeCandidateModal
        );


    elements.modalBackdrop
        ?.addEventListener(
            "click",
            closeCandidateModal
        );
}


function openCandidateModal(
    candidate
) {

    state.activeCandidate =
        candidate;


    const score =
        Number(
            candidate.final_score || 0
        );


    const decision =
        candidate.recommendation ||
        getDecisionFromScore(
            score
        );


    setText(
        elements.modalCandidateName,
        candidate.candidate_name ||
        "Candidate"
    );


    setText(
        elements.modalFinalScore,
        formatScore(score)
    );


    setText(
        elements.modalSemantic,
        formatScore(
            candidate.semantic_score
        )
    );


    setText(
        elements.modalRequired,
        formatScore(
            candidate.required_skill_score
        )
    );


    setText(
        elements.modalPreferred,
        formatScore(
            candidate.preferred_skill_score
        )
    );


    setText(
        elements.modalExperience,
        formatScore(
            candidate.experience_score
        )
    );


    setText(
        elements.modalEducation,
        formatScore(
            candidate.education_score
        )
    );


    if (elements.modalRecommendation) {

        elements.modalRecommendation
            .className =
            `decision-badge ${
                getDecisionClass(decision)
            }`;

        elements.modalRecommendation
            .textContent =
            decision;
    }


    renderSkills(
        elements.modalMatchedSkills,
        candidate.matched_skills,
        "matched"
    );


    renderSkills(
        elements.modalMissingSkills,
        candidate.missing_skills,
        "missing"
    );


    if (elements.candidateModal) {

        elements.candidateModal.hidden =
            false;

        document.body.style.overflow =
            "hidden";
    }
}


function closeCandidateModal() {

    if (elements.candidateModal) {

        elements.candidateModal.hidden =
            true;
    }

    document.body.style.overflow =
        "";

    state.activeCandidate =
        null;
}


function renderSkills(
    container,
    skills,
    type
) {

    if (!container) {
        return;
    }


    const values =
        Array.isArray(skills)
            ? skills
            : [];


    if (!values.length) {

        container.innerHTML = `
            <span class="skill-tag ${type}">
                None identified
            </span>
        `;

        return;
    }


    container.innerHTML =
        values
            .map(
                skill => `
                    <span
                        class="skill-tag ${type}"
                    >
                        ${escapeHtml(skill)}
                    </span>
                `
            )
            .join("");
}


/* ============================================================================
   REPORTS
============================================================================ */

function setupReports() {

    $$("[data-report]")
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        const filename =
                            button.dataset.report;

                        downloadReport(
                            filename
                        );
                    }
                );
            }
        );
}


function downloadReport(
    filename
) {

    if (!filename) {
        return;
    }


    const url =
        `${API.reports}/${encodeURIComponent(
            filename
        )}`;


    const link =
        document.createElement("a");


    link.href = url;

    link.download = filename;

    document.body.appendChild(
        link
    );

    link.click();

    link.remove();
}


/* ============================================================================
   SCREENING LOADING
============================================================================ */

function setScreeningLoading(
    loading
) {

    if (!elements.screenButton) {
        return;
    }


    elements.screenButton.disabled =
        loading;


    if (elements.buttonIcon) {

        elements.buttonIcon.textContent =
            loading
                ? "Processing..."
                : "Run AI Screening";
    }


    if (elements.buttonLoader) {

        elements.buttonLoader.hidden =
            !loading;
    }
}


/* ============================================================================
   PROGRESS
============================================================================ */

function showProgress(
    percentage,
    message
) {

    if (!elements.progressContainer) {
        return;
    }


    const value =
        Math.max(
            0,
            Math.min(
                100,
                Number(percentage) || 0
            )
        );


    elements.progressContainer.hidden =
        false;


    if (elements.progressBar) {

        elements.progressBar.style.width =
            `${value}%`;
    }


    if (elements.progressPercent) {

        elements.progressPercent.textContent =
            `${value}%`;
    }


    if (elements.progressText) {

        elements.progressText.textContent =
            message;
    }
}


function hideProgress() {

    if (elements.progressContainer) {

        elements.progressContainer.hidden =
            true;
    }


    if (elements.progressBar) {

        elements.progressBar.style.width =
            "0%";
    }
}


/* ============================================================================
   TOAST
============================================================================ */

let toastTimer = null;


function showToast(
    type,
    message
) {

    if (
        !elements.toast ||
        !elements.toastMessage
    ) {
        return;
    }


    clearTimeout(
        toastTimer
    );


    if (elements.toastIcon) {

        elements.toastIcon.textContent =
            type === "success"
                ? "✓"
                : "!";
    }


    elements.toastMessage.textContent =
        message;


    elements.toast.classList.add(
        "show"
    );


    toastTimer =
        setTimeout(
            () => {

                elements.toast.classList
                    .remove("show");

            },
            3500
        );
}


/* ============================================================================
   KEYBOARD
============================================================================ */

function setupKeyboardShortcuts() {

    document.addEventListener(
        "keydown",
        event => {

            if (event.key === "Escape") {

                closeCandidateModal();

                closeMobileSidebar();
            }
        }
    );
}


/* ============================================================================
   FORMATTING
============================================================================ */

function formatScore(
    value
) {

    const number =
        Number(value);


    if (Number.isNaN(number)) {
        return "0%";
    }


    return `${number.toFixed(2)}%`;
}


function formatNumber(
    value
) {

    const number =
        Number(value);


    if (Number.isNaN(number)) {
        return "0";
    }


    return number.toLocaleString();
}


/* ============================================================================
   SCORE STYLING
============================================================================ */

function getScoreClass(
    score
) {

    if (score >= 80) {
        return "score-high";
    }


    if (score >= 60) {
        return "score-medium";
    }


    return "score-low";
}


function getDecisionClass(
    decision
) {

    const value =
        String(
            decision || ""
        ).toLowerCase();


    if (value.includes("strong")) {
        return "decision-strong";
    }


    if (value.includes("good")) {
        return "decision-good";
    }


    if (value.includes("moderate")) {
        return "decision-moderate";
    }


    return "decision-weak";
}


function getDecisionFromScore(
    score
) {

    if (score >= 80) {
        return "Strong Match";
    }


    if (score >= 70) {
        return "Good Match";
    }


    if (score >= 60) {
        return "Moderate Match";
    }


    return "Weak Match";
}


/* ============================================================================
   SECURITY
============================================================================ */

function escapeHtml(
    value
) {

    return String(value)
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}


/* ============================================================================
   ERROR HANDLING
============================================================================ */

function getFriendlyError(
    error
) {

    const message =
        error?.message ||
        "An unexpected error occurred.";


    if (
        message.includes(
            "Failed to fetch"
        )
    ) {

        return (
            "Unable to connect to Flask. " +
            "Make sure python src/app.py is running."
        );
    }


    return message;
}


/* ============================================================================
   GLOBAL SCREENAI API
============================================================================ */

window.ScreenAI = {

    state,

    checkApiHealth,

    runScreening,

    downloadReport,

};


/* ============================================================================
   STARTUP LOG
============================================================================ */

console.log(
    "ScreenAI application controller loaded."
);