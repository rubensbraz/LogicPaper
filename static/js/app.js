/**
 * Main Application Logic
 * Handles state management, file uploading, and SSE communication.
 */

// --- Global State ---
let sessionId = crypto.randomUUID();
let isProcessing = false;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    initializeDragDrop(['dropData', 'dropTemplates', 'dropAssets']);
});

// --- State Management ---

/**
 * COMPLETELY resets the application state by reloading the page.
 * This ensures a truly clean slate (memory, file inputs, global variables).
 */
function performFullReset() {
    window.location.reload();
}

/**
 * Resets the UI state when inputs change.
 * Allows the user to start a fresh batch without page reload.
 * @param {string} type - The type of input changed ('excel', 'template', 'asset').
 */
function resetStateOnInput(type) {
    if (isProcessing) return;

    // 1. Hide Result Panel, Show Action Panel
    document.getElementById('resultPanel').classList.add('hidden');
    document.getElementById('actionPanel').classList.remove('hidden');

    // 2. Specific logic for Excel changes
    if (type === 'data') {
        const previewEl = document.getElementById('jsonPreview');
        previewEl.innerText = i18n.t('dashboard.config.placeholder_excel');
        previewEl.className = "absolute inset-0 p-4 text-xs font-mono text-green-400 overflow-auto scrollbar-thin";

        // Lock Config Panel until re-analysis
        document.getElementById('configPanel').classList.add('opacity-50', 'pointer-events-none');
        document.getElementById('colSelect').innerHTML = `<option>${i18n.t('dashboard.config.placeholder_excel')}</option>`;
    }

    // 3. Add visual separator in logs to indicate new context
    const term = document.getElementById('terminal');
    if (term.innerText.trim() !== i18n.t('dashboard.logs.ready')) {
        logToTerminal(i18n.t('alerts.inputs_changed'), 'info');
    }
}

// --- Drag & Drop Logic ---

/**
 * Initializes drag and drop listeners for a list of element IDs.
 * @param {string[]} ids - Array of DOM IDs.
 */
function initializeDragDrop(ids) {
    ids.forEach(id => {
        const dropZone = document.getElementById(id);
        const input = dropZone.querySelector('input');

        // Prevent default browser behavior
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });

        // Visual Feedback
        ['dragenter', 'dragover'].forEach(evt => {
            dropZone.addEventListener(evt, () => dropZone.classList.add('drag-over'), false);
        });

        ['dragleave', 'drop'].forEach(evt => {
            dropZone.addEventListener(evt, () => dropZone.classList.remove('drag-over'), false);
        });

        // Handle Drop
        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                input.files = files;
                updateUI(input);
            }
        }, false);
    });
}

/**
 * Updates the UI labels when files are selected.
 * Triggers state reset but DOES NOT auto-analyze.
 * @param {HTMLInputElement} input - The file input element.
 */
function updateUI(input) {
    const labelId = input.id.replace('file', 'lbl').replace('Excel', 'Data');
    const label = document.getElementById(input.id === 'fileData' ? 'lblData' : labelId);

    if (input.files && input.files.length > 0) {
        if (input.files.length === 1) {
            label.innerText = input.files[0].name;
        } else {
            label.innerText = i18n.t('alerts.files_selected_plural', { count: input.files.length });
        }

        // Visual confirmation style
        label.classList.add('text-blue-400', 'font-bold');
        label.classList.remove('text-gray-500');

        // Reset state (hide results, lock config) to force re-analysis
        const type = input.id === 'fileData' ? 'data' : 'other';
        resetStateOnInput(type);
    }
}

// --- API Helpers ---

/**
 * Helper to append correct data file to FormData
 */
function appendDataFile(formData, file) {
    if (file.name.toLowerCase().endsWith('.json')) {
        formData.append('file_json', file);
    } else {
        formData.append('file_excel', file);
    }
}

// --- API Actions ---

/**
 * MASTER FUNCTION: Orchestrates the Analysis and Validation workflow.
 * 1. Checks inputs.
 * 2. Runs Data Preview (Backend Analysis).
 * 3. Runs Template Validation (Backend Comparison).
 * 4. Unlocks Configuration if successful.
 */
