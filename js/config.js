/**
 * Application Configuration & Theme Setup
 * Defines global constants and TailwindCSS theme extensions.
 */

// Tailwind Configuration (Applied to CDN)
tailwind.config = {
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
                mono: ['JetBrains Mono', 'monospace'],
            },
            colors: {
                glass: "rgba(255, 255, 255, 0.05)",
                glassBorder: "rgba(255, 255, 255, 0.1)",
                neonBlue: "#3b82f6",
                neonGreen: "#10b981",
                darkBg: "#0B0C15"
            },
            animation: {
                'pulse-fast': 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            },
            keyframes: {
                shimmer: {
                    '100%': { transform: 'translateX(100%)' },
                }
            }
        }
    }
};

/**
 * Global Configuration Object
 * @type {Object}
 */
const CONFIG = {
    env: {
        isGithubPages: window.location.hostname.includes('github.io')
    },
    endpoints: {
        preview: '/api/preview',
        process: '/api/process',
        sample: '/api/sample',
        validate: '/api/validate'
    },
    dom: {
        navbarMount: 'navbar-mount',
        terminal: 'terminal',
        jsonPreview: 'jsonPreview'
    }
};