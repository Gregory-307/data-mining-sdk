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
    from web_search_sdk.scrapers import (
        google_web_top_words,
        wikipedia_top_words,
        related_words,
        google_news_top_words,
        search_and_parse,
        extract_article_content,
    )  # type: ignore
    from web_search_sdk.scrapers.base import ScraperContext  # type: ignore
    print("✅ SDK imported successfully (installed mode)")
except ModuleNotFoundError:
    # Fallback: assume we are being run from the repository root where the
    # code lives in flat folders (scrapers/, utils/, …).  Inject the repo
    # root into sys.path so that ``import scrapers`` resolves.
    REPO_ROOT = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(REPO_ROOT))

    import importlib, types

    # Create a pseudo-package "web_search_sdk" that points to the repo root so
    # that existing relative imports (e.g. ``from ..utils``) keep working.
    pkg = types.ModuleType("web_search_sdk")
    pkg.__path__ = [str(REPO_ROOT)]  # type: ignore[attr-defined]
    sys.modules["web_search_sdk"] = pkg

    # Ensure fully-qualified imports like "from web_search_sdk.scrapers import …" work.
    for _sub in ("scrapers", "utils", "resources"):
        full = f"web_search_sdk.{_sub}"
        mod = importlib.import_module(full)
        sys.modules[full] = mod
        setattr(pkg, _sub, mod)  # type: ignore[arg-type]

    from web_search_sdk.scrapers import (
        google_web_top_words,
        wikipedia_top_words,
        related_words,
        google_news_top_words,
        search_and_parse,
        extract_article_content,
    )  # type: ignore
    from web_search_sdk.scrapers.base import ScraperContext  # type: ignore
    print("✅ SDK imported successfully (development mode)")

async def main(term: str):
    print(f"\n🔍 Testing term: '{term}'")
    print("=" * 50)
    
    ctx = ScraperContext(use_browser=False, debug=False)

    tasks = [
        google_web_top_words(term, ctx=ctx, top_n=10),
        wikipedia_top_words(term, ctx=ctx, top_n=10),
        related_words(term, ctx=ctx),
        google_news_top_words(term, ctx=ctx, top_n=10),
        search_and_parse(term, ctx=ctx, top_n=5),
    ]

    gw, wp, rw, gn, sp = await asyncio.gather(*tasks, return_exceptions=True)

    print("\n📊 SMOKE TEST RESULTS")
    print("=" * 50)
    
    results = {
        "google_web_top_words": gw,
        "wikipedia_top_words": wp,
        "related_words": rw,
        "google_news_top_words": gn,
        "search_and_parse": sp,
    }
    
    for name, result in results.items():
        print(f"\n🔸 {name}:")
        if isinstance(result, Exception):
            print(f"   ❌ Error: {result}")
        else:
            if name == "search_and_parse":
                # Special handling for structured results
                if isinstance(result, dict) and "results" in result:
                    print(f"   ✅ Success: {len(result.get('results', []))} structured results")
                else:
                    print(f"   ✅ Success: {len(result.get('links', []))} links, {len(result.get('tokens', []))} tokens")
            else:
                print(f"   ✅ Success: {result[:5]}{'...' if len(result) > 5 else ''}")
    
    print("\n" + "=" * 50)
    print("✅ Smoke test completed")

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "openai")) 