async function performAnalysisSequence() {
    // Environment Guard: Check for Static Demo (GitHub Pages)
    // Since GitHub Pages only hosts static files, the backend API is unreachable
    if (CONFIG.env.isGithubPages) {
        Swal.fire({
            icon: 'info',
            title: i18n.t('alerts.static_mode.title'),
            html: i18n.t('alerts.static_mode.html'),
            background: '#1e293b',
            color: '#fff',
            confirmButtonColor: '#3b82f6',
            confirmButtonText: 'Understood'
        });
        return; // Halt execution immediately
    }

    const fileData = document.getElementById('fileData').files[0];
    const fileTemplates = document.getElementById('fileTemplates').files;

    // 1. Basic Input Validation
    if (!fileData) return Swal.fire({ icon: 'warning', title: i18n.t('alerts.missing_excel.title'), text: i18n.t('alerts.missing_excel.text'), background: '#1e293b', color: '#fff' });
    if (fileTemplates.length === 0) return Swal.fire({ icon: 'warning', title: i18n.t('alerts.missing_excel.title'), text: i18n.t('alerts.missing_templates.text'), background: '#1e293b', color: '#fff' });

    // 2. UI Loading State
    const btn = document.getElementById('btnValidate');
    const originalText = btn.innerHTML;
    btn.innerHTML = `<span class="animate-pulse">${i18n.t('dashboard.ingestion.btn_validating')}</span>`;
    btn.disabled = true;

    try {
        // 3. Step 1: Preview Data (Excel Analysis)
        // We await the result. If false, we stop.
        const previewSuccess = await previewData(fileData);
        if (!previewSuccess) throw new Error(i18n.t('alerts.analysis_failed'));

        // 4. Step 2: Validate Templates (Compatibility Check)
        const validationSuccess = await validateTemplates(fileData, fileTemplates);

        // 5. Unlock Configuration Panel only if everything passed
        if (validationSuccess) {
            document.getElementById('configPanel').classList.remove('opacity-50', 'pointer-events-none');
            // Log success to terminal
            logToTerminal(i18n.t('alerts.validation_success'), "success");
        }

    } catch (e) {
        // Silent catch (errors handled in sub-functions), but ensure button resets
        console.error(e);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}
/**
 * Analyzes the Excel file and populates the JSON preview.
 * @param {File} fileData - The Excel file object.
 * @returns {Promise<boolean>} True if successful.
 */
async function previewData(fileData) {
    const formData = new FormData();
    appendDataFile(formData, fileData);

    const prevEl = document.getElementById(CONFIG.dom.jsonPreview);
    prevEl.innerText = i18n.t('dashboard.preview.step1');
    prevEl.className = "absolute inset-0 p-4 text-xs font-mono text-blue-400 overflow-auto scrollbar-thin animate-pulse";

    try {
        const res = await fetch(CONFIG.endpoints.preview, { method: 'POST', body: formData });
        const data = await res.json();

        if (data.status === 'success') {
            // Render JSON
            prevEl.className = "absolute inset-0 p-4 text-xs font-mono text-green-400 overflow-auto scrollbar-thin";
            prevEl.innerText = JSON.stringify(data.preview, null, 2);

            // Populate Dropdown
            const sel = document.getElementById('colSelect');
            sel.innerHTML = `<option value="">${i18n.t('dashboard.config.opt_select_col')}</option>`;
            data.headers.forEach(h => {
                let opt = document.createElement('option');
                opt.value = h;
                opt.innerText = h;
                sel.appendChild(opt);
            });
            return true;
        } else {
            throw new Error(data.message);
        }
    } catch (e) {
        Swal.fire({ icon: 'error', title: i18n.t('alerts.analysis_failed'), text: e.message, background: '#1e293b', color: '#fff' });
        prevEl.innerText = i18n.t('dashboard.preview.error') + e.message;
        prevEl.className = "absolute inset-0 p-4 text-xs font-mono text-red-400 overflow-auto scrollbar-thin";
        return false;
    }
}

/**
 * Validates that template variables match Excel headers.
 * @param {File} fileData - The Excel file.
 * @param {FileList} fileTemplates - The list of templates.
 * @returns {Promise<boolean>} True if valid (or warning shown).
 */
async function validateTemplates(fileData, fileTemplates) {
    const formData = new FormData();
    appendDataFile(formData, fileData);
    for (let i = 0; i < fileTemplates.length; i++) {
        formData.append('files_templates', fileTemplates[i]);
    }

    try {
        const res = await fetch(CONFIG.endpoints.validate, { method: 'POST', body: formData });
        const data = await res.json();

        if (data.status === 'success') {
            renderValidationReport(data.report);
            // We return true even if there are warnings, to allow the user to proceed if they choose.
            // Strict mode would return data.report.overall_valid
            return true;
        } else {
            throw new Error(data.message);
        }
    } catch (e) {
        Swal.fire({ icon: 'error', title: 'Validation Failed', text: e.message, background: '#1e293b', color: '#fff' });
        return false;
    }
}

/**
 * Renders the validation results modal.
 * @param {Object} report - The validation report object from the backend.
 */
function renderValidationReport(report) {
    const valid = report.overall_valid;

    // Use i18n keys from 'alerts.validation_modal'
    const titleText = valid ? i18n.t('alerts.validation_modal.title_ok') : i18n.t('alerts.validation_modal.title_fail');
    const descText = valid ? i18n.t('alerts.validation_modal.desc_ok') : i18n.t('alerts.validation_modal.desc_fail');

    // 1. Build Header
    let html = `
    <div class="flex flex-col gap-6 text-left">
        <div class="p-4 rounded-xl border ${valid ? 'bg-green-500/10 border-green-500/50' : 'bg-red-500/10 border-red-500/50'} flex items-center gap-4">
            <div class="w-12 h-12 flex items-center justify-center rounded-full shrink-0 ${valid ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}">
                <span class="text-2xl leading-none">${valid ? '✔' : '⚠'}</span>
            </div>
            <div>
                <h3 class="text-lg font-bold text-white">${titleText}</h3>
                <p class="text-sm ${valid ? 'text-green-300' : 'text-red-300'}">
                    ${descText}
                </p>
            </div>
        </div>

        <div class="max-h-[400px] overflow-y-auto pr-2 space-y-3 custom-scrollbar">
    `;

    // 2. Build Cards
    report.details.forEach(item => {
        const isOk = item.status === 'OK';
        const borderColor = isOk ? 'border-l-green-500' : 'border-l-red-500';
        const icon = isOk ? '📄' : '📑';

        html += `
        <div class="bg-black/40 rounded-lg border border-white/5 border-l-4 ${borderColor} p-4 transition hover:bg-black/60">
            <div class="flex justify-between items-start mb-2">
                <div class="flex items-center gap-2">
                    <span class="text-xl">${icon}</span>
                    <span class="font-semibold text-gray-200 text-sm">${item.template}</span>
                </div>
                <span class="px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider ${isOk ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}">
                    ${item.status}
                </span>
            </div>
        `;

        // 3. Render Missing Variables
        if (item.missing_vars.length > 0) {
            html += `
            <div class="mt-3 bg-red-900/10 rounded p-3 border border-red-500/10">
                <p class="text-sm text-red-300 mb-2 font-semibold flex items-center gap-1">
                    <span>❌</span> ${i18n.t('alerts.validation_modal.missing_vars')}
                </p>
                <div class="flex flex-wrap gap-2">`;

            item.missing_vars.forEach(v => {
                html += `<span class="font-mono text-sm bg-red-500/20 text-red-200 px-2 py-1 rounded border border-red-500/30">{{ ${v} }}</span>`;
            });

            html += `</div></div>`;
        } else {
            // "variables matched successfully"
            html += `<div class="mt-1 text-sm text-gray-500 flex items-center gap-1">
                <span class="text-green-500">●</span> ${item.matched_vars.length} ${i18n.t('alerts.validation_modal.matched')}
             </div>`;
        }

        html += `</div>`;
    });

    html += `</div></div>`;

    // 4. Launch Modal
    Swal.fire({
        title: `<span class="text-xl font-bold text-gray-100">${i18n.t('alerts.validation_modal.title')}</span>`,
        html: html,
        background: '#0f172a',
        color: '#e2e8f0',
        showCloseButton: true,
        focusConfirm: false,
        confirmButtonText: valid ? i18n.t('alerts.validation_modal.btn_proceed') : i18n.t('alerts.validation_modal.btn_close'),
        confirmButtonColor: valid ? '#10b981' : '#3b82f6',
        customClass: {
            popup: 'glass-panel border border-white/10 shadow-2xl',
            title: 'text-left border-b border-white/10 pb-4',
            htmlContainer: '!m-0 !pt-4 !text-left',
            confirmButton: 'px-6 py-3 rounded-xl text-sm font-bold shadow-lg w-full mt-4'
        },
        width: '650px',
        padding: '2rem'
    });
}

/**
 * Generates a single sample row for testing.
 * Blocks the Batch Process button while generating.
 */
async function generateSample() {
    const params = validateInputs();
    if (!params) return;

    // UI Locking
    toggleLoadingState(true, 'btnSample');
    const btnProcess = document.getElementById('btnProcess');
    btnProcess.disabled = true;
    btnProcess.classList.add('opacity-50', 'cursor-not-allowed');

    logToTerminal(i18n.t('alerts.sample_start'), 'info');

    try {
        const formData = buildFormData(params);
        const response = await fetch(CONFIG.endpoints.sample, { method: 'POST', body: formData });

        if (response.ok) {
            downloadBlob(await response.blob(), "LogicPaper_Sample.zip");
            logToTerminal('✅ Sample generated successfully.', 'success');
            Swal.fire({
                icon: 'success',
                title: i18n.t('alerts.sample_ready_title'),
                text: i18n.t('alerts.sample_ready_text'),
                background: '#1e293b',
                color: '#fff',
                timer: 2000,
                showConfirmButton: false
            });
        } else {
            const err = await response.json();
            throw new Error(err.message || "Server Error");
        }
    } catch (e) {
        logToTerminal(i18n.t('alerts.sample_error', { error: e.message }), 'error');
        Swal.fire({ icon: 'error', title: 'Sample Failed', text: e.message, background: '#1e293b', color: '#fff' });
    } finally {
        // UI Unlocking
        toggleLoadingState(false, 'btnSample');
        btnProcess.disabled = false;
        btnProcess.classList.remove('opacity-50', 'cursor-not-allowed');
    }
}

/**
 * Starts the production batch process.
 * Permanently locks the Sample button during execution.
 */
function startProcessing() {
    const params = validateInputs();
    if (!params) return;

    // Reset Terminal visually
    document.getElementById(CONFIG.dom.terminal).innerHTML = '';
    logToTerminal(i18n.t('alerts.batch_init'), 'info');

    // UI Locking
    toggleLoadingState(true, 'btnProcess');
    const btnSample = document.getElementById('btnSample');
    btnSample.disabled = true;
    btnSample.classList.add('opacity-50', 'cursor-not-allowed');

    isProcessing = true;

    // Connect to SSE
    const evtSource = new EventSource(`/stream-logs/${sessionId}`);

    evtSource.onmessage = (event) => {
        logToTerminal(event.data);

        if (event.data.includes("PROCESS_COMPLETE")) {
            evtSource.close();
            finishBatch(true);
        } else if (event.data.includes("PROCESS_ERROR")) {
            evtSource.close();
            finishBatch(false);
        }
    };

    evtSource.onerror = () => {
        evtSource.close();
        logToTerminal("❌ Connection lost with server.", 'error');
        finishBatch(false);
    };

    // Trigger Backend
    const formData = buildFormData(params);
    fetch(CONFIG.endpoints.process, { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                document.getElementById('mainDownloadBtn').href = data.download_url;
            }
        })
        .catch(e => {
            logToTerminal(`❌ Request Error: ${e.message}`, 'error');
            finishBatch(false);
        });
}

