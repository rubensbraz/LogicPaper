/**
 * @fileoverview Clipboard utility for copying code snippets to clipboard.
 * Provides visual feedback via toast notification and element highlighting.
 */

/**
 * Copies the text content of an element to the clipboard.
 * Shows a toast notification and provides visual feedback on the clicked element.
 * 
 * @param {HTMLElement} element - The DOM element containing the text to copy.
 * @returns {void}
 * 
 * @example
 * // HTML: <div onclick="copyToClipboard(this)">{{ variable | filter }}</div>
 * // Clicking the div will copy its text content to clipboard
 */
function copyToClipboard(element) {
    const text = element.innerText;
    navigator.clipboard.writeText(text).then(() => {
        // Show Toast
        const toast = document.getElementById("toast");
        toast.className = "show";
        setTimeout(function () { toast.className = toast.className.replace("show", ""); }, 3000);

        // Visual feedback on element
        const originalBg = element.style.borderColor;
        element.style.borderColor = "#4ade80";
        element.style.color = "#4ade80";
        setTimeout(() => {
            element.style.borderColor = "";
            element.style.color = "";
        }, 500);
    });
}