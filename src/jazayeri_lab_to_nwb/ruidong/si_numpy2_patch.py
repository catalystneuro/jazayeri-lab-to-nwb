"""Runtime patch for a spikeinterface 0.99.1 x numpy-2 incompatibility.

Problem
-------
`BasePhyKilosortSortingExtractor` (spikeinterface/extractors/phykilosortextractors.py)
builds a pandas query as an f-string:

    cluster_info.query(f"cluster_id in {unique_unit_ids}")

When `unique_unit_ids` is a numpy array/list of numpy ints, under numpy >= 2.0
each element stringifies as ``np.int64(1)`` instead of ``1``. The resulting
query string contains the token ``np``, which pandas' expression engine tries
to resolve as a variable and fails with:

    pandas.errors.UndefinedVariableError: name 'np' is not defined

Historically this was worked around by hand-editing site-packages
(``unique_unit_ids = [int(id) for id in clust_id]``). That edit does not travel
with the repo and was lost in the openmind -> ORCD environment migration.

Fix
---
Import this module ONCE, early, before constructing the NWBConverter
(e.g. at the top of main_convert_session.py):

    import si_numpy2_patch  # noqa: F401  (applies the patch on import)

It wraps ``DataFrame.query`` on the extractor so any numpy-int list in the
expression is coerced to plain Python ints. Idempotent and dependency-light.
Safe to leave in permanently: on a spikeinterface build that already renders
plain ints, the wrapper is a no-op.
"""

import re
import functools


def apply_patch():
    try:
        from spikeinterface.extractors import phykilosortextractors as _pk
    except Exception as exc:  # pragma: no cover
        print(f"[si_numpy2_patch] spikeinterface not importable ({exc}); skipping.")
        return False

    cls = _pk.BasePhyKilosortSortingExtractor
    if getattr(cls, "_np2_query_patched", False):
        return True  # already applied

    orig_init = cls.__init__

    @functools.wraps(orig_init)
    def _patched_init(self, *args, **kwargs):
        import pandas as pd

        _real_query = pd.DataFrame.query

        # numpy-2 renders ints as "np.int64(5)"; strip the wrapper in query exprs.
        _np_scalar = re.compile(r"np\.\w+\((-?\d+(?:\.\d+)?)\)")

        def _safe_query(dfself, expr, *a, **kw):
            if isinstance(expr, str) and "np." in expr:
                expr = _np_scalar.sub(r"\1", expr)
            return _real_query(dfself, expr, *a, **kw)

        pd.DataFrame.query = _safe_query
        try:
            return orig_init(self, *args, **kwargs)
        finally:
            pd.DataFrame.query = _real_query  # restore immediately

    cls.__init__ = _patched_init
    cls._np2_query_patched = True
    print("[si_numpy2_patch] applied numpy-2 query fix to "
          "BasePhyKilosortSortingExtractor.")
    return True


# apply on import
apply_patch()
