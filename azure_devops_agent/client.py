"""Thin wrapper around the Azure DevOps Python SDK connection."""

from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication


def build_connection(organization_url: str, personal_access_token: str) -> Connection:
    """Return an authenticated :class:`~azure.devops.connection.Connection`.

    Parameters
    ----------
    organization_url:
        Full URL of the Azure DevOps organisation, e.g.
        ``https://dev.azure.com/my-org``.
    personal_access_token:
        A PAT that has been granted the scopes needed by the callers
        (at minimum *vso.work_read*, *vso.build_read*, *vso.code_read*).

    Returns
    -------
    Connection
        An authenticated SDK connection instance.
    """
    credentials = BasicAuthentication("", personal_access_token)
    return Connection(base_url=organization_url, creds=credentials)
