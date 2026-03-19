"""Central orchestrator that wires together all extractors and outputs."""

import logging
from typing import Any, Dict, List, Optional

from .client import build_connection
from .config import AgentConfig
from .extractors import (
    BuildExtractor,
    PipelineExtractor,
    RepositoryExtractor,
    TestPlanExtractor,
    WorkItemExtractor,
)
from .output import save

logger = logging.getLogger(__name__)


class AzureDevOpsAgent:
    """High-level agent for extracting data from Azure DevOps.

    Parameters
    ----------
    config:
        An :class:`~azure_devops_agent.config.AgentConfig` instance.  If
        *None* a default instance is constructed (values are read from
        environment variables).

    Examples
    --------
    >>> from azure_devops_agent import AzureDevOpsAgent, AgentConfig
    >>> cfg = AgentConfig(
    ...     organization_url="https://dev.azure.com/my-org",
    ...     personal_access_token="<PAT>",
    ...     project="MyProject",
    ... )
    >>> agent = AzureDevOpsAgent(cfg)
    >>> agent.extract_work_items(state="Active")
    """

    def __init__(self, config: Optional[AgentConfig] = None) -> None:
        self._config = config or AgentConfig()
        self._config.validate()

        self._connection = build_connection(
            self._config.organization_url,
            self._config.personal_access_token,
        )
        logger.info(
            "Connected to Azure DevOps organisation: %s",
            self._config.organization_url,
        )

    # ------------------------------------------------------------------
    # Work items
    # ------------------------------------------------------------------

    def extract_work_items(
        self,
        project: Optional[str] = None,
        work_item_types: Optional[List[str]] = None,
        state: Optional[str] = None,
        fields: Optional[List[str]] = None,
        save_output: bool = True,
    ) -> List[Dict[str, Any]]:
        """Extract work items and optionally persist them to disk.

        Parameters
        ----------
        project:
            Target project.  Falls back to ``config.project``.
        work_item_types:
            Filter by type, e.g. ``["Bug", "User Story"]``.
        state:
            Filter by state, e.g. ``"Active"``.
        fields:
            Work-item field reference names to fetch.
        save_output:
            When ``True`` (default) results are written to
            ``config.output_dir``.

        Returns
        -------
        list of dict
        """
        project = project or self._config.project
        extractor = WorkItemExtractor(self._connection, project=project)
        records = extractor.extract_all(
            project=project,
            work_item_types=work_item_types,
            state=state,
            fields=fields,
        )
        logger.info("Extracted %d work item(s).", len(records))

        if save_output:
            path = save(
                records,
                self._config.output_dir,
                "work_items",
                self._config.output_format,
            )
            logger.info("Work items written to: %s", path)

        return records

    def extract_work_items_by_wiql(
        self,
        wiql: str,
        project: Optional[str] = None,
        fields: Optional[List[str]] = None,
        save_output: bool = True,
    ) -> List[Dict[str, Any]]:
        """Run an arbitrary WIQL query and return the results.

        Parameters
        ----------
        wiql:
            A WIQL ``SELECT`` statement.
        project:
            Target project.
        fields:
            Work-item field reference names to fetch.
        save_output:
            When ``True`` results are persisted to disk.

        Returns
        -------
        list of dict
        """
        project = project or self._config.project
        extractor = WorkItemExtractor(self._connection, project=project)
        records = extractor.extract_by_query(wiql, project=project, fields=fields)
        logger.info("WIQL query returned %d work item(s).", len(records))

        if save_output:
            path = save(
                records,
                self._config.output_dir,
                "work_items_query",
                self._config.output_format,
            )
            logger.info("Query results written to: %s", path)

        return records

    # ------------------------------------------------------------------
    # Builds
    # ------------------------------------------------------------------

    def extract_build_pipelines(
        self, project: Optional[str] = None, save_output: bool = True
    ) -> List[Dict[str, Any]]:
        """Extract build pipeline definitions.

        Parameters
        ----------
        project:
            Target project.
        save_output:
            When ``True`` results are persisted to disk.

        Returns
        -------
        list of dict
        """
        project = project or self._config.project
        extractor = BuildExtractor(self._connection, project=project)
        records = extractor.extract_pipelines(project=project)
        logger.info("Extracted %d build pipeline(s).", len(records))

        if save_output:
            path = save(
                records,
                self._config.output_dir,
                "build_pipelines",
                self._config.output_format,
            )
            logger.info("Build pipelines written to: %s", path)

        return records

    def extract_builds(
        self,
        project: Optional[str] = None,
        definition_ids: Optional[List[int]] = None,
        branch_name: Optional[str] = None,
        max_builds_per_definition: int = 100,
        save_output: bool = True,
    ) -> List[Dict[str, Any]]:
        """Extract build runs.

        Parameters
        ----------
        project:
            Target project.
        definition_ids:
            Restrict to specific pipeline definitions.
        branch_name:
            Filter by source branch.
        max_builds_per_definition:
            Upper limit of builds to return.
        save_output:
            When ``True`` results are persisted to disk.

        Returns
        -------
        list of dict
        """
        project = project or self._config.project
        extractor = BuildExtractor(self._connection, project=project)
        records = extractor.extract_builds(
            project=project,
            definition_ids=definition_ids,
            branch_name=branch_name,
            max_builds_per_definition=max_builds_per_definition,
        )
        logger.info("Extracted %d build(s).", len(records))

        if save_output:
            path = save(
                records,
                self._config.output_dir,
                "builds",
                self._config.output_format,
            )
            logger.info("Builds written to: %s", path)

        return records

    # ------------------------------------------------------------------
    # Release pipelines
    # ------------------------------------------------------------------

    def extract_release_pipelines(
        self, project: Optional[str] = None, save_output: bool = True
    ) -> List[Dict[str, Any]]:
        """Extract release pipeline definitions.

        Parameters
        ----------
        project:
            Target project.
        save_output:
            When ``True`` results are persisted to disk.

        Returns
        -------
        list of dict
        """
        project = project or self._config.project
        extractor = PipelineExtractor(self._connection, project=project)
        records = extractor.extract_definitions(project=project)
        logger.info("Extracted %d release pipeline definition(s).", len(records))

        if save_output:
            path = save(
                records,
                self._config.output_dir,
                "release_pipelines",
                self._config.output_format,
            )
            logger.info("Release pipelines written to: %s", path)

        return records

    def extract_releases(
        self,
        project: Optional[str] = None,
        definition_id: Optional[int] = None,
        top: int = 50,
        save_output: bool = True,
    ) -> List[Dict[str, Any]]:
        """Extract release instances.

        Parameters
        ----------
        project:
            Target project.
        definition_id:
            Restrict to a specific pipeline.
        top:
            Maximum releases to fetch.
        save_output:
            When ``True`` results are persisted to disk.

        Returns
        -------
        list of dict
        """
        project = project or self._config.project
        extractor = PipelineExtractor(self._connection, project=project)
        records = extractor.extract_releases(
            project=project, definition_id=definition_id, top=top
        )
        logger.info("Extracted %d release(s).", len(records))

        if save_output:
            path = save(
                records,
                self._config.output_dir,
                "releases",
                self._config.output_format,
            )
            logger.info("Releases written to: %s", path)

        return records

    # ------------------------------------------------------------------
    # Repositories
    # ------------------------------------------------------------------

    def extract_repositories(
        self, project: Optional[str] = None, save_output: bool = True
    ) -> List[Dict[str, Any]]:
        """Extract all Git repositories in *project*.

        Parameters
        ----------
        project:
            Target project.
        save_output:
            When ``True`` results are persisted to disk.

        Returns
        -------
        list of dict
        """
        project = project or self._config.project
        extractor = RepositoryExtractor(self._connection, project=project)
        records = extractor.extract_repositories(project=project)
        logger.info("Extracted %d repository(-ies).", len(records))

        if save_output:
            path = save(
                records,
                self._config.output_dir,
                "repositories",
                self._config.output_format,
            )
            logger.info("Repositories written to: %s", path)

        return records

    def extract_commits(
        self,
        repository_id: str,
        project: Optional[str] = None,
        branch: str = "main",
        top: int = 100,
        save_output: bool = True,
    ) -> List[Dict[str, Any]]:
        """Extract commits from a repository.

        Parameters
        ----------
        repository_id:
            GUID or name of the repository.
        project:
            Target project.
        branch:
            Source branch name.
        top:
            Maximum number of commits to return.
        save_output:
            When ``True`` results are persisted to disk.

        Returns
        -------
        list of dict
        """
        project = project or self._config.project
        extractor = RepositoryExtractor(self._connection, project=project)
        records = extractor.extract_commits(
            repository_id=repository_id,
            project=project,
            branch=branch,
            top=top,
        )
        logger.info(
            "Extracted %d commit(s) from repository '%s'.", len(records), repository_id
        )

        if save_output:
            safe_name = repository_id.replace("/", "_").replace(" ", "_")
            path = save(
                records,
                self._config.output_dir,
                f"commits_{safe_name}",
                self._config.output_format,
            )
            logger.info("Commits written to: %s", path)

        return records

    # ------------------------------------------------------------------
    # Test plans / runs
    # ------------------------------------------------------------------

    def extract_test_plans(
        self, project: Optional[str] = None, save_output: bool = True
    ) -> List[Dict[str, Any]]:
        """Extract test plans.

        Parameters
        ----------
        project:
            Target project.
        save_output:
            When ``True`` results are persisted to disk.

        Returns
        -------
        list of dict
        """
        project = project or self._config.project
        extractor = TestPlanExtractor(self._connection, project=project)
        records = extractor.extract_plans(project=project)
        logger.info("Extracted %d test plan(s).", len(records))

        if save_output:
            path = save(
                records,
                self._config.output_dir,
                "test_plans",
                self._config.output_format,
            )
            logger.info("Test plans written to: %s", path)

        return records

    def extract_test_runs(
        self,
        project: Optional[str] = None,
        is_automated: Optional[bool] = None,
        save_output: bool = True,
    ) -> List[Dict[str, Any]]:
        """Extract test runs.

        Parameters
        ----------
        project:
            Target project.
        is_automated:
            ``True`` for automated runs, ``False`` for manual, ``None``
            for both.
        save_output:
            When ``True`` results are persisted to disk.

        Returns
        -------
        list of dict
        """
        project = project or self._config.project
        extractor = TestPlanExtractor(self._connection, project=project)
        records = extractor.extract_runs(project=project, is_automated=is_automated)
        logger.info("Extracted %d test run(s).", len(records))

        if save_output:
            path = save(
                records,
                self._config.output_dir,
                "test_runs",
                self._config.output_format,
            )
            logger.info("Test runs written to: %s", path)

        return records

    # ------------------------------------------------------------------
    # Convenience: extract everything
    # ------------------------------------------------------------------

    def extract_all(
        self, project: Optional[str] = None, save_output: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Run all extractors and return a combined result dictionary.

        Parameters
        ----------
        project:
            Target project.
        save_output:
            When ``True`` each dataset is persisted to disk.

        Returns
        -------
        dict
            Keys are dataset names; values are lists of record dicts.
        """
        project = project or self._config.project

        results: Dict[str, List[Dict[str, Any]]] = {}

        steps = [
            ("work_items", self.extract_work_items),
            ("build_pipelines", self.extract_build_pipelines),
            ("builds", self.extract_builds),
            ("release_pipelines", self.extract_release_pipelines),
            ("releases", self.extract_releases),
            ("repositories", self.extract_repositories),
            ("test_plans", self.extract_test_plans),
            ("test_runs", self.extract_test_runs),
        ]

        for name, method in steps:
            try:
                results[name] = method(project=project, save_output=save_output)
            except (ValueError, IOError, RuntimeError) as exc:
                logger.warning("Failed to extract '%s': %s", name, exc)
                results[name] = []
            except Exception as exc:  # catches msrest and azure-devops SDK errors
                logger.warning(
                    "Unexpected error extracting '%s': %s", name, exc, exc_info=True
                )
                results[name] = []

        return results
