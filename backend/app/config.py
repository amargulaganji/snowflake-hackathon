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

    @property
    def account_url(self) -> str:
        """The external account URL — needed for Cortex Agent API which
        doesn't work on the internal SPCS host."""
        spcs_host = os.getenv("SNOWFLAKE_HOST")
        if spcs_host:
            # SNOWFLAKE_HOST is like cn78418.ap-southeast-7.aws.snowflakecomputing.com
            # SNOWFLAKE_ACCOUNT is the account locator like omwcxrs-bz26859
            account = os.getenv("SNOWFLAKE_ACCOUNT", "")
            if account:
                return f"https://{account}.snowflakecomputing.com"
            # Fallback: use the SPCS host itself
            return f"https://{spcs_host}"
        return self.snowflake_account_url


settings = Settings()
