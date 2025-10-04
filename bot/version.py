"""Bot version information"""

import os
from pathlib import Path


def get_version() -> str:
    """Get bot version from environment, file, or return development version

    Priority:
    1. BOT_VERSION environment variable
    2. /app/VERSION file (Docker container)
    3. VERSION file in project root (local dev)
    4. Fallback to "development"

    Returns:
        str: Bot version string
    """
    # Try environment variable first (set in Docker)
    version = os.getenv("BOT_VERSION")
    if version:
        return version

    # Try /app/VERSION file (Docker container)
    version_file = Path("/app/VERSION")
    if version_file.exists():
        return version_file.read_text().strip()

    # Try VERSION file in project root (local development)
    local_version = Path(__file__).parent.parent / "VERSION"
    if local_version.exists():
        return local_version.read_text().strip()

    # Fallback for development
    return "development"


# Module-level variable for easy import
__version__ = get_version()
