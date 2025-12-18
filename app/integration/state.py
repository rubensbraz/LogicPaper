from typing import Any, Dict


# In-memory storage for job statuses. In prod, change this for Redis or Database
job_store: Dict[str, Dict[str, Any]] = {}
