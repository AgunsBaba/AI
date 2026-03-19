"""Extract test plans and test runs from Azure DevOps."""

from typing import Any, Dict, List, Optional

from azure.devops.connection import Connection


class TestPlanExtractor:
    """Fetch test plans, test suites, and test run results.

    Parameters
    ----------
    connection:
        An authenticated :class:`~azure.devops.connection.Connection`.
    project:
        Default project name.
    """

    def __init__(self, connection: Connection, project: Optional[str] = None) -> None:
        self._client = connection.clients.get_test_client()
        self._project = project

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def extract_plans(self, project: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all test plans in *project*.

        Parameters
        ----------
        project:
            Target project.

        Returns
        -------
        list of dict
        """
        project = project or self._project
        if not project:
            raise ValueError("A project name is required.")

        plans = self._client.get_plans(project=project)
        rows = []
        for p in plans:
            rows.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "state": p.state,
                    "area_path": p.area.name if p.area else None,
                    "iteration": p.iteration,
                    "start_date": p.start_date,
                    "end_date": p.end_date,
                    "owner": p.owner.display_name if p.owner else None,
                    "build_id": p.build.id if p.build else None,
                }
            )
        return rows

    def extract_runs(
        self, project: Optional[str] = None, is_automated: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Return test runs in *project*.

        Parameters
        ----------
        project:
            Target project.
        is_automated:
            When ``True`` only automated runs are returned; ``False`` for
            manual runs; ``None`` for both.

        Returns
        -------
        list of dict
        """
        project = project or self._project
        if not project:
            raise ValueError("A project name is required.")

        runs = self._client.get_runs(project=project, is_automated=is_automated)
        rows = []
        for r in runs:
            rows.append(
                {
                    "id": r.id,
                    "name": r.name,
                    "state": r.state,
                    "is_automated": r.is_automated,
                    "total_tests": r.total_tests,
                    "passed_tests": r.passed_tests,
                    "failed_tests": r.failed_tests,
                    "incomplete_tests": r.incomplete_tests,
                    "not_applicable_tests": r.not_applicable_tests,
                    "started_date": r.started_date,
                    "completed_date": r.completed_date,
                    "build_id": r.build.id if r.build else None,
                    "plan_id": r.plan.id if r.plan else None,
                }
            )
        return rows
