"""Test suite package for explainable-stepup.

Importing this package (which ``python -m unittest tests.unit.<module>``,
``python -m unittest discover`` and ``pytest`` all do before importing any
test module) runs a small Windows compatibility shim, so that
``scikit-learn`` / ``shap`` / ``scipy`` can be imported even on machines
where Windows "Smart App Control" intermittently blocks one of scipy's
compiled extension DLLs.  See ``_ensure_scipy_optimize_importable`` below.
"""

import importlib
import sys
import types


def _ensure_scipy_optimize_importable() -> None:
    """Make ``scipy.optimize`` importable when its ``_trlib`` DLL is blocked.

    On Windows machines running Smart App Control (App Control for Business)
    in enforcement mode, loading ``scipy/optimize/_trlib/_trlib*.pyd`` can
    fail with::

        ImportError: DLL load failed while importing _trlib:
        An Application Control policy has blocked this file.

    The block is based on the file's cloud reputation and can appear
    intermittently.  ``scipy.optimize`` imports ``_trlib`` eagerly (it backs
    the optional ``trust-krylov`` optimizer) even though nothing in this
    project, in scikit-learn, or in shap ever uses that optimizer, so a
    blocked DLL breaks ``import sklearn`` / ``import shap`` and therefore
    every test module.

    If the real extension cannot be loaded, register a stand-in module for
    ``scipy.optimize._trlib`` so the rest of ``scipy.optimize`` (and
    everything built on top of it) imports normally.  The stand-in only
    raises if the ``trust-krylov`` optimizer is actually invoked, which never
    happens in this test suite.
    """
    try:
        import scipy  # noqa: F401 -- fail fast if scipy itself is missing
    except ImportError:
        # scipy is genuinely not installed; do not mask that with a stub.
        return

    try:
        importlib.import_module("scipy.optimize._trlib")
        return  # Real extension loaded fine; nothing to do.
    except ImportError:
        pass

    stub = types.ModuleType("scipy.optimize._trlib")

    def _trust_krylov_unavailable(*_args, **_kwargs):
        raise NotImplementedError(
            "scipy.optimize._trlib could not be loaded on this machine "
            "(blocked by a Windows Application Control policy); the scipy "
            "'trust-krylov' optimizer is unavailable."
        )

    stub.get_trlib_quadratic_subproblem = _trust_krylov_unavailable
    stub.TRLIBQuadraticSubproblem = None
    sys.modules["scipy.optimize._trlib"] = stub


_ensure_scipy_optimize_importable()
