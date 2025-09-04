#!/usr/bin/env python3
"""
Version bump script for League Analysis MCP Server.
Keeps pyproject.toml and config/settings.json versions synchronized.
"""

import json
import re
import sys
from pathlib import Path
from typing import Tuple


def get_current_version() -> str:
    """Extract current version from pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found")
    
    content = pyproject_path.read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("Version not found in pyproject.toml")
    
    return match.group(1)


def parse_version(version: str) -> Tuple[int, int, int]:
    """Parse semantic version string into tuple"""
    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version}")
    
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    return (major, minor, patch)


def format_version(major: int, minor: int, patch: int) -> str:
    """Format version tuple back to string"""
    return f"{major}.{minor}.{patch}"


def bump_version(current_version: str, bump_type: str) -> str:
    """Bump version according to type (major, minor, patch)"""
    major, minor, patch = parse_version(current_version)
    
    if bump_type == "major":
        return format_version(major + 1, 0, 0)
    elif bump_type == "minor":
        return format_version(major, minor + 1, 0)
    elif bump_type == "patch":
        return format_version(major, minor, patch + 1)
    else:
        raise ValueError(f"Invalid bump type: {bump_type}. Use: major, minor, patch")


def update_pyproject_version(new_version: str) -> None:
    """Update version in pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    
    updated_content = re.sub(
        r'^version\s*=\s*"[^"]+"',
        f'version = "{new_version}"',
        content,
        flags=re.MULTILINE
    )
    
    pyproject_path.write_text(updated_content)
    print(f"Updated pyproject.toml: version = \"{new_version}\"")


def update_settings_version(new_version: str) -> None:
    """Update version in all settings.json files"""
    settings_files = [
        "config/settings.json",
        "src/league_analysis_mcp_server/config/settings.json"
    ]
    
    for settings_path_str in settings_files:
        settings_path = Path(settings_path_str)
        if not settings_path.exists():
            print(f"Warning: {settings_path_str} not found, skipping")
            continue
        
        with open(settings_path, "r") as f:
            settings = json.load(f)
        
        settings["server"]["version"] = new_version
        
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)
        
        print(f"Updated {settings_path_str}: version = \"{new_version}\"")


def update_release_version(new_version: str) -> None:
    """Update version in RELEASE.md"""
    release_path = Path("RELEASE.md")
    if not release_path.exists():
        print("Warning: RELEASE.md not found, skipping")
        return
    
    content = release_path.read_text(encoding='utf-8')
    
    # Update the current release line
    updated_content = re.sub(
        r'^## Current Release: v[0-9]+\.[0-9]+\.[0-9]+ ✅',
        f'## Current Release: v{new_version} ✅',
        content,
        flags=re.MULTILINE
    )
    
    release_path.write_text(updated_content, encoding='utf-8')
    print(f"Updated RELEASE.md: Current Release = v{new_version}")


def main():
    """Main version bump logic"""
    if len(sys.argv) != 2:
        print("Usage: python bump_version.py <major|minor|patch>")
        print("       python bump_version.py <specific_version>")
        sys.exit(1)
    
    arg = sys.argv[1].lower()
    
    try:
        current_version = get_current_version()
        print(f"Current version: {current_version}")
        
        # Check if argument is a bump type or specific version
        if arg in ["major", "minor", "patch"]:
            new_version = bump_version(current_version, arg)
        else:
            # Validate it's a proper version format
            parse_version(arg)  # This will raise if invalid
            new_version = arg
        
        print(f"New version: {new_version}")
        
        # Update all files
        update_pyproject_version(new_version)
        update_settings_version(new_version)
        update_release_version(new_version)
        
        print(f"\n✅ Version bumped from {current_version} to {new_version}")
        print(f"Next steps:")
        print(f"  1. git add .")
        print(f"  2. git commit -m \"chore: Bump version to {new_version}\"")
        print(f"  3. git tag v{new_version}")
        print(f"  4. git push origin main && git push origin v{new_version}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()