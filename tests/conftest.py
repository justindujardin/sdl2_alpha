"""
Pytest configuration for blendy tests.
"""
import pytest


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (may take several seconds)"
    )


@pytest.fixture(scope="session")
def reference_colors():
    """Common color values for testing."""
    return {
        'transparent': (0, 0, 0, 0),
        'opaque_black': (0, 0, 0, 255),
        'opaque_white': (255, 255, 255, 255),
        'opaque_red': (255, 0, 0, 255),
        'opaque_green': (0, 255, 0, 255),
        'opaque_blue': (0, 0, 255, 255),
        'semi_red': (255, 0, 0, 128),
        'semi_white': (255, 255, 255, 128),
        'quarter_black': (0, 0, 0, 64),
    }