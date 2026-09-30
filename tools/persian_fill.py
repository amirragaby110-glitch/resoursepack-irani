#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""persian_fill.py — اجرای مستقل موتور رفع باگ v5 روی پک موجود.

اجرا:  python3 tools/persian_fill.py
گام‌ها: ۱) زره‌ها و پروژکتایل (BUG#2/#3)  ۲) موتور رویه‌ای پُرکن (BUG#4)
موتور اصلی در tools/build_pack.py است (توابع build_armor و procedural_fill).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_pack as bp  # noqa: E402

if __name__ == "__main__":
    bp.build_armor()      # آیکون‌های ۷ متریال + لایه‌های 3D + wind_charge انتیتی
    bp.procedural_fill()  # اسکن رجیستری و پر کردن هر تکسچر غایب با نویز پارسی
    bp.make_zip()         # بازسازی ZIP نهایی
    print("✅ persian_fill کامل شد.")
