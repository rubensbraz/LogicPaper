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
    const isDashboard = path === '/' || path === '/index.html';
    const isHelp = path.includes('/help');

    // CSS Classes for states
    const activeClass = "text-blue-400 border-b border-blue-500/50 pb-0.5";
    const inactiveClass = "text-gray-400 hover:text-white transition";

    const navbarHTML = `
    <header class="w-full max-w-7xl flex justify-between items-center mb-8 px-4 md:px-0 select-none">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-gradient-to-tr from-blue-500 to-purple-600 rounded-lg flex items-center justify-center font-bold text-xl shadow-lg shadow-blue-500/20">D</div>
            <div>
                <h1 class="text-2xl font-bold tracking-tight text-gray-100">Doc<span class="text-blue-400">Genius</span></h1>
                <p class="text-[10px] text-gray-400 font-mono tracking-widest uppercase">Batch Processing Engine v1.0</p>
            </div>
        </div>
        
        <nav class="md:flex items-center gap-8 text-sm font-medium">
            <a href="/" class="${isDashboard ? activeClass : inactiveClass} flex items-center gap-2">
                <span>Dashboard</span>
            </a>
            <a href="/help" class="${isHelp ? activeClass : inactiveClass} flex items-center gap-2">
                <span>How to Use</span>
            </a>
        </nav>

        <div class="md:flex text-xs text-gray-200 font-mono items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span> SYSTEM OPERATIONAL
        </div>
    </header>
    `;

    mountPoint.innerHTML = navbarHTML;
}

// Initialize on load
document.addEventListener('DOMContentLoaded', renderNavbar);