# 🚀 DocGenius Project Roadmap & To-Do List

## 1. 🛡️ Security & Production Hardening (Priority: HIGH)
*Currently, the system runs in "Development Mode" and has no access control.*

- [ ] **Remove Development Flags:**
    - Update `docker-compose.yml` and `Dockerfile` to remove `--reload`.
    - Configure `gunicorn` as a process manager with `uvicorn` workers for better stability.
- [ ] **Implement API Security:**
    - Add **API Key Authentication** (X-API-Key header) or Basic Auth to prevent unauthorized usage.
    - Implement **Rate Limiting** (using `slowapi`) to prevent a single user from crashing the LibreOffice workers with 1000 requests/second.
- [ ] **File Validation Guardrails:**
    - Implement strict MIME-type checking (don't trust file extensions).
    - Limit file size uploads (e.g., max 50MB for assets).
    - Add a "Panic Button" or timeout to kill LibreOffice processes that hang longer than 60 seconds (prevents Zombie processes).

## 2. 🧠 Backend Logic Enhancements (Priority: MEDIUM)
*Improving the "Smart Engine".*

- [ ] **Legacy Format Support:**
    - Implement the logic to detect `.doc` files and auto-convert them to `.docx` using LibreOffice *before* the templating engine starts.
- [ ] **Advanced Formatting:**
    - Add support for conditional table rows (dynamic lists inside Word tables).
    - Add support for Rich Text (HTML to Word) injection.

## 3. 📊 Observability & QA (Priority: ONGOING)
*You cannot fix what you cannot see.*

- [ ] **Structured Logging:**
    - Configure Python `logging` to output JSON format (compatible with Datadog/ELK Stack).
- [ ] **Unit & Integration Testing:**
    - Create a `tests/` folder.
    - Write `pytest` cases for:
        - The `DataFormatter` logic (does currency formatting really work for all locales?).
        - The `DocumentEngine` (does it handle missing assets gracefully?).
- [ ] **Health Check Endpoint:**
    - Add `/health` route that checks if LibreOffice is responsive and if the disk has space.