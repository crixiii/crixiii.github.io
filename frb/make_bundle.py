"""Packs the frbbeaming package into frbbeaming.zip next to this script.

Usage: python make_bundle.py path/to/frbbeaming
GitHub Pages' Jekyll build skips names that start with an underscore (such as __init__.py),
so the page loads the package from one zip instead of loose files.
"""
import sys
import zipfile
from pathlib import Path

SKIP = {"plotting.py", "validation.py", "__main__.py"}  # matplotlib-only parts are not needed in the browser

src = Path(sys.argv[1] if len(sys.argv) > 1 else "frbbeaming")
out = Path(__file__).with_name("frbbeaming.zip")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(src.glob("*.py")):
        if f.name not in SKIP:
            z.write(f, f"frbbeaming/{f.name}")
print(f"wrote {out} ({out.stat().st_size / 1024:.0f} kB)")
