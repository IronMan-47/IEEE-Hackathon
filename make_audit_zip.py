from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT.parent / "JARVIS_SOURCE_AUDIT.zip"

EXCLUDED_DIRS = {
    "node_modules",
    ".venv",
    ".venv-local",
    "__pycache__",
    ".pytest_cache",
    ".git",
    "dist",
    "release",
    ".jarvis",
    ".mypy_cache",
    ".ruff_cache",
}

EXCLUDED_FILES = {
    "electron-download.zip",
}

def should_exclude(path: Path) -> bool:
    if path.name in EXCLUDED_FILES:
        return True

    return any(part in EXCLUDED_DIRS for part in path.parts)

def main() -> None:
    print(f"Creating: {OUTPUT}")

    files_added = 0

    with zipfile.ZipFile(
        OUTPUT,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as zf:
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue

            if should_exclude(path):
                continue

            relative = path.relative_to(ROOT)
            zf.write(path, relative)
            files_added += 1

    size_mb = OUTPUT.stat().st_size / (1024 * 1024)

    print(f"Files added: {files_added}")
    print(f"ZIP size: {size_mb:.2f} MB")
    print(f"Created: {OUTPUT}")

if __name__ == "__main__":
    main()