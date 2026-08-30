#!/usr/bin/env python3
"""Build the EasyEDA plugin package as a .eext archive."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


def build_plugin(source_dir: Path, output_file: Path) -> None:
    """Create a zip archive containing the source directory contents at the archive root."""
    if not source_dir.exists():
        raise FileNotFoundError(f"Plugin source directory not found: {source_dir}")

    if not source_dir.is_dir():
        raise NotADirectoryError(f"Plugin source path is not a directory: {source_dir}")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_file, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source_dir.rglob("*")):
            if path.is_dir():
                continue
            arcname = path.relative_to(source_dir)
            zf.write(path, arcname.as_posix())

    print(f"Built plugin archive: {output_file}")


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent
    default_source = repo_root / "easyeda_plugin" / "src"
    default_output = repo_root / "easyeda_plugin" / "mcp_plugin.eext"

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=default_source,
        help=f"Directory to compress (default: {default_source})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help=f"Destination .eext archive (default: {default_output})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build_plugin(args.source.resolve(), args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
