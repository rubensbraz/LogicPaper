# 🚀 DocGenius Project To-Do List

## 1. 🛡️ Security & Production Hardening (Priority: HIGH)

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

## 2. 📊 Observability & QA (Priority: LOW)

- [ ] **Unit & Integration Testing:**
  - Create a `tests/` folder.
  - Write `pytest` cases for:
    - The `DataFormatter` logic (does currency formatting really work for all locales?).
    - The `DocumentEngine` (does it handle missing assets gracefully?).
- [ ] **Health Check Endpoint:**
  - Add `/health` route that checks if LibreOffice is responsive and if the disk has space.
