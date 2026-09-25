"""
ASSET Package
=============

Asset management and utility package for the San Guo game.

Package Structure
-----------------
This package serves as the primary asset layer, exporting commonly-used
drawing, font, and lifecycle utilities so that submodules can import
them directly from ``ASSET``::

    from ASSET import draw_gradient_bg, cull_dead, get_font

Exported Symbols
----------------
- **safe_exit** – Gracefully shut down the current module and return to
  the main menu (does not terminate the process).
- **draw_gradient_bg / cull_dead / get_font / logger** – Re-exported
  from :mod:`ASSET.game_data` for convenience.

Notes
-----
- The main menu exit is handled by ``sys.exit(0)`` at the end of
  ``main.py``; ``safe_exit`` only tears down a single module.
- On Android, ``android.exit()`` is called when available.
"""

from __future__ import annotations

import os
import sys
import pygame

from ASSET.game_data import draw_gradient_bg, cull_dead, get_font, logger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ANDROID_ENV_KEY: str = "ANDROID_DATA"

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def safe_exit(
    module_name: str = "模块",
    error: str = "",
) -> None:
    """Safely exit the current module and return to the main menu.

    This function performs a clean teardown of the active sub-module:

    1. Prints an exit notice (and the exception message, if any).
    2. Quits the running ``pygame`` instance and immediately re-initialises
       it so the main menu can continue to operate.
    3. On Android, invokes ``android.exit()`` when the runtime is present.

    After calling this function, the caller should ``return`` so that
    ``run_module()`` can unwind back to the main menu naturally.

    Parameters
    ----------
    module_name:
        Human-readable name of the module being exited.
        Defaults to ``"模块"``.
    error:
        Optional error description to display.  When non-empty the
        message is printed after the exit notice.

    Returns
    -------
    None
        This function does not return a value.  It only performs
        side-effects (console output and pygame lifecycle management).

    Examples
    --------
    >>> safe_exit("地图编辑器", error="文件加载失败")
    ...  # prints exit info, tears down pygame, then caller returns
    """
    print(f"\n【退出】{module_name} 已关闭")
    if error:
        print(f"异常：{error}")

    # --- auto-save before tearing down -------------------------------------
    try:
        from ASSET.game_data import save as _save
        _save()
    except Exception as _e:
        logger.debug(
            "[异常静默] safe_exit save: %s: %s",
            type(_e).__name__,
            _e,
        )

    # --- pygame teardown & re-init ----------------------------------------
    if pygame.get_init():
        try:
            pygame.quit()
        except Exception as _e:
            logger.debug(
                "[异常静默] pygame.quit: %s: %s",
                type(_e).__name__,
                _e,
            )
        # Re-initialise pygame so the main menu can keep using it
        try:
            pygame.init()
        except Exception as _e:
            logger.debug(
                "[异常静默] pygame.init: %s: %s",
                type(_e).__name__,
                _e,
            )

    # --- drop caches holding objects invalidated by pygame.quit() ---------
    # Cached Font/Surface objects cannot be reused after pygame is torn
    # down, otherwise the next module fails with "Invalid font".
    try:
        from ASSET import game_data as _game_data
        _game_data.clear_caches()
    except Exception as _e:
        logger.debug(
            "[异常静默] clear_caches: %s: %s",
            type(_e).__name__,
            _e,
        )

    # --- Android-specific exit --------------------------------------------
    if _ANDROID_ENV_KEY in os.environ:
        try:
            import android
            android.exit()
        except Exception as _e:
            logger.debug(
                "[异常静默] android.exit: %s: %s",
                type(_e).__name__,
                _e,
            )


# ---------------------------------------------------------------------------
# Public exports
# ---------------------------------------------------------------------------

__all__: list[str] = [
    "safe_exit",
    "draw_gradient_bg",
    "cull_dead",
    "get_font",
    "logger",
]
