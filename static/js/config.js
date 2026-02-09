/**
 * @fileoverview Application Configuration & Theme Setup
 * Defines global constants and TailwindCSS theme extensions.
 */

/**
 * Tailwind Configuration (Applied to CDN runtime)
 */
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
 * Frozen to prevent accidental runtime modifications.
 * @type {Readonly<Object>}
 */
const CONFIG = Object.freeze({
    env: {
        isGithubPages: window.IS_STATIC || window.location.hostname.includes('github.io') || window.location.protocol === 'file:'
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
});