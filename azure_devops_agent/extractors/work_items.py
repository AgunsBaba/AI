"""Extract work items from an Azure DevOps project."""

from typing import Any, Dict, List, Optional

from azure.devops.connection import Connection


class WorkItemExtractor:
    """Fetch work items using the Azure DevOps Work Item Tracking API.

    Parameters
    ----------
    connection:
        An authenticated :class:`~azure.devops.connection.Connection`.
    project:
        Default project name used when *project* is not supplied to a method.
    """

    def __init__(self, connection: Connection, project: Optional[str] = None) -> None:
        self._client = connection.clients.get_work_item_tracking_client()
        self._project = project

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def extract_by_query(
        self,
        wiql: str,
        project: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Run a WIQL query and return matching work items as dictionaries.

        Parameters
        ----------
        wiql:
            A WIQL ``SELECT`` statement, e.g.::

                SELECT [System.Id], [System.Title]
                FROM WorkItems
                WHERE [System.TeamProject] = @project

        project:
            Project to scope the query to.  Falls back to the value passed
            to the constructor.
        fields:
            List of field reference names to include in each result.  When
            *None* a sensible default set is used.

        Returns
        -------
        list of dict
            One dictionary per work item containing the requested fields.
        """
        project = project or self._project
        default_fields = [
            "System.Id",
            "System.Title",
            "System.WorkItemType",
            "System.State",
            "System.AssignedTo",
            "System.CreatedDate",
            "System.ChangedDate",
            "System.AreaPath",
            "System.IterationPath",
            "Microsoft.VSTS.Common.Priority",
        ]
        fields = fields or default_fields

        from azure.devops.v7_1.work_item_tracking.models import Wiql

        wiql_obj = Wiql(query=wiql)
        result = self._client.query_by_wiql(wiql_obj, project=project)

        if not result.work_items:
            return []

        ids = [wi.id for wi in result.work_items]
        # Fetch in batches of 200 (API limit).
        items: List[Dict[str, Any]] = []
        for batch_start in range(0, len(ids), 200):
            batch = ids[batch_start : batch_start + 200]
            work_items = self._client.get_work_items(
                ids=batch, fields=fields, error_policy="omit"
            )
            for wi in work_items:
                if wi is None:
                    continue
                row: Dict[str, Any] = {"id": wi.id}
                if wi.fields:
                    row.update(wi.fields)
                items.append(row)

        return items

    def extract_all(
        self,
        project: Optional[str] = None,
        work_item_types: Optional[List[str]] = None,
        state: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Extract all work items from *project* matching optional filters.

        Parameters
        ----------
        project:
            Target project name.  Falls back to the constructor default.
        work_item_types:
            Restrict to specific work item types, e.g. ``["Bug", "Task"]``.
            When *None* all types are returned.
        state:
            Restrict to a single state value, e.g. ``"Active"``.
        fields:
            Passed through to :meth:`extract_by_query`.

        Returns
        -------
        list of dict
        """
        project = project or self._project
        if not project:
            raise ValueError("A project name is required.")

        def _escape(value: str) -> str:
            """Escape single quotes in a WIQL string literal."""
            return value.replace("'", "''")

        conditions = [f"[System.TeamProject] = '{_escape(project)}'"]
        if work_item_types:
            types_str = ", ".join(f"'{_escape(t)}'" for t in work_item_types)
            conditions.append(f"[System.WorkItemType] IN ({types_str})")
        if state:
            conditions.append(f"[System.State] = '{_escape(state)}'")

        where_clause = " AND ".join(conditions)
        wiql = (
            "SELECT [System.Id] FROM WorkItems "
            f"WHERE {where_clause} "
            "ORDER BY [System.ChangedDate] DESC"
        )
        return self.extract_by_query(wiql, project=project, fields=fields)
