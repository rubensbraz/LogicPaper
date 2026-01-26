# 🤝 Contributing to LogicPaper

First off, thank you for considering contributing to **LogicPaper**! It is people like you who make this engine a powerful tool for everyone.

We aim to keep LogicPaper clean, scalable, and easy to maintain. To help us achieve this, we have put together the following guidelines to help you get started.

---

## 🗺️ Project Roadmap

Before diving in, feel free to check our current strategic goals. If any of these interest you, we would love your help!

### 🧪 Automated Testing Suite

- **Unit Testing:** Implement `pytest` across all formatting strategies to handle edge cases like null values, empty strings, and localized formats.
- **Integration Testing:** Establish end-to-end testing for all FastAPI endpoints using `TestClient` to ensure API stability.

### 🔐 Security & Multi-Tenancy

- **Authentication Layer:** Implement robust User Authentication (JWT/OAuth2) with the ability to enforce mandatory login for all system features.
- **Data Isolation (Multi-Tenancy):** Create logical separation of data so users can only access their own generated documents and templates.
- **Advanced API Management:** Develop scoped API keys with expiration dates, usage quotas, and permission levels for external integrations.

### 📊 Persistence (PostgreSQL) & Analytics

- **Job History:** Enable users to view, audit, and re-download past document generations.
- **Metrics & Statistics:** Store and display template usage statistics, processing times, and success rates per user or API key.

---

## 🏗️ Architectural Philosophy

LogicPaper strives to follow the principles of **Hexagonal Architecture** (Ports and Adapters). The goal is to keep our "Core" (business logic) independent of external technologies (like the API or Database).

- **Core (`app/core`):** This is the heart of the engine. It shouldn't know about the Web or the Database.
- **Strategies (`app/core/strategies`):** Specialized modules for data transformation.
- **Integration (`app/integration`):** Where the engine connects to the real world (FastAPI, Redis, File System).

**Don't worry if you aren't an expert in this architecture!** If your contribution adds value, we will happily work together during the Code Review to help align the code with these patterns.

---

## 🛠️ Best Practices for Pull Requests

To help us review and merge your work quickly, we encourage you to follow these steps:

1. **Focused Scope:** Keep PRs small and focused. It is much easier to review a bug fix and a new feature if they are in separate PRs.
2. **Testing:** We highly encourage including `pytest` files for any new strategy or feature.
3. **Documentation:** If you add a new filter or function, please update the `help.html` and `README.md` so users know how to use it!
4. **Style:** Keep code clean, use meaningful variable names, and provide comments in English.
5. **Template Syntax:** If your change affects how users write tags in Word/Excel, please open an Issue for discussion first to avoid breaking existing templates.

---

## 🚀 Getting Started

We are open to contributions of all kinds! To get started:

1. **Pick an issue:** Explore the roadmap above for inspiration. Have a different idea? Feel free to contribute in any way you'd like, we value all creative input!
2. **Fork the repo:** Create a branch for your specific feature or fix.
3. **Submit your PR:** Describe what you changed and what you tested. We’ll review it as soon as possible!
