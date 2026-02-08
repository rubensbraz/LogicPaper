/**
 * @fileoverview Internationalization Handler
 * Manages language switching, persistent storage, and DOM updates.
 */

class I18nHandler {
    constructor() {
        /**
         * @type {string} The current language code ('en' or 'pt').
         * @public
         */
        this.currentLang = localStorage.getItem('logicpaper_lang') || CONFIG.settings?.defaultLocale || 'en';

        /**
         * @type {Object} The translation dictionary.
         * @private
         */
        this.translations = TRANSLATIONS;

        // Initialize immediately if DOM is ready, otherwise wait.
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.updateDOM());
        } else {
            this.updateDOM();
        }
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

        this.updateDOM();
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

        // 1. Try current language
        let value = this._getValue(this.translations[this.currentLang], keys);

        // 2. Fallback to English
        if (!value && this.currentLang !== 'en') {
            console.warn(`[i18n] Missing '${key}' in '${this.currentLang}'. Fallback to 'en'.`);
            value = this._getValue(this.translations['en'], keys);
        }

        // 3. Last Resort: Return key
        if (!value) return key;

        // Interpolation
        return value.replace(/{{(\w+)}}/g, (_, k) => {
            return params[k] !== undefined ? params[k] : `{{${k}}}`;
        });
    }

    /**
     * Helper to traverse object safely.
     * @param {Object} obj 
     * @param {string[]} keys 
     * @returns {*}
     * @private
     */
    _getValue(obj, keys) {
        return keys.reduce((acc, current) => (acc && acc[current] !== undefined) ? acc[current] : undefined, obj);
    }

    /**
     * Updates all HTML elements with the data-i18n attribute.
     */
    updateDOM() {
        // Text Content
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const translation = this.t(key);

            // Safe HTML Injection check
            if (/<[a-z][\s\S]*>/i.test(translation)) {
                el.innerHTML = translation;
            } else {
                el.innerText = translation;
            }
        });

        // Placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            el.placeholder = this.t(key);
        });

        // Attributes (data-i18n-attr="attr:key,attr2:key2")
        document.querySelectorAll('[data-i18n-attr]').forEach(el => {
            const raw = el.getAttribute('data-i18n-attr');
            const pairs = raw.split(',');

            pairs.forEach(pair => {
                const parts = pair.split(':');
                if (parts.length >= 2) {
                    const attr = parts[0].trim();
                    const key = parts.slice(1).join(':').trim();
                    el.setAttribute(attr, this.t(key));
                }
            });
        });
    }
}

// Global Instance
const i18n = new I18nHandler();