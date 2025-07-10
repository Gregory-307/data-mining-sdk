"""Minimal demo

Run it two ways:

1. **Installed wheel / editable mode** – after::

       pip install -e .
       python smoke_test.py "openai"

2. **Directly from a fresh checkout** – without installing anything.  The
   helper below temporarily injects the repository root on ``sys.path`` so
   the local modules (``scrapers/``, ``utils/`` …) are importable under the
   *flat* layout we use inside the repo.
"""

import asyncio, sys, pprint, os, pathlib

# ------------------------------------------------------------
# Import helpers – work both before *and* after ``pip install -e .``
# ------------------------------------------------------------

try:
    # Standard path when the package is installed (editable or wheel)
    from Data_Mining.scrapers import google_web_top_words  # type: ignore
    from Data_Mining.scrapers.base import ScraperContext  # type: ignore
except ModuleNotFoundError:
    # Fallback: assume we are being run from the repository root where the
    # code lives in flat folders (scrapers/, utils/, …).  Inject the repo
    # root into sys.path so that ``import scrapers`` resolves.
    REPO_ROOT = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(REPO_ROOT))

    import importlib, types

    # Create a pseudo-package "Data_Mining" that points to the repo root so
    # that existing relative imports (e.g. ``from ..utils``) keep working.
    pkg = types.ModuleType("Data_Mining")
    pkg.__path__ = [str(REPO_ROOT)]  # type: ignore[attr-defined]
    sys.modules["Data_Mining"] = pkg

    # Ensure fully-qualified imports like "from Data_Mining.scrapers import …" work.
    for _sub in ("scrapers", "utils", "resources"):
        full = f"Data_Mining.{_sub}"
        mod = importlib.import_module(full)
        sys.modules[full] = mod
        setattr(pkg, _sub, mod)  # type: ignore[arg-type]

    from Data_Mining.scrapers import google_web_top_words  # type: ignore
    from Data_Mining.scrapers.base import ScraperContext  # type: ignore

async def main(term: str):
    ctx = ScraperContext(use_browser=True, debug=False)
    words = await google_web_top_words(term, ctx=ctx, top_n=10)
    pprint.pp(words)

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "openai")) 