# -*- coding: utf-8 -*-
"""Fon xizmatining kirish nuqtasi (python-for-android shu faylni alohida jarayonda ishga tushiradi)."""
import os
import sys
import traceback

try:
    import selfupdate

    overlay = selfupdate.overlay_dir()
    if os.path.isdir(overlay) and overlay not in sys.path:
        sys.path.insert(0, overlay)       # terminal orqali qilingan o'zgarishlar xizmatda ham amal qilsin
except Exception:
    pass

try:
    from fon import run_service
    run_service()
except Exception:
    try:
        from fon import write_status
        write_status(running=False, state="yiqildi", error=traceback.format_exc()[-400:])
    except Exception:
        pass
    raise
