/**
 * @fileoverview History page logic for displaying job execution history.
 * Handles loading job data from the backend API and rendering the history table.
 */

/**
 * Loads job history from the backend and renders the table.
 * Fetches data from /api/history endpoint and dynamically generates table rows
 * with status badges, file counts, and download links.
 * 
 * @async
 * @function loadHistory
 * @returns {Promise<void>}
 * 
 * @throws {Error} If the API request fails or returns invalid data
 * 
 * @example
 * // Called automatically on page load or manually via refresh button
 * loadHistory();
 */
window.loadHistory = async function () {
    const tbody = document.getElementById('history-table-body');

    // Show loading state
    tbody.innerHTML = `
        <tr>
            <td colspan="5" class="p-8 text-center text-gray-500 animate-pulse">
                ${i18n.t('history.loading')}
            </td>
        </tr>
    `;

    // Check for Static Mode (GitHub Pages)
    if (typeof CONFIG !== 'undefined' && CONFIG.env && CONFIG.env.isGithubPages) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="p-8 text-center text-gray-400">
                    <div class="flex flex-col items-center gap-2">
                        <span class="text-xl">⚠️</span>
                        <span>${i18n.t('history.static_mode')}</span>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    try {
        const response = await fetch('/api/history');
        const data = await response.json();

        if (!data.history || data.history.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="p-8 text-center text-gray-400">
                        ${i18n.t('history.empty')}
                    </td>
                </tr>
            `;
            return;
        }

        // Render rows
        tbody.innerHTML = data.history.map(job => {
            const date = job.start_time ? new Date(job.start_time).toLocaleString(i18n.currentLang) : i18n.t('history.na');
            const inputFile = escapeHtml(job.input_file || i18n.t('history.na'));
            const filesGenerated = job.files_generated || 0;

            // Status badge
            let statusBadge = '';
            if (job.status === 'completed') {
                statusBadge = `<span class="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-xs font-mono border border-green-500/30">${i18n.t('history.status_completed')}</span>`;
            } else if (job.status === 'failed') {
                statusBadge = `<span class="px-3 py-1 bg-red-500/20 text-red-400 rounded-full text-xs font-mono border border-red-500/30">${i18n.t('history.status_failed')}</span>`;
            } else {
                statusBadge = `<span class="px-3 py-1 bg-yellow-500/20 text-yellow-400 rounded-full text-xs font-mono border border-yellow-500/30 animate-pulse">${i18n.t('history.status_processing')}</span>`;
            }

            // Action button
            let actionButton = '';
            if (job.status === 'completed' && job.download_url) {
                actionButton = `
                    <a href="${escapeHtml(job.download_url)}" 
                       class="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg transition border border-blue-500/30 text-xs font-medium">
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        ${i18n.t('history.btn_download')}
                    </a>
                `;
            } else if (job.status === 'failed') {
                actionButton = `<span class="text-xs text-gray-600">${escapeHtml(job.error || i18n.t('history.error'))}</span>`;
            } else {
                actionButton = `<span class="text-xs text-gray-600">${i18n.t('history.no_action')}</span>`;
            }

            return `
                <tr class="hover:bg-white/5 transition">
                    <td class="p-4 font-mono text-xs text-gray-400">${escapeHtml(date)}</td>
                    <td class="p-4">${inputFile}</td>
                    <td class="p-4">${statusBadge}</td>
                    <td class="p-4 text-center font-mono text-sm">${filesGenerated}</td>
                    <td class="p-4 text-right">${actionButton}</td>
                </tr>
            `;
        }).join('');

    } catch (error) {
        console.error('Failed to load history:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="p-8 text-center text-red-400">
                    ${i18n.t('history.error')}: ${escapeHtml(error.message)}
                </td>
            </tr>
        `;
    }
};

// Auto-load on page load
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
});
