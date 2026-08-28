"""Package a checked-in SAP iFlow export directory as a CPI artifact ZIP."""

from pathlib import Path
import argparse
import zipfile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    if not source.is_dir():
        raise SystemExit(f"iFlow source directory not found: {source}")
    files = sorted(
        path for path in source.rglob("*")
        if path.is_file() and path.name.lower() != "readme.md"
    )
    if not files:
        raise SystemExit(f"iFlow source directory is empty: {source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in files:
            bundle.write(path, path.relative_to(source).as_posix())
    print(f"Created {output} from {len(files)} source files")


if __name__ == "__main__":
    main()
