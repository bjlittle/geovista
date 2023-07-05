"""Unit-tests for :func:`geovista.gridlines.create_meridian_labels`."""
import pytest

from geovista.gridlines import (
    LABEL_DEGREE,
    LABEL_EAST,
    LABEL_WEST,
    create_meridian_labels,
)


def test_empty():
    """Test nop label generation."""
    result = create_meridian_labels([])
    assert len(result) == 0


@pytest.mark.parametrize(
    "value, expected",
    [
        [-180, f"180{LABEL_DEGREE}"],
        [[-180], f"180{LABEL_DEGREE}"],
        [-90, f"90{LABEL_WEST}"],
        [[-90], f"90{LABEL_WEST}"],
        [0, f"0{LABEL_DEGREE}"],
        [[0], f"0{LABEL_DEGREE}"],
        [90, f"90{LABEL_EAST}"],
        [[90], f"90{LABEL_EAST}"],
        [180, f"180{LABEL_DEGREE}"],
        [[180], f"180{LABEL_DEGREE}"],
    ],
)
def test(value, expected):
    """Test label generation of a meridian."""
    result = create_meridian_labels(value)
    assert result == [expected]


@pytest.mark.parametrize(
    "value, expected",
    [
        [-180.1, f"180{LABEL_DEGREE}"],
        [-90.12, f"90{LABEL_WEST}"],
        [0.123, f"0{LABEL_DEGREE}"],
        [90.1234, f"90{LABEL_EAST}"],
        [180.12345, f"180{LABEL_DEGREE}"],
    ],
)
def test_truncation(value, expected):
    """Test label generation performs value truncation."""
    result = create_meridian_labels(value)
    assert result == [expected]
