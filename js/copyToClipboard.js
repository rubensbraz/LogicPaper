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