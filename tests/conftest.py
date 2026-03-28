import os
from pathlib import Path
from unittest.mock import patch
import pytest

# Load .env from project root (supports `export KEY=VALUE` syntax)
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        line = line.removeprefix("export ").strip()
        if "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


@pytest.fixture(autouse=True)
def mock_loki(monkeypatch):
    """Prevent tests from requiring a running Loki instance."""
    monkeypatch.setattr(
        "frameworks.langgraph_agents.ecommerce_customer_support.customer_support_agent.log_to_loki",
        lambda *args, **kwargs: None,
    )
