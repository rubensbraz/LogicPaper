/**
 * Shared Utility Functions
 * Common helpers used across multiple pages.
 */

/**
 * Escapes HTML characters to prevent XSS attacks.
 * @param {string} text - The text to escape
 * @returns {string} The escaped text
 */
function escapeHtml(text) {
    if (!text) return text;
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * Copies text content of an element to clipboard with visual feedback.
 * @param {HTMLElement} element - The element containing text to copy.
 */
function copyToClipboard(element) {
    if (!element) return;

    const text = element.innerText;
    navigator.clipboard.writeText(text).then(() => {
        // Show Toast if exists
        const toast = document.getElementById("toast");
        if (toast) {
            toast.className = "show";
            setTimeout(() => { toast.className = toast.className.replace("show", ""); }, 3000);
        }

        // Visual feedback
        const originalColor = element.style.color;
        const originalBorder = element.style.borderColor;

        element.style.borderColor = "#4ade80"; // green-400
        element.style.color = "#4ade80";

        setTimeout(() => {
            element.style.borderColor = originalBorder;
            element.style.color = originalColor;
        }, 500);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}
