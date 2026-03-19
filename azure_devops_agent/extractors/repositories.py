"""Extract Git repositories and commits from Azure DevOps."""

from typing import Any, Dict, List, Optional

from azure.devops.connection import Connection


class RepositoryExtractor:
    """Fetch Git repositories and commit history.

    Parameters
    ----------
    connection:
        An authenticated :class:`~azure.devops.connection.Connection`.
    project:
        Default project name.
    """

    def __init__(self, connection: Connection, project: Optional[str] = None) -> None:
        self._client = connection.clients.get_git_client()
        self._project = project

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def extract_repositories(
        self, project: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return all Git repositories in *project*.

        Parameters
        ----------
        project:
            Target project.

        Returns
        -------
        list of dict
            Each entry contains ``id``, ``name``, ``default_branch``,
            ``remote_url``, ``size``, and ``is_disabled``.
        """
        project = project or self._project
        if not project:
            raise ValueError("A project name is required.")

        repos = self._client.get_repositories(project=project)
        rows = []
        for r in repos:
            rows.append(
                {
                    "id": r.id,
                    "name": r.name,
                    "default_branch": r.default_branch,
                    "remote_url": r.remote_url,
                    "size": r.size,
                    "is_disabled": r.is_disabled,
                }
            )
        return rows

    def extract_commits(
        self,
        repository_id: str,
        project: Optional[str] = None,
        branch: str = "main",
        top: int = 100,
    ) -> List[Dict[str, Any]]:
        """Return commits for *repository_id* on *branch*.

        Parameters
        ----------
        repository_id:
            GUID or name of the repository.
        project:
            Target project.
        branch:
            Branch name (without ``refs/heads/`` prefix).
        top:
            Maximum number of commits to return.

        Returns
        -------
        list of dict
        """
        project = project or self._project
        if not project:
            raise ValueError("A project name is required.")

        from azure.devops.v7_1.git.models import GitQueryCommitsCriteria

        criteria = GitQueryCommitsCriteria(item_version={"version": branch})
        commits = self._client.get_commits(
            repository_id=repository_id,
            search_criteria=criteria,
            project=project,
            top=top,
        )

        rows = []
        for c in commits:
            rows.append(
                {
                    "commit_id": c.commit_id,
                    "comment": c.comment,
                    "author_name": c.author.name if c.author else None,
                    "author_email": c.author.email if c.author else None,
                    "author_date": c.author.date if c.author else None,
                    "committer_name": c.committer.name if c.committer else None,
                    "committer_date": c.committer.date if c.committer else None,
                    "url": c.url,
                }
            )
        return rows

    def extract_branches(
        self, repository_id: str, project: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return all branches for *repository_id*.

        Parameters
        ----------
        repository_id:
            GUID or name of the repository.
        project:
            Target project.

        Returns
        -------
        list of dict
        """
        project = project or self._project
        if not project:
            raise ValueError("A project name is required.")

        refs = self._client.get_refs(
            repository_id=repository_id,
            project=project,
            filter="heads/",
        )

        rows = []
        for ref in refs:
            rows.append(
                {
                    "name": ref.name,
                    "object_id": ref.object_id,
                    "creator": ref.creator.display_name if ref.creator else None,
                }
            )
        return rows