// --- Helpers ---

/**
 * Validates form inputs before submission.
 * @returns {Object|null} Parameters object or null if invalid.
 */
function validateInputs() {
    const fileData = document.getElementById('fileData').files[0];
    const fileTemplates = document.getElementById('fileTemplates').files;
    const fileAssets = document.getElementById('fileAssets').files[0];
    const colName = document.getElementById('colSelect').value;
    const toPdf = document.getElementById('checkPDF').checked;
    const groupFolders = document.getElementById('checkFolders').checked;

    if (fileTemplates.length === 0) {
        Swal.fire({ icon: 'warning', title: i18n.t('alerts.missing_templates.title'), text: i18n.t('alerts.missing_templates.text'), background: '#1e293b', color: '#fff' });
        return null;
    }
    if (!colName || colName === "") {
        Swal.fire({ icon: 'warning', title: i18n.t('alerts.missing_excel.title'), text: i18n.t('dashboard.ingestion.drop_data.sub'), background: '#1e293b', color: '#fff' });
        return null;
    }

    return { fileData, fileTemplates, fileAssets, colName, toPdf, groupFolders };
}

/**
 * Builds the FormData object for the request.
 */
function buildFormData(p) {
    const fd = new FormData();
    fd.append('session_id', sessionId);
    fd.append('filename_col', p.colName);
    fd.append('output_pdf', p.toPdf);
    fd.append('group_by_folders', p.groupFolders);
    appendDataFile(fd, p.fileData);

    for (let i = 0; i < p.fileTemplates.length; i++) fd.append('files_templates', p.fileTemplates[i]);
    if (p.fileAssets) fd.append('file_assets', p.fileAssets);
    return fd;
}

