"""Extract build pipeline runs from Azure DevOps."""

from typing import Any, Dict, List, Optional

from azure.devops.connection import Connection


class BuildExtractor:
    """Fetch build pipeline runs using the Azure DevOps Build API.

    Parameters
    ----------
    connection:
        An authenticated :class:`~azure.devops.connection.Connection`.
    project:
        Default project name.
    """

    def __init__(self, connection: Connection, project: Optional[str] = None) -> None:
        self._client = connection.clients.get_build_client()
        self._project = project

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def extract_pipelines(self, project: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all build pipeline definitions in *project*.

        Parameters
        ----------
        project:
            Target project.

        Returns
        -------
        list of dict
            Each entry contains ``id``, ``name``, ``path``, ``type``,
            ``queue_status``, and ``created_date``.
        """
        project = project or self._project
        if not project:
            raise ValueError("A project name is required.")

        definitions = self._client.get_definitions(project=project)
        rows = []
        for d in definitions:
            rows.append(
                {
                    "id": d.id,
                    "name": d.name,
                    "path": d.path,
                    "type": str(d.type) if d.type else None,
                    "queue_status": str(d.queue_status) if d.queue_status else None,
                    "created_date": d.created_date,
                }
            )
        return rows

    def extract_builds(
        self,
        project: Optional[str] = None,
        definition_ids: Optional[List[int]] = None,
        branch_name: Optional[str] = None,
        max_builds_per_definition: int = 100,
    ) -> List[Dict[str, Any]]:
        """Return build runs, optionally filtered by pipeline or branch.

        Parameters
        ----------
        project:
            Target project.
        definition_ids:
            Restrict to these pipeline definition IDs.
        branch_name:
            Filter by source branch, e.g. ``"refs/heads/main"``.
        max_builds_per_definition:
            Upper limit of builds fetched per definition.

        Returns
        -------
        list of dict
        """
        project = project or self._project
        if not project:
            raise ValueError("A project name is required.")

        builds = self._client.get_builds(
            project=project,
            definitions=definition_ids,
            branch_name=branch_name,
            top=max_builds_per_definition,
        )

        rows = []
        for b in builds:
            rows.append(
                {
                    "id": b.id,
                    "build_number": b.build_number,
                    "status": str(b.status) if b.status else None,
                    "result": str(b.result) if b.result else None,
                    "source_branch": b.source_branch,
                    "source_version": b.source_version,
                    "queue_time": b.queue_time,
                    "start_time": b.start_time,
                    "finish_time": b.finish_time,
                    "definition_id": b.definition.id if b.definition else None,
                    "definition_name": b.definition.name if b.definition else None,
                    "requested_by": (
                        b.requested_by.display_name if b.requested_by else None
                    ),
                    "url": b.url,
                }
            )
        return rows
