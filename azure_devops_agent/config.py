"""Configuration management for the Azure DevOps agent."""

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class AgentConfig:
    """Configuration for the Azure DevOps extraction agent.

    Attributes:
        organization_url: The URL of the Azure DevOps organization
            (e.g. https://dev.azure.com/my-org).
        personal_access_token: A PAT with read access to the required scopes.
        project: Optional default project name to use when one is not
            explicitly provided to an extractor.
        output_dir: Directory where extracted data files are written.
        output_format: Default serialisation format – ``"json"`` or ``"csv"``.
    """

    organization_url: str = field(
        default_factory=lambda: os.environ.get("AZURE_DEVOPS_ORG_URL", "")
    )
    personal_access_token: str = field(
        default_factory=lambda: os.environ.get("AZURE_DEVOPS_PAT", "")
    )
    project: Optional[str] = field(
        default_factory=lambda: os.environ.get("AZURE_DEVOPS_PROJECT")
    )
    output_dir: str = field(
        default_factory=lambda: os.environ.get("AZURE_DEVOPS_OUTPUT_DIR", "output")
    )
    output_format: str = field(
        default_factory=lambda: os.environ.get("AZURE_DEVOPS_OUTPUT_FORMAT", "json")
    )

    def validate(self) -> None:
        """Raise *ValueError* when required fields are missing."""
        if not self.organization_url:
            raise ValueError(
                "organization_url is required. Set AZURE_DEVOPS_ORG_URL or pass it "
                "directly to AgentConfig."
            )
        if not self.personal_access_token:
            raise ValueError(
                "personal_access_token is required. Set AZURE_DEVOPS_PAT or pass it "
                "directly to AgentConfig."
            )
        if self.output_format not in ("json", "csv"):
            raise ValueError(
                f"output_format must be 'json' or 'csv', got '{self.output_format}'."
            )
