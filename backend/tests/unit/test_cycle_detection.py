import pytest

from src.utils.cycle_detection import has_cycle

pytestmark = pytest.mark.unit


def test_has_cycle_returns_false_for_acyclic_dependency_graph():
    graph = {
        3: [2, 1],
        2: [1],
        1: [],
    }

    assert has_cycle(3, graph) is False


def test_has_cycle_returns_true_for_direct_cycle():
    graph = {
        1: [2],
        2: [1],
    }

    assert has_cycle(1, graph) is True


def test_has_cycle_returns_true_for_indirect_cycle():
    graph = {
        1: [3],
        2: [1],
        3: [2],
    }

    assert has_cycle(1, graph) is True


def test_has_cycle_handles_missing_nodes_as_leaves():
    graph = {
        10: [99],
    }

    assert has_cycle(10, graph) is False
