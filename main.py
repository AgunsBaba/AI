#!/usr/bin/env python3
"""Command-line interface for the Azure DevOps data extraction agent.

Usage examples
--------------
Extract all work items in a project::

    python main.py work-items --project MyProject

Extract builds for a specific branch::

    python main.py builds --project MyProject --branch refs/heads/main

Extract everything and save to CSV::

    python main.py all --project MyProject --format csv

Run ``python main.py --help`` for full option details.
"""

import argparse
import logging
import sys

from azure_devops_agent import AgentConfig, AzureDevOpsAgent


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="azure-devops-agent",
        description="Extract data from Azure DevOps and save it to JSON or CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Global options
    parser.add_argument(
        "--org-url",
        metavar="URL",
        help=(
            "Azure DevOps organisation URL "
            "(default: AZURE_DEVOPS_ORG_URL env var)."
        ),
    )
    parser.add_argument(
        "--pat",
        metavar="TOKEN",
        help=(
            "Personal Access Token "
            "(default: AZURE_DEVOPS_PAT env var)."
        ),
    )
    parser.add_argument(
        "--project",
        metavar="NAME",
        help=(
            "Default project name "
            "(default: AZURE_DEVOPS_PROJECT env var)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        metavar="DIR",
        default="output",
        help="Directory for output files (default: output).",
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Output format (default: json).",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging verbosity (default: INFO).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # -- work-items ---------------------------------------------------
    wi = subparsers.add_parser("work-items", help="Extract work items.")
    wi.add_argument("--project", dest="project_override", metavar="NAME")
    wi.add_argument(
        "--types",
        nargs="+",
        metavar="TYPE",
        help='Work item types to include, e.g. --types Bug "User Story".',
    )
    wi.add_argument("--state", metavar="STATE", help="Filter by state.")
    wi.add_argument(
        "--wiql",
        metavar="QUERY",
        help="Custom WIQL SELECT statement (overrides --types / --state).",
    )

    # -- builds -------------------------------------------------------
    bd = subparsers.add_parser("builds", help="Extract build pipeline runs.")
    bd.add_argument("--project", dest="project_override", metavar="NAME")
    bd.add_argument(
        "--definition-ids",
        nargs="+",
        type=int,
        metavar="ID",
        help="Restrict to these pipeline definition IDs.",
    )
    bd.add_argument("--branch", metavar="BRANCH", help="Filter by source branch.")
    bd.add_argument(
        "--top",
        type=int,
        default=100,
        help="Maximum builds to fetch (default: 100).",
    )

    # -- build-pipelines ----------------------------------------------
    bp = subparsers.add_parser(
        "build-pipelines", help="Extract build pipeline definitions."
    )
    bp.add_argument("--project", dest="project_override", metavar="NAME")

    # -- release-pipelines --------------------------------------------
    rp = subparsers.add_parser(
        "release-pipelines", help="Extract release pipeline definitions."
    )
    rp.add_argument("--project", dest="project_override", metavar="NAME")

    # -- releases -----------------------------------------------------
    rl = subparsers.add_parser("releases", help="Extract release instances.")
    rl.add_argument("--project", dest="project_override", metavar="NAME")
    rl.add_argument("--definition-id", type=int, metavar="ID")
    rl.add_argument(
        "--top",
        type=int,
        default=50,
        help="Maximum releases to fetch (default: 50).",
    )

    # -- repositories -------------------------------------------------
    repo = subparsers.add_parser("repositories", help="Extract Git repositories.")
    repo.add_argument("--project", dest="project_override", metavar="NAME")

    # -- commits ------------------------------------------------------
    commits = subparsers.add_parser("commits", help="Extract commits from a repository.")
    commits.add_argument("--project", dest="project_override", metavar="NAME")
    commits.add_argument(
        "--repo-id",
        required=True,
        metavar="REPO",
        help="Repository GUID or name.",
    )
    commits.add_argument(
        "--branch",
        default="main",
        help="Branch name (default: main).",
    )
    commits.add_argument(
        "--top",
        type=int,
        default=100,
        help="Maximum commits to fetch (default: 100).",
    )

    # -- test-plans ---------------------------------------------------
    tp = subparsers.add_parser("test-plans", help="Extract test plans.")
    tp.add_argument("--project", dest="project_override", metavar="NAME")

    # -- test-runs ----------------------------------------------------
    tr = subparsers.add_parser("test-runs", help="Extract test runs.")
    tr.add_argument("--project", dest="project_override", metavar="NAME")
    tr.add_argument(
        "--automated",
        choices=["yes", "no", "all"],
        default="all",
        help="Filter automated/manual runs (default: all).",
    )

    # -- all ----------------------------------------------------------
    all_cmd = subparsers.add_parser("all", help="Run all extractors.")
    all_cmd.add_argument("--project", dest="project_override", metavar="NAME")

    return parser


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Build config – CLI flags override env vars.
    config_kwargs = {
        "output_dir": args.output_dir,
        "output_format": args.format,
    }
    if args.org_url:
        config_kwargs["organization_url"] = args.org_url
    if args.pat:
        config_kwargs["personal_access_token"] = args.pat
    if args.project:
        config_kwargs["project"] = args.project

    config = AgentConfig(**config_kwargs)

    # Per-sub-command project override.
    project_override = getattr(args, "project_override", None)
    effective_project = project_override or config.project

    try:
        agent = AzureDevOpsAgent(config)
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    try:
        if args.command == "work-items":
            if args.wiql:
                agent.extract_work_items_by_wiql(
                    wiql=args.wiql, project=effective_project
                )
            else:
                agent.extract_work_items(
                    project=effective_project,
                    work_item_types=args.types,
                    state=args.state,
                )

        elif args.command == "builds":
            agent.extract_builds(
                project=effective_project,
                definition_ids=args.definition_ids,
                branch_name=args.branch,
                max_builds_per_definition=args.top,
            )

        elif args.command == "build-pipelines":
            agent.extract_build_pipelines(project=effective_project)

        elif args.command == "release-pipelines":
            agent.extract_release_pipelines(project=effective_project)

        elif args.command == "releases":
            agent.extract_releases(
                project=effective_project,
                definition_id=args.definition_id,
                top=args.top,
            )

        elif args.command == "repositories":
            agent.extract_repositories(project=effective_project)

        elif args.command == "commits":
            agent.extract_commits(
                repository_id=args.repo_id,
                project=effective_project,
                branch=args.branch,
                top=args.top,
            )

        elif args.command == "test-plans":
            agent.extract_test_plans(project=effective_project)

        elif args.command == "test-runs":
            is_automated = (
                None
                if args.automated == "all"
                else args.automated == "yes"
            )
            agent.extract_test_runs(
                project=effective_project, is_automated=is_automated
            )

        elif args.command == "all":
            agent.extract_all(project=effective_project)

    except (ValueError, IOError, RuntimeError, KeyboardInterrupt) as exc:
        logging.getLogger(__name__).error("Extraction failed: %s", exc, exc_info=True)
        return 1
    except Exception as exc:  # catches msrest.exceptions and azure-devops SDK errors
        logging.getLogger(__name__).error(
            "Unexpected error during extraction: %s", exc, exc_info=True
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
