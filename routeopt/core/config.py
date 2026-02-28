from __future__ import annotations

from pathlib import Path

import yaml

from routeopt.models.constraints import Constraints


def load_constraints(path: str | Path) -> Constraints:
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return Constraints.model_validate(data)
