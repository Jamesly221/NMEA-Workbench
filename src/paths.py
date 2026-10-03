from pathlib import Path
import sys


def project_root():
    # Packaged releases keep editable resources beside the executable.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]
