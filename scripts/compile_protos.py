#!/usr/bin/env python3
"""
Script to compile protobuf definitions to Python code.

This script uses grpcio-tools to compile the Arrow Flight SQL
protobuf definitions into Python code with proper type stubs.

Requirements:
    - grpcio-tools
    - mypy-protobuf (for .pyi stub generation)

Usage:
    python scripts/compile_protos.py
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Compile protobuf definitions to Python code."""
    # Get project root
    project_root = Path(__file__).parent.parent
    proto_dir = project_root / "proto"
    output_dir = project_root / "src" / "altertable_flightsql" / "generated"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Proto files to compile
    proto_files = [
        proto_dir / "arrow_flight_sql.proto",
    ]

    # Check that proto files exist
    for proto_file in proto_files:
        if not proto_file.exists():
            print(f"Error: Proto file not found: {proto_file}", file=sys.stderr)
            sys.exit(1)

    print("Compiling protobuf definitions...")
    print(f"  Proto directory: {proto_dir}")
    print(f"  Output directory: {output_dir}")
    print()

    # Build the protoc command
    # We use python -m grpc_tools.protoc instead of protoc directly
    # to ensure we use the correct version that matches grpcio
    cmd = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"--proto_path={proto_dir}",
        f"--python_out={output_dir}",
        f"--pyi_out={output_dir}",  # Type stubs for IDE support
    ]

    # Add all proto files
    for proto_file in proto_files:
        cmd.append(str(proto_file))

    print(f"Running: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        print("✓ Successfully compiled protobuf definitions!")
        print()
        print("Generated files:")
        for generated_file in sorted(output_dir.glob("*.py*")):
            print(f"  - {generated_file.relative_to(project_root)}")

    except subprocess.CalledProcessError as e:
        print("✗ Error compiling protobuf definitions:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(
            "✗ Error: grpc_tools.protoc not found. Please install grpcio-tools:",
            file=sys.stderr,
        )
        print("  pip install grpcio-tools mypy-protobuf", file=sys.stderr)
        sys.exit(1)

    # Post-processing: Fix imports in generated files
    print()
    print("Post-processing generated files...")
    fix_imports(output_dir)
    print("✓ Post-processing complete!")


def fix_imports(output_dir: Path):
    """
    Fix imports in generated protobuf files to use relative imports.

    The generated files use absolute imports like:
        import arrow_flight_sql_pb2

    We need to change them to relative imports:
        from . import arrow_flight_sql_pb2
    """
    for py_file in output_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        content = py_file.read_text()
        original_content = content

        # Fix imports for our proto files
        content = content.replace(
            "import arrow_flight_sql_pb2 as",
            "from . import arrow_flight_sql_pb2 as",
        )

        # Only write if changed
        if content != original_content:
            py_file.write_text(content)
            print(f"  Fixed imports in: {py_file.name}")


if __name__ == "__main__":
    main()
