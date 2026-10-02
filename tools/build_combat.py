#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SHAMSHIR — Persian Combat Pack builder (MC Java 1.21.11, 16x/32x).

پک مستقل: مدرن، مینیمال، Competitive با هویت یکپارچه‌ی ایرانی.
فلسفه: پایه‌ی 16x وانیلا + «هارمونایز» پالت پارسی (حس ماینکرفت حفظ شود)
+ بازطراحی 32x آیتم‌های کلیدی PvP + GUI شنی/طلایی + HUD فیروزه.
"""
import json
import os
import shutil
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_pack as bp  # noqa: E402  (موتور مشترک)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "PersianCombat")
AS = os.path.join(PACK, "assets", "minecraft")
TEX = os.path.join(AS, "textures")
VAN = "/tmp/mc121/assets/minecraft/textures"
LEGACY = os.path.join(ROOT, "PersianLegacy", "assets", "minecraft")
RELEASE = os.path.join(ROOT, "release")

# پالت رسمی پک (docs/persian-combat-spec.md)
TURQ = (64, 224, 208)
LAPIS = (38, 70, 150)
GOLD = (224, 182, 70)
RED = (196, 60, 54)
SAND = (224, 211, 186)
SLATE = (46, 48, 56)

# لنگرهای Hue (درجه): قرمز، شنی/طلا، سبز حفظ‌شده، فیروزه، لاجورد، بنفش
HUE_ANCHORS = np.array([0, 38, 55, 110, 150, 178, 215, 268, 330, 360],
                       dtype=np.float32)
PULL = 0.38          # قدرت کشش به لنگر


def ensure(p):
    os.makedirs(p, exist_ok=True)


def harmonize(img):
    """هارمونایز پالت: Hue به نزدیک‌ترین لنگر پارسی کشیده می‌شود؛
    اشباع +۸٪، کنتراست ملایم — بافت وانیلا دست نمی‌خورد."""
    img = img.convert("RGBA")
    arr = np.asarray(img)
    hsv = np.asarray(Image.fromarray(arr[..., :3], "RGB").convert("HSV")
                     ).astype(np.float32).copy()
    h = hsv[..., 0] * (360.0 / 255.0)
    d = h[..., None] - HUE_ANCHORS[None, None, :]
    d = (d + 180) % 360 - 180
    idx = np.abs(d).argmin(axis=-1)
    nearest = np.take_along_axis(d, idx[..., None], axis=-1)[..., 0]
    h = (h - nearest * PULL) % 360
    hsv[..., 0] = h * (255.0 / 360.0)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.08, 0, 255)
    v = hsv[..., 2] / 255.0
    hsv[..., 2] = np.clip(((v - .5) * 1.05 + .5) * 255, 0, 255)
    rgb = Image.fromarray(hsv.astype(np.uint8), "HSV").convert("RGB")
    return Image.fromarray(np.dstack([np.asarray(rgb), arr[..., 3]]), "RGBA")


def step_base():
    """پایه: کل تکسچرهای 1.21.11 در 16x + هارمونایز پارسی."""
    skip_top = {"gui", "font", "colormap"}
    n = 0
    for dp, _, fs in os.walk(VAN):
        rel_dir = os.path.relpath(dp, VAN).replace(os.sep, "/")
        if rel_dir.split("/")[0] in skip_top:
            continue
        for f in fs:
            if not f.endswith(".png"):
                continue
            rel = (rel_dir + "/" + f) if rel_dir != "." else f
            dst = os.path.join(TEX, rel)
            ensure(os.path.dirname(dst))
            harmonize(Image.open(os.path.join(dp, f))).save(dst,
                                                            optimize=True)
            meta = os.path.join(dp, f + ".mcmeta")
            if os.path.exists(meta):
                shutil.copy2(meta, dst + ".mcmeta")
            n += 1
    # جلای انچنت: فیروزه
    for g in ("enchanted_glint_item", "enchanted_glint_entity"):
        p = os.path.join(TEX, "misc", g + ".png")
        if os.path.exists(p):
            bp.adjust(Image.open(p), tint=TURQ).save(p, optimize=True)
    print(f"[1] پایه: {n} تکسچر 16x هارمونایزشده ✔")


def _pixelize(canvas, npx, ncol, sat=1.2, val=1.1):
    pp = canvas.resize((npx, npx), Image.BOX)
    aa = np.asarray(pp).copy()
    aa[..., 3] = np.where(aa[..., 3] > 110, 255, 0)
    rr = Image.fromarray(aa[..., :3], "RGB")
    rr = ImageEnhance.Color(rr).enhance(sat)
    rr = ImageEnhance.Brightness(rr).enhance(val)
    rr = ImageEnhance.Contrast(rr).enhance(1.12)
    rr = rr.quantize(colors=ncol, dither=Image.NONE).convert("RGB")
    return Image.fromarray(np.dstack([np.asarray(rr), aa[..., 3]]), "RGBA")


def _ai_item(src_name, out, npx=32, ncol=22, ops=None):
    sp = os.path.join(bp.SRC, "item", src_name + ".png")
    if not os.path.exists(sp):
        return False
    im = bp.chroma_key(Image.open(sp), key="magenta")
    b = im.getbbox()
    if b:
        im = im.crop(b)
    s = max(im.size)
    cv = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    cv.paste(im, ((s - im.width) // 2, (s - im.height) // 2), im)
    px = _pixelize(cv, npx, ncol)
    if ops:
        px = bp.adjust(px, **ops)
    px.save(os.path.join(TEX, "item", out + ".png"), optimize=True)
    return True


SWORD_TINTS = {          # شمشیرِ شمشیر 32x برای هر ۶ متریال
    "wooden_sword": dict(tint=(164, 116, 72)),
    "stone_sword": dict(tint=(142, 142, 148)),
    "iron_sword": None,
    "golden_sword": dict(tint=(238, 190, 70)),
    "diamond_sword": dict(tint=(96, 222, 206)),
    "netherite_sword": dict(tint=(96, 80, 92)),
}


def step_pvp_items():
    """آیتم‌های کلیدی PvP در 32x — خوانا، جمع‌وجور، یکپارچه."""
    n = 0
    for tgt, ops in SWORD_TINTS.items():
        if _ai_item("shamshir_pixel2", tgt, 32, 22, ops):
            n += 1
    _ai_item("mace", "mace", 32, 22)
    n += 1
    # توتم فروهر (از هنر Legacy) — کوچک و نیمه‌شفاف
    tp = os.path.join(LEGACY, "textures", "item", "totem_of_undying.png")
    if os.path.exists(tp):
        t = Image.open(tp).convert("RGBA")
        px = _pixelize(t, 32, 24)
        a = np.asarray(px).astype(np.float32)
        a[..., 3] *= 0.8
        Image.fromarray(a.astype(np.uint8), "RGBA").save(
            os.path.join(TEX, "item", "totem_of_undying.png"), optimize=True)
        n += 1
    # اندرپرل = گوی فیروزه‌ی بادگیر
    wp = os.path.join(bp.SRC, "entity", "wind_charge_v2.png")
    if os.path.exists(wp):
        w = ImageOps.fit(Image.open(wp).convert("RGB"), (256, 256),
                         Image.LANCZOS)
        aa = np.asarray(w).astype(np.float32)
        al = np.clip(aa.max(axis=2) * 1.6, 0, 255)
        orb = Image.fromarray(
            np.dstack([aa.astype(np.uint8), al.astype(np.uint8)]), "RGBA")
        _px = _pixelize(orb, 16, 14)
        _px.save(os.path.join(TEX, "item", "ender_pearl.png"), optimize=True)
        n += 1
    # معجون‌های کیمیاگری (16x از Lite)
    lsrc = os.path.join(ROOT, "PersianLegacyLite", "assets", "minecraft",
                        "textures", "item")
    for f in ("potion", "splash_potion", "lingering_potion",
              "potion_overlay", "glass_bottle", "honey_bottle",
              "experience_bottle", "dragon_breath"):
        p = os.path.join(lsrc, f + ".png")
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(TEX, "item", f + ".png"))
            n += 1
    # سیب طلایی متمایز + انچنتد با هاله‌ی فیروزه
    gp = os.path.join(TEX, "item", "golden_apple.png")
    if os.path.exists(gp):
        g = bp.adjust(Image.open(gp), sat=1.45, val=1.12)
        g.save(gp, optimize=True)
        a = np.asarray(g).copy()
        m = a[..., 3] > 0
        halo = (~m & (np.roll(m, 1, 0) | np.roll(m, -1, 0) |
                      np.roll(m, 1, 1) | np.roll(m, -1, 1)))
        a[halo] = TURQ + (210,)
        Image.fromarray(a, "RGBA").save(
            os.path.join(TEX, "item", "enchanted_golden_apple.png"),
            optimize=True)
        n += 2
    # کمان/پیکان حین استفاده (گرم و واضح)
    for t in ("bow", "bow_pulling_0", "bow_pulling_1", "bow_pulling_2",
              "arrow", "spectral_arrow", "tipped_arrow_base",
              "fishing_rod", "fishing_rod_cast", "shield"):
        p = os.path.join(TEX, "item", t + ".png")
        if os.path.exists(p):
            bp.adjust(Image.open(p), sat=1.25, val=1.05).save(p,
                                                              optimize=True)
            n += 1
    print(f"[2] آیتم‌های PvP: {n} تکسچر 32x/16x ✔")


def step_blocks():
    """بلاک‌های Survival/PvP: کاشی شاه‌عباسی، خاتم، اورهای پارسی 16x."""
    blk = os.path.join(TEX, "block")
    n = 0
    # ۶ کاشی لعاب‌دار (از منبع AI، پیکسلی 16)
    sp = os.path.join(bp.SRC, "block", "shah_abbasi_tile.png")
    if os.path.exists(sp):
        tb = ImageOps.fit(Image.open(sp).convert("RGB"), (256, 256),
                          Image.LANCZOS)
        tb = bp.make_seamless(tb)
        for tgt, ops in bp.TILE_FAMILY.items():
            tv = bp.adjust(tb, **ops) if ops else tb.convert("RGBA")
            px = tv.convert("RGB").resize((16, 16), Image.BOX)
            px = px.quantize(colors=16, dither=Image.NONE).convert("RGBA")
            px.save(os.path.join(blk, tgt + ".png"), optimize=True)
            n += 1
    # میز خاتم‌کاری + نوت‌بلاک (پیکسلی از AI)
    for src_n, tgts in (("crafting_table_top", ["crafting_table_top"]),
                        ("khatam_wood", ["note_block", "jukebox_side"])):
        p = os.path.join(bp.SRC, "block", src_n + ".png")
        if not os.path.exists(p):
            continue
        im = ImageOps.fit(Image.open(p).convert("RGB"), (128, 128),
                          Image.LANCZOS)
        im = bp.make_seamless(im).resize((16, 16), Image.BOX)
        im = im.quantize(colors=20, dither=Image.NONE).convert("RGBA")
        for t in tgts:
            im.save(os.path.join(blk, t + ".png"), optimize=True)
            n += 1
    # اورها: نسخه‌ی پارسی Legacy → 16x پیکسلی (رگه‌های پررنگ خوانا)
    lblk = os.path.join(LEGACY, "textures", "block")
    ores = ["coal_ore", "iron_ore", "copper_ore", "gold_ore",
            "redstone_ore", "emerald_ore", "lapis_ore", "diamond_ore"]
    for o in ores:
        p = os.path.join(lblk, o + ".png")
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB").resize((16, 16), Image.BOX)
        im = ImageEnhance.Color(im).enhance(1.35)
        im = im.quantize(colors=24, dither=Image.NONE).convert("RGBA")
        im.save(os.path.join(blk, o + ".png"), optimize=True)
        dark = bp.adjust(im, sat=1.05, val=0.5)
        dark.save(os.path.join(blk, "deepslate_" + o + ".png"),
                  optimize=True)
        n += 2
    # لو-فایر + آب زلال + گدازه خوانا
    for fn in ("fire_0", "fire_1", "soul_fire_0", "soul_fire_1"):
        p = os.path.join(blk, fn + ".png")
        if os.path.exists(p):
            bp._lite_shorten_fire(p)
            n += 1
    for fn in ("water_still", "water_flow"):
        p = os.path.join(blk, fn + ".png")
        if os.path.exists(p):
            im = Image.open(p).convert("RGBA")
            a = np.asarray(im).astype(np.float32)
            a[..., 3] *= 0.62
            Image.fromarray(a.astype(np.uint8), "RGBA").save(p,
                                                             optimize=True)
            n += 1
    for fn in ("lava_still", "lava_flow"):
        p = os.path.join(blk, fn + ".png")
        if os.path.exists(p):
            bp.adjust(Image.open(p), sat=1.2, val=1.08).save(p,
                                                             optimize=True)
            n += 1
    print(f"[3] بلاک‌ها: {n} تکسچر ✔")


GUI_MAP = [((250, 256), (247, 241, 229)), ((180, 250), (225, 212, 187)),
           ((120, 180), (173, 155, 122)), ((60, 120), (97, 80, 50))]


def _gui_recolor(img):
    """GUI وانیلا => شنی/طلایی پارسی (فقط خاکستری‌ها؛ لی‌اوت دست‌نخورده)."""
    arr = np.asarray(img.convert("RGBA")).copy()
    r, g, b2 = (arr[..., i].astype(np.int16) for i in range(3))
    grayish = ((np.abs(r - g) < 14) & (np.abs(g - b2) < 14) &
               (arr[..., 3] > 0))
    lum = (r + g + b2) // 3
    for (lo, hi), col in GUI_MAP:
        m = grayish & (lum >= lo) & (lum < hi)
        arr[m, 0], arr[m, 1], arr[m, 2] = col
    return Image.fromarray(arr, "RGBA")


def step_gui():
    """GUI کامل: کانتینرها + دکمه‌ها + HUD + هات‌بار خاتم."""
    n = 0
    for sub in ("gui/container", "gui/sprites/widget",
                "gui/sprites/container", "gui"):
        vdir = os.path.join(VAN, sub)
        if not os.path.isdir(vdir):
            continue
        for dp, _, fs in os.walk(vdir):
            for f in fs:
                if not f.endswith(".png"):
                    continue
                rel = os.path.relpath(os.path.join(dp, f), VAN)
                dst = os.path.join(TEX, rel)
                if os.path.exists(dst):
                    continue
                ensure(os.path.dirname(dst))
                _gui_recolor(Image.open(os.path.join(dp, f))).save(
                    dst, optimize=True)
                meta = os.path.join(dp, f + ".mcmeta")
                if os.path.exists(meta):
                    shutil.copy2(meta, dst + ".mcmeta")
                n += 1
    # HUD فیروزه (موتور v13) + هات‌بار خاتم (v9) با override
    old_tex, old_pack = bp.TEX, bp.PACK
    bp.TEX, bp.PACK = TEX, PACK
    ensure(os.path.join(PACK, "assets", "minecraft", "models", "item"))
    ensure(os.path.join(AS, "lang"))
    try:
        bp.build_hud_sprites()
        blank = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
        ensure(os.path.join(TEX, "gui"))
        blank.save(os.path.join(TEX, "gui", "widgets.png"))
        bp.build_hotbar_v9()
        widgets = Image.open(os.path.join(TEX, "gui", "widgets.png"))
        sc = widgets.width // 256
        hud = os.path.join(TEX, "gui", "sprites", "hud")
        for name, (x, y, w, h) in bp.LITE_SPRITES_WIDGETS.items():
            crop = widgets.crop((x * sc, y * sc, (x + w) * sc,
                                 (y + h) * sc))
            fp = os.path.join(hud, name + ".png")
            ensure(os.path.dirname(fp))
            crop.save(fp, optimize=True)
        bp.build_particles()
        bp.build_colormaps()
        bp.build_pvp_models()
        bp.write_lang()
    finally:
        bp.TEX, bp.PACK = old_tex, old_pack
    print(f"[4] GUI پارسی: {n} فایل + HUD/هات‌بار/پارتیکل/مدل/زبان ✔")


def step_meta():
    meta = {"pack": {
        "pack_format": 75,
        "supported_formats": {"min_inclusive": 48, "max_inclusive": 99},
        "description": "§bSHAMSHIR§7 — §6Persian Combat§r §8| 1.21.11 PvP"}}
    with open(os.path.join(PACK, "pack.mcmeta"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    lp = os.path.join(bp.SRC, "misc", "shamshir_logo.png")
    if os.path.exists(lp):
        ImageOps.fit(Image.open(lp).convert("RGB"), (256, 256),
                     Image.LANCZOS).save(os.path.join(PACK, "pack.png"))
    print("[5] pack.mcmeta (فرمت 75) + لوگو ✔")


def step_zip():
    qn = 0
    for dp, _, fs in os.walk(TEX):
        for f in fs:
            if not f.endswith(".png"):
                continue
            p = os.path.join(dp, f)
            try:
                im = Image.open(p)
                if im.mode == "P":
                    continue
                im = im.convert("RGBA")
                if im.getcolors(256) is None:
                    continue
                before = os.path.getsize(p)
                q = im.quantize(colors=256, method=Image.FASTOCTREE,
                                dither=Image.NONE)
                q.save(p, optimize=True)
                if os.path.getsize(p) >= before:
                    im.save(p, optimize=True)
                else:
                    qn += 1
            except Exception:
                pass
    ensure(RELEASE)
    zp = os.path.join(RELEASE, "SHAMSHIR-PersianCombat-v1.0.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for root, _, files in os.walk(PACK):
            for f in files:
                p = os.path.join(root, f)
                z.write(p, os.path.relpath(p, PACK))
    print(f"[6] کوانتایز {qn} فایل | ZIP: {zp} "
          f"({os.path.getsize(zp)/1048576:.1f} MB) ✔")


def main():
    if os.path.isdir(PACK):
        shutil.rmtree(PACK)
    ensure(TEX)
    print("═" * 50)
    print("  SHAMSHIR — Persian Combat (MC 1.21.11, 16x/32x)")
    print("═" * 50)
    step_base()
    step_pvp_items()
    step_blocks()
    step_gui()
    step_meta()
    step_zip()
    print("✅ SHAMSHIR آماده شد — PersianCombat/")


if __name__ == "__main__":
    main()
