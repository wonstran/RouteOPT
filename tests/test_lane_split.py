from routeopt.core.tasks import split_lanes_balanced


def test_split_lanes_balanced_even():
    assert split_lanes_balanced(4) == (2, 2)


def test_split_lanes_balanced_odd():
    assert split_lanes_balanced(5) == (3, 2)
