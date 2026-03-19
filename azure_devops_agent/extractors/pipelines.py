"""Extract release pipeline definitions and deployments from Azure DevOps."""

from typing import Any, Dict, List, Optional

from azure.devops.connection import Connection


class PipelineExtractor:
    """Fetch release pipeline definitions and deployments.

    Parameters
    ----------
    connection:
        An authenticated :class:`~azure.devops.connection.Connection`.
    project:
        Default project name.
    """

    def __init__(self, connection: Connection, project: Optional[str] = None) -> None:
        self._client = connection.clients.get_release_client()
        self._project = project

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def extract_definitions(
        self, project: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return all release pipeline definitions in *project*.

        Parameters
        ----------
        project:
            Target project.

        Returns
        -------
        list of dict
            Each entry contains ``id``, ``name``, ``path``,
            ``created_by``, ``created_on``, and ``modified_on``.
        """
        project = project or self._project
        if not project:
            raise ValueError("A project name is required.")

        definitions = self._client.get_release_definitions(project=project)
        rows = []
        for d in definitions:
            rows.append(
                {
                    "id": d.id,
                    "name": d.name,
                    "path": d.path,
                    "created_by": d.created_by.display_name if d.created_by else None,
                    "created_on": d.created_on,
                    "modified_on": d.modified_on,
                }
            )
        return rows

    def extract_releases(
        self,
        project: Optional[str] = None,
        definition_id: Optional[int] = None,
        top: int = 50,
    ) -> List[Dict[str, Any]]:
        """Return release instances, optionally scoped to one pipeline.

        Parameters
        ----------
        project:
            Target project.
        definition_id:
            Restrict to a specific release definition.
        top:
            Maximum number of releases to fetch.

        Returns
        -------
        list of dict
        """
        project = project or self._project
        if not project:
            raise ValueError("A project name is required.")

        releases = self._client.get_releases(
            project=project,
            definition_id=definition_id,
            top=top,
        )

        rows = []
        for r in releases:
            rows.append(
                {
                    "id": r.id,
                    "name": r.name,
                    "status": str(r.status) if r.status else None,
                    "created_on": r.created_on,
                    "modified_on": r.modified_on,
                    "created_by": r.created_by.display_name if r.created_by else None,
                    "description": r.description,
                    "definition_id": (
                        r.release_definition.id if r.release_definition else None
                    ),
                    "definition_name": (
                        r.release_definition.name if r.release_definition else None
                    ),
                }
            )
        return rows
