"""Pytest configuration: ensure the main package is on the path."""

import sys
from pathlib import Path

# Add the package directory so "from intake import ..." and "from talk_to_your_slackbot" work.
root = Path(__file__).resolve().parent.parent
pkg = root / "talk-to-your-slackbot"
if str(pkg) not in sys.path:
    sys.path.insert(0, str(pkg))
