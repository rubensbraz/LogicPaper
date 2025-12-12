/**
 * Main Application Logic
 * Handles state management, file uploading, and SSE communication.
 */

// --- Global State ---
let sessionId = crypto.randomUUID();
let isProcessing = false;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    initializeDragDrop(['dropExcel', 'dropTemplates', 'dropAssets']);
});

// --- State Management ---

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
    if (type === 'excel') {
        const previewEl = document.getElementById('jsonPreview');
        previewEl.innerText = "Awaiting Excel file...";
        previewEl.className = "absolute inset-0 p-4 text-xs font-mono text-green-400 overflow-auto scrollbar-thin";

        // Lock Config Panel until re-analysis
        document.getElementById('configPanel').classList.add('opacity-50', 'pointer-events-none');
        document.getElementById('colSelect').innerHTML = '<option>Awaiting Excel file...</option>';
    }

    // 3. Add visual separator in logs to indicate new context
    const term = document.getElementById('terminal');
    if (term.innerText.trim() !== "System ready. Waiting for command...") {
        logToTerminal('--- INPUTS CHANGED ---', 'info');
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
 * Triggers state reset and automatic analysis for Excel files.
 * @param {HTMLInputElement} input - The file input element.
 */
function updateUI(input) {
    // ID Convention: fileExcel -> lblExcel
    const labelId = input.id.replace('file', 'lbl');
    const label = document.getElementById(labelId);

    if (input.files && input.files.length > 0) {
        if (input.files.length === 1) {
            label.innerText = input.files[0].name;
        } else {
            label.innerText = `${input.files.length} files selected`;
        }

        // Visual confirmation style
        label.classList.add('text-blue-400', 'font-bold');
        label.classList.remove('text-gray-500');

        // Determine type for state reset
        let type = 'other';

        // Auto-trigger analysis if it is the Excel file
        if (input.id === 'fileExcel') {
            type = 'excel';
            resetStateOnInput(type);
            previewData(); // Auto-execute analysis
        } else {
            resetStateOnInput(type);
        }
    }
}

// --- API Actions ---

/**
 * Analyzes the Excel file and populates the configuration panel.
 */
async function previewData() {
    const fileExcel = document.getElementById('fileExcel').files[0];
    if (!fileExcel) return Swal.fire({ icon: 'error', title: 'Missing Input', text: 'Please upload an Excel file first.', background: '#1e293b', color: '#fff' });

    const formData = new FormData();
    formData.append('file_excel', fileExcel);

    const prevEl = document.getElementById('jsonPreview');
    prevEl.innerText = "Scanning file structure...";
    prevEl.className = "absolute inset-0 p-4 text-xs font-mono text-blue-400 overflow-auto scrollbar-thin animate-pulse";

    try {
        const res = await fetch('/api/preview', { method: 'POST', body: formData });
        const data = await res.json();

        if (data.status === 'success') {
            // Unlock Config
            document.getElementById('configPanel').classList.remove('opacity-50', 'pointer-events-none');

            // Render JSON
            prevEl.className = "absolute inset-0 p-4 text-xs font-mono text-green-400 overflow-auto scrollbar-thin";
            prevEl.innerText = JSON.stringify(data.preview, null, 2);

            // Populate Dropdown
            const sel = document.getElementById('colSelect');
            sel.innerHTML = '<option value="">-- Select Identifier Column --</option>';
            data.headers.forEach(h => {
                let opt = document.createElement('option');
                opt.value = h;
                opt.innerText = h;
                sel.appendChild(opt);
            });
        } else {
            throw new Error(data.message);
        }
    } catch (e) {
        Swal.fire({ icon: 'error', title: 'Analysis Failed', text: e.message, background: '#1e293b', color: '#fff' });
        prevEl.innerText = "Error: " + e.message;
        prevEl.className = "absolute inset-0 p-4 text-xs font-mono text-red-400 overflow-auto scrollbar-thin";
    }
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

    logToTerminal('--- STARTED: SAMPLE GENERATION ---', 'info');

    try {
        const formData = buildFormData(params);
        const response = await fetch(CONFIG.endpoints.sample, { method: 'POST', body: formData });

        if (response.ok) {
            downloadBlob(await response.blob(), "DocGenius_Sample.zip");
            logToTerminal('✅ Sample generated successfully.', 'success');
            Swal.fire({
                icon: 'success', title: 'Sample Ready',
                text: 'Check your downloads folder.',
                background: '#1e293b', color: '#fff', timer: 2000, showConfirmButton: false
            });
        } else {
            const err = await response.json();
            throw new Error(err.message || "Server Error");
        }
    } catch (e) {
        logToTerminal(`❌ Sample Failed: ${e.message}`, 'error');
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
    logToTerminal('--- INITIALIZING BATCH ENGINE ---', 'info');

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
    const fileExcel = document.getElementById('fileExcel').files[0];
    const fileTemplates = document.getElementById('fileTemplates').files;
    const fileAssets = document.getElementById('fileAssets').files[0];
    const colName = document.getElementById('colSelect').value;
    const toPdf = document.getElementById('checkPDF').checked;
    const groupFolders = document.getElementById('checkFolders').checked;

    if (fileTemplates.length === 0) {
        Swal.fire({ icon: 'warning', title: 'No Templates', text: 'Please select templates.', background: '#1e293b', color: '#fff' });
        return null;
    }
    if (!colName || colName === "") {
        Swal.fire({ icon: 'warning', title: 'Configuration Missing', text: 'Please select a column.', background: '#1e293b', color: '#fff' });
        return null;
    }

    return { fileExcel, fileTemplates, fileAssets, colName, toPdf, groupFolders };
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
    fd.append('file_excel', p.fileExcel);
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
        btn.innerHTML = `<span class="animate-pulse">⏳ Processing...</span>`;
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

        logToTerminal("🏁 Batch processing finished successfully.", 'success');
    } else {
        // On failure, re-enable the sample button so user can fix and retry
        const btnSample = document.getElementById('btnSample');
        btnSample.disabled = false;
        btnSample.classList.remove('opacity-50', 'cursor-not-allowed');

        Swal.fire({ icon: 'error', title: 'Batch Failed', text: 'Check logs for details.', background: '#1e293b', color: '#fff' });
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