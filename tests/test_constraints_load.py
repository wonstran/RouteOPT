from pathlib import Path

import yaml


def test_constraints_example_is_valid_yaml():
    p = Path("constraints.example.yaml")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert data["depot"]["lat"]
    assert data["limits"]["max_hours_per_night"] == 4.0
