from __future__ import annotations

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    snowflake_account_url: str = ""
    snowflake_pat: str = ""
    snowflake_database: str = "CLINICAL_COPILOT"
    snowflake_schema: str = "CORE"
    snowflake_agent_name: str = "CLINICAL_COPILOT_AGENT"
    snowflake_warehouse: str = "COPILOT_WH"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def effective_account_url(self) -> str:
        spcs_host = os.getenv("SNOWFLAKE_HOST")
        if spcs_host:
            return f"https://{spcs_host}"
        return self.snowflake_account_url


settings = Settings()
