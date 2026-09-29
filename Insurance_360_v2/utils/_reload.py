"""
utils/_reload.py
Pick up edits to the helper modules without restarting the app.

Why this exists
---------------
Streamlit re-executes the entry script (and the active page script) on every
rerun, but modules already present in ``sys.modules`` are NOT re-imported.
So after editing ``utils/theme.py`` the running process keeps the old module
object, and a page doing ``from utils.theme import section`` raises

    ImportError: cannot import name 'section' from 'utils.theme'

even though the name exists on disk.

How it behaves
--------------
* Fresh process: the helper modules are not in ``sys.modules`` yet when this
  runs, so nothing happens - zero cost.
* Process that already imported an older version: each helper is reloaded once,
  which is when caches are still empty, so nothing is lost.
* Normal reruns afterwards: a helper is reloaded only when its file mtime has
  actually changed. Streamlit's ``@st.cache_data`` / ``@st.cache_resource``
  entries therefore survive ordinary reruns and are dropped only on a real
  code change, which is the correct behaviour.

The mtime stamp is stored as an attribute on the target module (not here),
because this module is deliberately re-imported fresh on every run.
"""
import importlib
import os
import sys

# Dependency order matters: rag_agent imports names from data_loader, so
# data_loader must be refreshed first, and rag_agent must follow it.
#
# IMPORTANT: data_loader is EXCLUDED from the reload list because it holds a
# @st.cache_resource connection whose .session() returns a Snowpark Session.
# Reloading the module creates a new @st.cache_resource-decorated function,
# which produces a SECOND Session on next call while the old one is still
# alive — triggering Snowpark error 1409 ("More than one active session").
# Theme and rag_agent are safe to reload (no session creation).
_HELPERS = ("utils.theme", "utils.rag_agent")
_DEPENDS_ON_DATA_LOADER = ()

_STAMP_ATTR = "__source_mtime__"


def _mtime(mod):
    path = getattr(mod, "__file__", None)
    if not path:
        return None
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def refresh_helpers() -> list:
    """Reload stale helper modules. Returns the names that were reloaded."""
    reloaded = []
    force = False

    # Ensure the import system re-reads the directory rather than trusting a
    # cached listing from before the files were redeployed.
    importlib.invalidate_caches()

    for name in _HELPERS:
        mod = sys.modules.get(name)
        if mod is None:
            continue  # not imported yet in this process - nothing to refresh

        now = _mtime(mod)
        if now is None:
            continue

        previous = getattr(mod, _STAMP_ATTR, None)
        # previous is None => first time we have seen this module in this
        # process, and it was imported before we got a chance to stamp it,
        # so we cannot prove it is current. Reload once to be sure.
        stale = previous is None or previous != now
        if name in _DEPENDS_ON_DATA_LOADER and force:
            stale = True

        if not stale:
            continue

        try:
            importlib.reload(mod)
        except Exception:
            # A broken edit should surface as the page's own error, not as an
            # opaque failure in the reload guard.
            continue

        setattr(mod, _STAMP_ATTR, _mtime(mod) or now)
        reloaded.append(name)
        if name == "utils.data_loader":
            force = True

    return reloaded
