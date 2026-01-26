/**
 * Navbar Component
 * Renders the top navigation bar and highlights the active page.
 */

/**
 * Renders the navigation HTML structure.
 */
function renderNavbar() {
    const mountPoint = document.getElementById('navbar-mount');
    if (!mountPoint) return;

    // Determine active page for styling
    const path = window.location.pathname;
    // Enhanced detection for GitHub Pages subfolder routing
    const isDashboard = path.endsWith("/") || path.endsWith("/index.html");
    const isHelp = path.endsWith("/help.html");

    // CSS Classes for states
    const activeClass = "text-white bg-white/10 px-3 py-2 rounded-lg transition-all w-full md:w-auto text-center";
    const inactiveClass = "text-gray-400 hover:text-white hover:bg-white/5 px-3 py-2 rounded-lg transition-all w-full md:w-auto text-center";

    // --- Dynamic Status Badge Logic ---
    let statusBadgeHTML = '';
    if (CONFIG.env.isGithubPages) {
        // Red Badge for Preview Mode (GitHub Pages)
        statusBadgeHTML = `
            <div class="flex items-center justify-center gap-2 px-3 py-1.5 bg-red-500/10 border border-red-500/20 rounded-full w-fit mx-auto md:mx-0" title="Backend Unavailable">
                <div class="w-2 h-2 bg-red-500 rounded-full"></div>
                <span class="text-xs font-mono text-red-400">${i18n.t('navbar.badge_preview')}</span>
            </div>
        `;
    } else {
        // Green Badge for Operational Mode (Localhost)
        statusBadgeHTML = `
            <div class="flex items-center justify-center gap-2 px-3 py-1.5 bg-green-500/10 border border-green-500/20 rounded-full w-fit mx-auto md:mx-0">
                <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span class="text-xs font-mono text-green-400">${i18n.t('navbar.badge_online')}</span>
            </div>
        `;
    }

    // --- Language Toggle Button ---
    const toggleLangHTML = `
        <button onclick="toggleLanguage()" class="text-gray-400 hover:text-white hover:bg-white/5 px-3 py-2 rounded-lg transition-all w-full md:w-auto text-center flex items-center justify-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
            </svg>
            <span>${i18n.currentLang === 'en' ? i18n.t('navbar.lang_pt') : i18n.t('navbar.lang_en')}</span>
        </button>
    `;

    // --- Navbar ---
    const navbarHTML = `
        <header class="w-full max-w-7xl flex flex-col md:flex-row justify-between items-center mb-8 px-4 md:px-0 select-none gap-6 md:gap-0">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-gradient-to-tr from-blue-500 to-purple-600 rounded-lg flex items-center justify-center font-bold text-xl shadow-lg shadow-blue-500/20">L</div>
                <div>
                    <h1 class="text-2xl font-bold tracking-tight text-gray-100">${i18n.t('navbar.title_main')}<span class="text-blue-400">${i18n.t('navbar.title_sub')}</span></h1>
                    <p class="text-[10px] text-gray-400 font-mono tracking-widest uppercase">${i18n.t('navbar.subtitle')}</p>
                </div>
            </div>
            <nav class="flex flex-col md:flex-row items-center gap-4 w-full md:w-auto">
                <div class="flex flex-col md:flex-row items-center gap-2 md:gap-8 text-sm font-medium w-full md:w-auto">
                    <a href="index.html" class="${isDashboard ? activeClass : inactiveClass} flex items-center justify-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>
                        <span>${i18n.t('navbar.link_dashboard')}</span>
                    </a>
                    <a href="help.html" class="${isHelp ? activeClass : inactiveClass} flex items-center justify-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>
                        <span>${i18n.t('navbar.link_help')}</span>
                    </a>
                    ${toggleLangHTML}
                </div>
                <div class="w-full md:w-auto flex justify-center">
                    ${statusBadgeHTML}
                </div>
            </nav>
        </header>
    `;

    mountPoint.innerHTML = navbarHTML;
}

// Global function for the button
window.toggleLanguage = function () {
    const newLang = i18n.currentLang === 'en' ? 'pt' : 'en';
    i18n.setLanguage(newLang);
    renderNavbar(); // Re-render navbar immediately
};

// Listen for global language changes
document.addEventListener('languageChanged', renderNavbar);
document.addEventListener('DOMContentLoaded', renderNavbar);