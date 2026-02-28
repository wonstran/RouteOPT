from routeopt.core.config import load_constraints


def test_constraints_example_loads_with_schema():
    c = load_constraints("constraints.example.yaml")
    assert c.depot.lat
    assert c.limits.max_hours_per_night == 4.0
