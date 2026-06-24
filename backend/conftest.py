"""
Root conftest.py — patches applied at session start, cover all tests under backend/.

CountryResolver auto-seed:
  G01 made CountryResolver data-driven (no hardcoded ORG_DEFAULT→pakistan mapping).
  Tests that create services backed by PayrollService / CountryResolver need ORG_DEFAULT
  seeded before use. Patching __init__ here means every CountryResolver() in any test
  automatically gets the dev/test default mappings without each test having to call
  seed_dev_defaults() manually.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.country_resolver import CountryResolver, seed_dev_defaults as _seed

_orig_resolver_init = CountryResolver.__init__


def _auto_seeded_init(self: CountryResolver) -> None:
    _orig_resolver_init(self)
    _seed(self)


CountryResolver.__init__ = _auto_seeded_init  # type: ignore[method-assign]
