"""Output helpers – serialise extracted records to JSON or CSV."""

import csv
import json
import os
from typing import Any, Dict, List


def save(
    records: List[Dict[str, Any]],
    output_dir: str,
    filename: str,
    fmt: str = "json",
) -> str:
    """Persist *records* to *output_dir*/<*filename*>.<*fmt*>.

    Parameters
    ----------
    records:
        A list of flat dictionaries – each represents one extracted row.
    output_dir:
        Directory that will be created if it does not already exist.
    filename:
        Base file name **without** extension.
    fmt:
        ``"json"`` (default) or ``"csv"``.

    Returns
    -------
    str
        Absolute path of the written file.

    Raises
    ------
    ValueError
        When *fmt* is not ``"json"`` or ``"csv"``.
    """
    if fmt not in ("json", "csv"):
        raise ValueError(f"Unsupported format: '{fmt}'. Use 'json' or 'csv'.")

    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{filename}.{fmt}")

    if fmt == "json":
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(records, fh, indent=2, default=str)
    else:
        if records:
            with open(path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)
        else:
            # Write an empty file so callers always get a path back.
            with open(path, "w", encoding="utf-8"):
                pass

    return os.path.abspath(path)
