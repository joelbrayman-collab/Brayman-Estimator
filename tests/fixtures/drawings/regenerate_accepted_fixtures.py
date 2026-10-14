"""Regenerate the accepted drawing fixtures. Run only when the drawing standard changes
on purpose (bump STANDARD_VERSION first), then review the previews before committing:

    python -m tests.fixtures.drawings.regenerate_accepted_fixtures
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import app.models  # noqa: F401
from app.services.drawings.pdf import render_png
from app.services.drawings.standard import set_signature, standard

HERE = Path(__file__).parent / "pool-deck-synthetic-j1"


def main():
    from PIL import Image

    from tests.test_drawing_engine_deck import _build

    _ds, sheets, _basis, _takeoff = _build()
    HERE.mkdir(parents=True, exist_ok=True)
    (HERE / "standard.json").write_text(json.dumps(standard(), indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    (HERE / "signature.json").write_text(json.dumps(set_signature(sheets), indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    for sh in sheets:
        im = Image.open(io.BytesIO(render_png(sh, dpi=90))).convert("P", palette=Image.ADAPTIVE, colors=64)
        im.save(HERE / f"{sh.number}.png", optimize=True)
    print("written", HERE)


if __name__ == "__main__":
    main()
