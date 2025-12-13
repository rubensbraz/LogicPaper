/**
 * Internationalization Handler.
 * Manages language switching, persistent storage, and DOM updates.
 */
class I18nHandler {
    constructor() {
        this.currentLang = localStorage.getItem('logicpaper_lang') || 'en';
        this.translations = TRANSLATIONS;
        this.init();
    }

    /**
     * Initializes the page language.
     */
    init() {
        this.setLanguage(this.currentLang);
    }

    /**
     * Sets the language and updates the UI.
     * @param {string} lang - 'en' or 'pt'
     */
    setLanguage(lang) {
        if (!this.translations[lang]) {
            console.error(`Language ${lang} not supported.`);
            return;
        }

        this.currentLang = lang;
        localStorage.setItem('logicpaper_lang', lang);

        // Update DOM elements with data-i18n attribute
        this.updateDOM();

        // Dispatch event for other components (like Navbar)
        document.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
    }

    /**
     * Retrieves a translated string by dot-notation key.
     * Supports variable interpolation {{key}}.
     * @param {string} key - The dot notation key (e.g. 'dashboard.title')
     * @param {Object} [params] - Key-value pairs for interpolation
     * @returns {string} The translated string
     */
    t(key, params = {}) {
        const keys = key.split('.');

        // 1. Try to find in current language
        let value = this._getValue(this.translations[this.currentLang], keys);

        // 2. Fallback: Try to find in English if missing
        if (!value && this.currentLang !== 'en') {
            console.warn(`Missing translation for '${key}' in '${this.currentLang}'. Falling back to 'en'.`);
            value = this._getValue(this.translations['en'], keys);
        }

        // 3. Last Resort: Return key name
        if (!value) return key;

        // Handle Interpolation
        return value.replace(/{{(\w+)}}/g, (_, k) => {
            return params[k] !== undefined ? params[k] : `{{${k}}}`;
        });
    }

    // Helper to traverse object safely
    _getValue(obj, keys) {
        return keys.reduce((acc, current) => (acc && acc[current] !== undefined) ? acc[current] : undefined, obj);
    }

    /**
     * Updates all HTML elements with the data-i18n attribute.
     */
    updateDOM() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const translation = this.t(key);

            // Check if translation contains HTML tags
            if (/<[a-z][\s\S]*>/i.test(translation)) {
                el.innerHTML = translation;
            } else {
                el.innerText = translation;
            }
        });

        // Handle placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            el.placeholder = this.t(key);
        });
    }
}

// Global Instance
const i18n = new I18nHandler();