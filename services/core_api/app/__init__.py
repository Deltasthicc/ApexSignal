"""core_api application package.

`services/evidence_memory` is a sibling library, not an installed
package, so `services/` goes on the import path here. This is the only
cross-directory import Workstream C makes, and it stays inside
Workstream C's own folders -- `services/radio_ai` and `apps/web` are
reached over HTTP/JSON contracts only, never imported.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SERVICES_ROOT = str(Path(__file__).resolve().parents[2])
if _SERVICES_ROOT not in sys.path:
    sys.path.insert(0, _SERVICES_ROOT)
