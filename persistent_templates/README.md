# 🗄️ Persistent Templates Library

This directory serves as the **central repository** for templates used by the **Headless API** (Integration Layer).

Unlike the Web Dashboard (which requires uploading templates manually for every session), the API expects templates to be pre-loaded in this folder so they can be referenced by path in your JSON requests.

## 🚀 How to Use

1. **Place Files:** Drop your templates here.
2. **Organize:** You can create subfolders (e.g., `contracts/`, `reports/`) to keep things organized.
3. **Reference:** In your API calls, refer to the file path relative to this directory.

## 🔌 API Example

**Scenario:**
You have placed a file structure like this:
`persistent_templates/contracts/service_agreement_v1.docx`

**Request:**
Send the following JSON payload to `POST /api/v1/integration/generate`:

```json
{
  "template_path": "contracts/service_agreement_v1.docx",
  "output_format": "pdf",
  "data": [
    {
      "client_name": "Acme Corp",
      "contract_date": "2024-01-01",
      "amount": 5000.00
    }
  ]
}
```

## 🐳 Docker Volume Info

This directory is mapped as a volume in `docker-compose.yml`. Any file you add, remove, or modify here on your host machine is immediately available inside the running container without needing to restart or rebuild the service.
