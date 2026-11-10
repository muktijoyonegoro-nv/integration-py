"""Script to sync canonical .proto files and compile them into Python bindings."""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Mapping of environment variable names to their compilation configuration
# Format: env_var: (fallback_relative_path, description)
PROTO_ENV_VARS = ["SORT_NODE_PROTO"]
ADDRESSING_PROTO_ENV_VARS = [
    "ADDRESSING_ZONE_EVENT_PROTO",
    "ADDRESSING_ZONE_V4_PROTO",
    "ADDRESSING_FIRST_MILE_ZONE_EVENT_PROTO",
]
ADDRESSING_EXTERNAL_PROTO_ROOT_ENV = "ADDRESSING_PROTO_EXTERNAL_ROOT"


def find_sbt_project_name(proto_file: Path) -> str:
    """Finds the enclosing repo's build.sbt and extracts the project name."""
    curr = proto_file.parent
    while curr != curr.parent:
        sbt_file = curr / "build.sbt"
        if sbt_file.is_file():
            content = sbt_file.read_text(encoding="utf-8")
            # Look for: name := "protos-sort" or name := "..."
            match = re.search(r'name\s*:=\s*"([^"]+)"', content)
            if match:
                return match.group(1)
            # Fallback to repo directory name if name := not found
            return curr.name
        curr = curr.parent
    # Fallback to folder name 4 levels up if build.sbt not found
    return "protos"


def extract_protobuf_relative_path(proto_file: Path) -> Path:
    """Extracts path relative to src/main/protobuf/ or proto/."""
    parts = list(proto_file.parts)
    # Check for src/main/protobuf
    for i in range(len(parts) - 3):
        if parts[i] == "src" and parts[i + 1] == "main" and parts[i + 2] == "protobuf":
            return Path(*parts[i + 3 :])
    # Fallback to file name
    return Path(proto_file.name)


def sanitize_package_name(name: str) -> str:
    """Sanitizes project name to valid Python package identifier (e.g. protos-sort -> protos_sort)."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)


def protobuf_source_root(proto_file: Path) -> Path:
    """Returns the enclosing ``src/main/protobuf`` directory for a schema."""
    parts = list(proto_file.parts)
    for i in range(len(parts) - 3):
        if parts[i : i + 3] == ["src", "main", "protobuf"]:
            return Path(*parts[: i + 3])
    raise ValueError(f"Could not find src/main/protobuf for {proto_file}")


def imported_proto_paths(proto_file: Path) -> list[str]:
    return re.findall(r'^\s*import\s+"([^"]+)"\s*;', proto_file.read_text(encoding="utf-8"), re.MULTILINE)


def sync_proto_closure(
    entry: Path,
    source_roots: list[Path],
    destination_root: Path,
    proto_root: Path,
) -> None:
    """Copies one schema and only the non-Google schemas it transitively imports."""
    visited: set[str] = set()

    def copy_import(import_path: str, source: Path) -> None:
        if import_path.startswith("google/"):
            return
        if import_path in visited:
            return
        visited.add(import_path)
        for source_root in source_roots:
            candidate = source_root / import_path
            if candidate.is_file():
                destination = destination_root / import_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(candidate, destination)
                ensure_init_py(destination.parent, proto_root)
                for nested_import in imported_proto_paths(candidate):
                    copy_import(nested_import, candidate)
                return
        raise FileNotFoundError(f"Unable to resolve import {import_path!r} used by {source}")

    entry_root = next(root for root in source_roots if entry.is_relative_to(root))
    entry_import_path = str(entry.relative_to(entry_root))
    copy_import(entry_import_path, entry)


def ensure_init_py(directory: Path, stop_at: Path) -> None:
    """Creates __init__.py in all directories up to stop_at."""
    curr = directory
    while curr != stop_at and curr.is_relative_to(stop_at):
        init_file = curr / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Generated Protobuf Package."""\n', encoding="utf-8")
        curr = curr.parent
    init_file = stop_at / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""Generated Protobuf Root Package."""\n', encoding="utf-8")


def sync_and_generate() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    proto_root = root_dir / "proto"
    proto_root.mkdir(parents=True, exist_ok=True)
    ensure_init_py(proto_root, proto_root)

    synced_targets: list[tuple[Path, Path]] = []

    for env_var in PROTO_ENV_VARS:
        proto_path_str = os.environ.get(env_var, "").strip()
        if not proto_path_str:
            print(f"ERROR: Environment variable {env_var} is not set in .env", file=sys.stderr)
            print("Please define it pointing to your local repo checkout.", file=sys.stderr)
            sys.exit(1)

        proto_file = Path(os.path.expandvars(proto_path_str)).expanduser().resolve()
        if not proto_file.is_file():
            print(f"ERROR: Proto file not found at: {proto_file} (from {env_var})", file=sys.stderr)
            print("Please ensure the proto repo is checked out locally.", file=sys.stderr)
            sys.exit(1)

        raw_project_name = find_sbt_project_name(proto_file)
        sanitized_project = sanitize_package_name(raw_project_name)
        rel_proto_path = extract_protobuf_relative_path(proto_file)

        dest_file = proto_root / sanitized_project / rel_proto_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        ensure_init_py(dest_file.parent, proto_root)

        print(f"Syncing {env_var}:")
        print(f"  Source:      {proto_file}")
        print(f"  Destination: {dest_file}")
        shutil.copy2(proto_file, dest_file)
        synced_targets.append((dest_file, proto_root / sanitized_project))

    addressing_entries: list[tuple[str, Path]] = []
    for env_var in ADDRESSING_PROTO_ENV_VARS:
        proto_file = Path(os.environ.get(env_var, "").strip()).expanduser().resolve()
        if not proto_file.is_file():
            print(f"ERROR: Environment variable {env_var} must point to a protobuf schema", file=sys.stderr)
            sys.exit(1)
        addressing_entries.append((env_var, proto_file))

    external_root = Path(os.environ.get(ADDRESSING_EXTERNAL_PROTO_ROOT_ENV, "").strip()).expanduser().resolve()
    if not external_root.is_dir():
        print(f"ERROR: {ADDRESSING_EXTERNAL_PROTO_ROOT_ENV} must point to external protobuf dependencies", file=sys.stderr)
        sys.exit(1)

    addressing_project = proto_root / "protos_addressing"
    if addressing_project.exists():
        shutil.rmtree(addressing_project)
    source_roots = [protobuf_source_root(entry) for _, entry in addressing_entries] + [external_root]
    for env_var, entry in addressing_entries:
        print(f"Syncing {env_var}:\n  Source:      {entry}\n  Destination: {addressing_project}")
        sync_proto_closure(entry, source_roots, addressing_project, proto_root)
    synced_targets.extend((proto, addressing_project) for proto in addressing_project.rglob("*.proto"))

    # Compile synced proto files using grpc_tools.protoc
    compiled_projects: set[Path] = set()
    for _, project_root in synced_targets:
        if project_root in compiled_projects:
            continue
        compiled_projects.add(project_root)
        proto_files = sorted(project_root.rglob("*.proto"))
        if not proto_files:
            continue
        print(f"Compiling protobuf project: {project_root.relative_to(root_dir)}...")
        cmd = [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"--proto_path={project_root}",
            f"--python_out={project_root}",
            f"--pyi_out={project_root}",
            *(str(proto) for proto in proto_files),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            print(f"protoc compilation failed for {project_root}:\n{res.stderr}", file=sys.stderr)
            sys.exit(res.returncode)

    print("All protobuf definitions synced and compiled successfully!")


if __name__ == "__main__":
    sync_and_generate()