/**
 * Toggles the loading state of buttons.
 */
function toggleLoadingState(isLoading, btnId) {
    const btn = document.getElementById(btnId);
    if (isLoading) {
        btn.dataset.originalText = btn.innerHTML;
        btn.innerHTML = `<span class="animate-pulse">${i18n.t('dashboard.config.btn_processing')}</span>`;
        btn.disabled = true;
        document.querySelectorAll('input, select').forEach(i => i.disabled = true);
        document.querySelectorAll('.drop-zone').forEach(d => d.classList.add('disabled-zone'));
    } else {
        if (btn.dataset.originalText) btn.innerHTML = btn.dataset.originalText;
        btn.disabled = false;
        document.querySelectorAll('input, select').forEach(i => i.disabled = false);
        document.querySelectorAll('.drop-zone').forEach(d => d.classList.remove('disabled-zone'));
    }
}

/**
 * Appends a log message to the terminal.
 * @param {string} msg - The raw message.
 * @param {string} [type] - 'info', 'error', 'success'.
 */
function logToTerminal(msg, type = 'normal') {
    const term = document.getElementById('terminal');
    const p = document.createElement('div');
    p.className = "mb-1 border-l-2 border-transparent pl-2 text-xs font-mono break-all log-entry";

    // Clean message
    const cleanMsg = msg.replace('data:', '').trim();

    if (msg.includes("ERROR") || msg.includes("❌") || type === 'error') {
        p.classList.add('text-red-400', 'border-red-500', 'bg-red-900/10');
    } else if (msg.includes("✅") || type === 'success') {
        p.classList.add('text-green-400', 'border-green-500');
    } else if (msg.includes("---")) {
        p.classList.add('text-blue-400', 'font-bold', 'mt-2');
    } else {
        p.classList.add('text-gray-300');
    }

    p.innerText = cleanMsg;
    term.appendChild(p);
    term.scrollTop = term.scrollHeight;
}

/**
 * Handles batch completion UI logic.
 */
function finishBatch(success) {
    isProcessing = false;
    toggleLoadingState(false, 'btnProcess');

    if (success) {
        document.getElementById('actionPanel').classList.add('hidden');
        const resultPanel = document.getElementById('resultPanel');
        resultPanel.classList.remove('hidden');

        resultPanel.classList.add('animate-pulse');
        setTimeout(() => resultPanel.classList.remove('animate-pulse'), 500);

        logToTerminal(i18n.t('alerts.batch_success'), 'success');
    } else {
        // On failure, re-enable the sample button so user can fix and retry
        const btnSample = document.getElementById('btnSample');
        btnSample.disabled = false;
        btnSample.classList.remove('opacity-50', 'cursor-not-allowed');

        Swal.fire({ icon: 'error', title: i18n.t('alerts.batch_fail_title'), text: i18n.t('alerts.batch_fail_text'), background: '#1e293b', color: '#fff' });
    }

    sessionId = crypto.randomUUID();
}

/**
 * Triggers a browser download from a Blob.
 */
function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
}