"""Unit-tests for :mod:`geovista.qt`."""
import pytest


def test_import():
    """
    The test environment may or may not contain the "pyvistaqt" package.
    This test only checks that the expected exception is raised when it
    detects that the package is not already available in the test
    environment.

    """
    try:
        import pyvistaqt
    except ImportError:
        pyvistaqt = False

    if not pyvistaqt:
        emsg = 'please install the "pyvistaqt" and "pyqt" packages'
        with pytest.raises(ImportError, match=emsg):
            # pylint: disable-next=import-outside-toplevel
            import geovista.qt  # noqa: F401
