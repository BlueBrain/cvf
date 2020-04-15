"""Sample nosetest file."""
from channel_validation_framework import main


def test_add_3_4():
    """Adding 3 and 4."""
    assert main.add(3, 4) == 7


def test_add_0_0():
    """Adding zero to zero."""
    assert main.add(0, 0) == 0
