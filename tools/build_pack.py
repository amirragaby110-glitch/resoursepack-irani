#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
 PERSIAN LEGACY — PvP Resource Pack Builder  |  سازنده ریسورس پک «میراث پارسی»
============================================================================
 پایپ‌لاین کامل و خودکار:
   1. ساخت ساختار استاندارد پوشه‌های ریسورس پک (assets/minecraft/...)
   2. پردازش تکسچرهای خام AI (src_textures/) :
        - Seamless کردن (حذف درز تکرار بلاک‌ها)
        - Resize به توان ۲ (Mipmap-Safe برای جلوگیری از لگ PvP)
        - تولید خودکار نقشه‌های PBR به فرمت LabPBR ( _n = Normal+AO+Height ،
          _s = Smoothness+F0+Emissive ) برای شیدرهای SEUS/BSL/Complementary
   3. کلید کروما (حذف پس‌زمینه سبز) برای آیتم‌ها و سلاح‌های PvP
   4. بازطراحی برنامه‌نویسی‌شده‌ی HUD (دقیقاً روی مختصات وانیلی => هرگز نمی‌شکند):
        - قلب‌های فیروزه‌ای با حاشیه طلایی
        - Hotbar شفاف با حاشیه گره‌چینی طلایی
        - Crosshair ستاره هشت‌پر مینیمال
        - نوار XP طلایی
   5. پارتیکل‌های پرکنتراست PvP (فیروزه‌ای/طلایی) + گلینت انچنت فیروزه‌ای
   6. Colormap های بایوم (جنگل هیرکانی / کویر لوت / البرز) + آب فیروزه‌ای OptiFine
   7. مدل‌های JSON سلاح‌ها با ترنسفورم PvP (شمشیر کوچک‌تر و پایین‌تر = دید باز)
   8. آسمان OptiFine (کویر روز / شب پرستاره) + خورشید و ماه سفارشی
   9. بهینه‌سازی PNG (فشرده‌سازی Lossless) و بسته‌بندی ZIP نهایی

 استفاده:
   python3 tools/build_pack.py            # ساخت کامل + ZIP
   python3 tools/build_pack.py --res 512  # نسخه سبک‌تر برای PvP رقابتی
   python3 tools/build_pack.py --no-zip   # فقط پوشه پک
============================================================================
"""
import argparse
import json
import math
import os
import shutil
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

# ---------------------------------------------------------------- مسیرها
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src_textures")          # خروجی خام AI
VANILLA = os.path.join(ROOT, "vanilla")           # فایل‌های مرجع وانیلی 1.20.1
PACK = os.path.join(ROOT, "PersianLegacy")        # پوشه نهایی پک
TEX = os.path.join(PACK, "assets", "minecraft", "textures")
RELEASE = os.path.join(ROOT, "release")

# ------------------------------------------------------------- پالت پارسی
TURQUOISE = (64, 224, 208)     # فیروزه‌ای
TURQ_DEEP = (0, 140, 140)      # فیروزه تیره
GOLD = (212, 175, 55)          # طلایی
GOLD_DARK = (122, 92, 24)      # طلایی تیره (حاشیه‌ها)
LAPIS = (18, 52, 120)          # لاجوردی
IVORY = (245, 240, 225)        # عاجی

# نگاشت تکسچر بلاک‌ها + پارامترهای PBR هر متریال
#   smooth: صافی سطح 0..1  |  f0: بازتاب فلزی (230=فلز LabPBR)  |  emiss: نور خودتاب
BLOCK_MATERIALS = {
    "stone":                  dict(smooth=0.25, f0=20,  emiss=0.00),
    "cobblestone":            dict(smooth=0.20, f0=20,  emiss=0.00),
    "stone_bricks":           dict(smooth=0.30, f0=22,  emiss=0.00),
    "bricks":                 dict(smooth=0.35, f0=24,  emiss=0.00),
    "oak_planks":             dict(smooth=0.45, f0=28,  emiss=0.00),
    "sand":                   dict(smooth=0.15, f0=18,  emiss=0.00),
    "dirt":                   dict(smooth=0.12, f0=18,  emiss=0.00),
    "blue_glazed_terracotta": dict(smooth=0.85, f0=40,  emiss=0.00),
    "gold_block":             dict(smooth=0.90, f0=230, emiss=0.05),
    "diamond_block":          dict(smooth=0.92, f0=60,  emiss=0.08),
    # ---- [v3.1] دارایی‌های فاز ۴ ----
    "diamond_ore":            dict(smooth=0.45, f0=42,  emiss=0.06),
    "gold_ore":               dict(smooth=0.40, f0=80,  emiss=0.02),
    "obsidian":               dict(smooth=0.82, f0=46,  emiss=0.00),
    "netherrack":             dict(smooth=0.18, f0=18,  emiss=0.02),
    "grass_block_top":        dict(smooth=0.10, f0=16,  emiss=0.00),
}

ITEM_FILES = ["diamond_sword", "iron_sword", "netherite_sword",
              "bow", "golden_apple", "ender_pearl",
              # [v3.1] فاز ۴ — PvP-Critical
              "shield", "totem_of_undying", "arrow", "mace"]

# چرخش اسپرایت سلاح‌ها برای هم‌راستایی با محور مورب وانیلی (لبه به بالا-راست)
# [رفع باگ ممیزی #5: خروجی AI افقی بود => در دست بازیکن کج دیده می‌شد]
ITEM_ROTATE = {"diamond_sword": 35, "iron_sword": 35}

# ------------------- سیستم Fallback تماتیک (نسخه ۲) -------------------
# اگر برای دارایی خاصی تکسچر AI ساخته نشده باشد، از نزدیک‌ترین تکسچر
# تماتیک با تنظیم رنگ/روشنایی مشتق می‌شود تا کل دنیای بازی یکدست بماند.
# (توجه: تکسچر بنفش-مشکی Missing فقط از «ارجاع مدل شکسته» ایجاد می‌شود،
#  نه از نبود تکسچر — ریسورس پک همیشه به وانیلا Fallback می‌کند. این سیستم
#  برای «یکدستی تم» است، نه رفع خطا.)
DERIVED_BLOCKS = {
    # target: (source, تنظیمات رنگ)
    "deepslate":            ("stone",        dict(sat=0.55, val=0.45)),
    "cobbled_deepslate":    ("cobblestone",  dict(sat=0.55, val=0.45)),
    "smooth_stone":         ("stone",        dict(sat=0.80, val=1.05, blur=4)),
    "andesite":             ("stone",        dict(sat=0.45, val=0.90)),
    "diorite":              ("stone",        dict(sat=0.30, val=1.20)),
    "granite":              ("stone",        dict(hue=0.02, sat=0.60, val=0.95)),
    "sandstone":            ("sand",         dict(val=0.96)),
    "sandstone_top":        ("sand",         dict(val=0.90)),
    "sandstone_bottom":     ("sand",         dict(val=0.85)),
    "cracked_stone_bricks": ("stone_bricks", dict(val=0.78)),
    "mossy_stone_bricks":   ("stone_bricks", dict(hue=0.10, sat=0.95, val=0.92)),
    "spruce_planks":        ("oak_planks",   dict(val=0.62)),
    "dark_oak_planks":      ("oak_planks",   dict(val=0.48)),
    "birch_planks":         ("oak_planks",   dict(sat=0.55, val=1.22)),
    "cherry_planks":        ("oak_planks",   dict(force_hue=0.93, sat=0.40, val=1.10)),
    "bamboo_planks":        ("oak_planks",   dict(force_hue=0.12, sat=0.50, val=1.15)),
    "acacia_planks":        ("oak_planks",   dict(force_hue=0.03, sat=0.85, val=0.95)),
    "jungle_planks":        ("oak_planks",   dict(force_hue=0.05, sat=0.70, val=0.90)),
    "mangrove_planks":      ("oak_planks",   dict(force_hue=0.99, sat=0.65, val=0.70)),
    "gravel":               ("cobblestone",  dict(sat=0.35, val=0.80)),
    "mud_bricks":           ("bricks",       dict(sat=0.45, val=0.75)),  # کاهگل!
}
DERIVED_ITEMS = {
    "netherite_sword": ("diamond_sword", dict(sat=0.35, val=0.50)),
    "golden_sword":    ("iron_sword",    dict(force_hue=0.11, sat=1.70, val=1.10)),
    "stone_sword":     ("iron_sword",    dict(sat=0.30, val=0.75)),
    "wooden_sword":    ("iron_sword",    dict(force_hue=0.07, sat=1.30, val=0.70)),
}

SWORDS = ["wooden_sword", "stone_sword", "iron_sword",
          "golden_sword", "diamond_sword", "netherite_sword"]


# ============================================================ ابزارهای پایه
def ensure(path):
    os.makedirs(path, exist_ok=True)
    return path


def save_png(img, path, optimize=True):
    """ذخیره PNG با فشرده‌سازی Lossless (کاهش حجم بدون افت کیفیت)."""
    ensure(os.path.dirname(path))
    img.save(path, "PNG", optimize=optimize)


def pot(n):
    """نزدیک‌ترین توان ۲ (لازمه‌ی Mipmap سالم => بدون لگ در PvP)."""
    return 1 << max(4, int(round(math.log2(max(16, n)))))


ERRORS = []  # [v2] جمع‌آوری خطاهای مراحل — بیلد هرگز وسط راه نمی‌میرد


def stage(label):
    """[v2] دکوراتور مدیریت خطا: هر مرحله ایزوله اجرا و خطایش گزارش می‌شود."""
    def wrap(fn):
        def inner(*a, **kw):
            try:
                return fn(*a, **kw)
            except Exception as e:
                ERRORS.append(f"{label}: {type(e).__name__}: {e}")
                print(f"  ✖ خطا در {label}: {e}")
        return inner
    return wrap


def adjust(img, hue=0.0, sat=1.0, val=1.0, force_hue=None, blur=0):
    """[v2] موتور مشتق‌سازی Fallback: تنظیم رنگ با حفظ آلفا و بافت."""
    img = img.convert("RGBA")
    if blur:
        rgb = img.convert("RGB").filter(ImageFilter.GaussianBlur(blur))
    else:
        rgb = img.convert("RGB")
    arr = np.asarray(img)
    hsv = np.asarray(rgb.convert("HSV")).astype(np.int16).copy()
    if force_hue is not None:
        hsv[..., 0] = int(force_hue * 255) % 256
    else:
        hsv[..., 0] = (hsv[..., 0] + int(hue * 255)) % 256
    hsv[..., 1] = np.clip(hsv[..., 1] * sat, 0, 255)
    hsv[..., 2] = np.clip(hsv[..., 2] * val, 0, 255)
    out_rgb = Image.fromarray(hsv.astype(np.uint8), "HSV").convert("RGB")
    return Image.fromarray(
        np.dstack([np.asarray(out_rgb), arr[..., 3]]), "RGBA")


# ====================================================== ۱) ساختار استاندارد
def build_structure():
    """ایجاد کامل ساختار پوشه‌های استاندارد ریسورس پک."""
    for d in ["block", "item", "gui", "environment", "misc", "particle",
              "colormap", "entity", "models"]:
        ensure(os.path.join(TEX, d))
    ensure(os.path.join(PACK, "assets", "minecraft", "models", "item"))
    ensure(os.path.join(PACK, "assets", "minecraft", "optifine", "sky", "world0"))
    ensure(os.path.join(PACK, "assets", "minecraft", "optifine", "colormap"))
    print("[1/9] ساختار پوشه‌ها ساخته شد ✔")


def write_mcmeta():
    """pack.mcmeta — شناسنامه پک (pack_format 15 = نسخه 1.20.x)"""
    meta = {
        "pack": {
            # 15 = Minecraft 1.20 – 1.20.1  (با supported_formats تا نسخه‌های جدیدتر)
            "pack_format": 15,
            "supported_formats": {"min_inclusive": 9, "max_inclusive": 46},
            "description": "§b✦ §6Persian Legacy §b✦§r §7Photoreal PvP §8| §e میراث پارسی"
        }
    }
    with open(os.path.join(PACK, "pack.mcmeta"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print("[2/9] pack.mcmeta نوشته شد ✔")


# ==================== [v3] Detail_Enhancement_Subroutine + Color_Grading
def enhance_micro(img, amount=0.6):
    """
    [v3-Phase2] افزودن میکرو-جزئیات: تیزسازی بافت (خش‌های ریز، تخلخل آجر)
    + نویز دانه‌ای ۱٪ برای شکستن حالت «پلاستیکی/بیش‌ازحد صاف».
    """
    sharp = img.filter(ImageFilter.UnsharpMask(radius=3, percent=int(90 * amount),
                                               threshold=2))
    arr = np.asarray(sharp).astype(np.int16)
    rng = np.random.default_rng(1401)  # ثابت => بیلد تکرارپذیر
    noise = rng.integers(-3, 4, arr.shape[:2])[..., None]
    arr[..., :3] = np.clip(arr[..., :3] + noise, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), img.mode)


def grade(img):
    """
    [v3-Phase2] گرید رنگ سینمایی: تقویت انتخابی «فیروزه‌ای» و «طلایی/لاجورد»
    + منحنی S ملایم روی روشنایی — بدون خستگی چشم در PvP (اشباع مهارشده).
    """
    rgb = img.convert("RGB")
    hsv = np.asarray(rgb.convert("HSV")).astype(np.float32)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    # تقویت فیروزه (hue≈120..150 در مقیاس 0..255) و طلایی (hue≈25..50)
    turq = np.exp(-((h - 133) ** 2) / (2 * 14 ** 2))
    gold = np.exp(-((h - 36) ** 2) / (2 * 12 ** 2))
    s = np.clip(s * (1.0 + 0.16 * turq + 0.12 * gold), 0, 255)
    v = np.clip(255 * (v / 255) ** 0.97 * (1 + 0.05 * np.sin(
        (v / 255 - 0.5) * math.pi)), 0, 255)  # S-curve ملایم
    out = Image.fromarray(
        np.stack([h, s, v], -1).astype(np.uint8), "HSV").convert("RGB")
    if img.mode == "RGBA":
        out = Image.fromarray(
            np.dstack([np.asarray(out), np.asarray(img)[..., 3]]), "RGBA")
    return out


# ============================================== ۲) پردازش بلاک‌ها + PBR
def make_seamless(img, blend=0.07):
    """حذف درز تکرار: لبه‌های مقابل را با ماسک خطی به هم می‌آمیزد."""
    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    h, w, _ = a.shape
    bw = max(2, int(w * blend))
    # افقی
    ramp = np.linspace(0.0, 0.5, bw)[None, :, None]
    left, right = a[:, :bw].copy(), a[:, -bw:].copy()
    a[:, :bw] = left * (0.5 + ramp) + right[:, ::-1] * (0.5 - ramp)
    a[:, -bw:] = right * (0.5 + ramp[:, ::-1]) + left[:, ::-1] * (0.5 - ramp[:, ::-1])
    # عمودی
    bh = max(2, int(h * blend))
    rampv = np.linspace(0.0, 0.5, bh)[:, None, None]
    top, bot = a[:bh].copy(), a[-bh:].copy()
    a[:bh] = top * (0.5 + rampv) + bot[::-1] * (0.5 - rampv)
    a[-bh:] = bot * (0.5 + rampv[::-1]) + top[::-1] * (0.5 - rampv[::-1])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def gen_labpbr(img, mat):
    """تولید خودکار نقشه‌های LabPBR (نرمال/AO/ارتفاع + صافی/F0/امیسیو)."""
    g = np.asarray(img.convert("L"), dtype=np.float32) / 255.0
    # نقشه ارتفاع = روشنایی نرم‌شده
    height = np.asarray(
        Image.fromarray((g * 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(2)), dtype=np.float32) / 255.0
    # نرمال از گرادیان (Sobel ساده با wrap برای حفظ tiling)
    gx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 2.0
    gy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 2.0
    nz = 1.0 / np.sqrt(gx * gx + gy * gy + 1.0)
    nx, ny = -gx * nz, -gy * nz
    # AO تقریبی = ارتفاع معکوس‌شده ملایم
    ao = 0.75 + 0.25 * height
    n = np.stack([(nx * 0.5 + 0.5), (ny * 0.5 + 0.5), ao, height], axis=-1)
    normal = Image.fromarray((np.clip(n, 0, 1) * 255).astype(np.uint8), "RGBA")

    # Specular: صافی با کمی تنوع محلی + F0 ثابت متریال + امیسیو از نقاط روشن
    local = np.abs(g - height)  # زبری محلی
    smooth = np.clip(mat["smooth"] - local * 0.6, 0.02, 0.98)
    emiss = np.clip((g - 0.82) * 4.0, 0, 1) * mat["emiss"] * 255
    s = np.stack([
        smooth * 255,
        np.full_like(g, mat["f0"]),
        np.zeros_like(g),
        np.clip(emiss, 0, 254),   # 255 در LabPBR رزرو است
    ], axis=-1)
    spec = Image.fromarray(s.astype(np.uint8), "RGBA")
    return normal, spec


def build_blocks(res):
    src_dir = os.path.join(SRC, "block")
    out_dir = os.path.join(TEX, "block")
    if not os.path.isdir(src_dir):
        print("[3/9] هشدار: src_textures/block یافت نشد — رد شد")
        return
    n = 0
    for name, mat in BLOCK_MATERIALS.items():
        p = os.path.join(src_dir, name + ".png")
        if not os.path.exists(p):
            continue
        img = Image.open(p).convert("RGB")
        img = ImageOps.fit(img, (res, res), Image.LANCZOS)
        img = make_seamless(img)
        img = grade(enhance_micro(img))   # [v3] میکرو-جزئیات + گرید سینمایی
        if name == "grass_block_top":
            # [v3.1] Tint-Safe: خاکستری خالص => رنگ سبز از colormap بایوم
            # (هیرکانی/لوت/البرز) در خود بازی اعمال می‌شود، مثل وانیلا
            l = np.asarray(img.convert("L"), np.float32)
            l = np.clip(l * (150.0 / max(l.mean(), 1.0)), 0, 255).astype(np.uint8)
            img = Image.merge("RGB", [Image.fromarray(l)] * 3)
        save_png(img.convert("RGBA"), os.path.join(out_dir, name + ".png"))
        normal, spec = gen_labpbr(img, mat)
        save_png(normal, os.path.join(out_dir, name + "_n.png"))
        save_png(spec, os.path.join(out_dir, name + "_s.png"))
        n += 1
    # [v3.1] شیشه اروسی: مرکزِ سبز کروماکی => کاملاً شفاف (دید PvP باز)
    gp = os.path.join(src_dir, "glass.png")
    if os.path.exists(gp):
        g = chroma_key(Image.open(gp)).resize((res, res), Image.LANCZOS)
        save_png(g, os.path.join(out_dir, "glass.png"))
        n += 1
    print(f"[3/9] {n} بلاک + نقشه‌های PBR ساخته شد ✔ (رزولوشن {res})")


# ============================================== ۳) آیتم‌ها (کلید کروما سبز)
def chroma_key(img, despill=True):
    """حذف پس‌زمینه سبز خالص و پاک‌سازی لبه‌ها برای آیکون آیتم تمیز PvP."""
    a = np.asarray(img.convert("RGB"), dtype=np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    greenness = g - np.maximum(r, b)
    alpha = np.clip(255 - (greenness - 12) * 6, 0, 255).astype(np.uint8)
    alpha[greenness > 60] = 0
    if despill:  # حذف هاله سبز لبه‌ها
        spill = np.clip(g - (r + b) // 2, 0, 255)
        a[..., 1] = np.clip(g - spill // 2, 0, 255)
    out = np.dstack([a.astype(np.uint8), alpha])
    return Image.fromarray(out, "RGBA")


def build_items(res_item):
    src_dir = os.path.join(SRC, "item")
    out_dir = os.path.join(TEX, "item")
    if not os.path.isdir(src_dir):
        print("[4/9] هشدار: src_textures/item هنوز خالی است — رد شد")
        return
    n = 0
    for name in ITEM_FILES:
        p = os.path.join(src_dir, name + ".png")
        if not os.path.exists(p):
            continue
        img = chroma_key(Image.open(p))
        # [v2] هم‌راستاسازی مورب سلاح‌ها با گرفتن وانیلی (رفع باگ #5)
        if name in ITEM_ROTATE:
            img = img.rotate(ITEM_ROTATE[name], expand=True,
                             resample=Image.BICUBIC)
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        # قرارگیری در بوم مربع با حاشیه ۴٪ (Hitbox دقیق و بدون بزرگ‌نمایی کاذب)
        side = int(max(img.size) * 1.08)
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        canvas.paste(img, ((side - img.width) // 2, (side - img.height) // 2), img)
        canvas = canvas.resize((res_item, res_item), Image.LANCZOS)
        canvas = grade(canvas)            # [v3] گرید فیروزه/طلا روی سلاح‌ها
        save_png(canvas, os.path.join(out_dir, name + ".png"))
        n += 1
    print(f"[4/9] {n} آیتم/سلاح PvP ساخته شد ✔")


# ================================================ ۴) HUD اختصاصی پارسی
S = 4  # ضریب بزرگ‌نمایی GUI (256 -> 1024)


def hue_remap(img_arr, cond, target_hue_shift):
    """چرخش رنگ پیکسل‌های انتخابی با حفظ سایه‌روشن (خوانایی کامل HUD)."""
    import colorsys
    a = img_arr
    ys, xs = np.where(cond)
    for y, x in zip(ys, xs):
        r, g, b, al = a[y, x] / 255.0
        h, l, s_ = colorsys.rgb_to_hls(r, g, b)
        h = (h + target_hue_shift) % 1.0
        r2, g2, b2 = colorsys.hls_to_rgb(h, l, min(1.0, s_ * 1.1))
        a[y, x] = [int(r2 * 255), int(g2 * 255), int(b2 * 255), int(al * 255)]
    return a


def draw_eight_star(d, cx, cy, r_out, r_in, fill, outline=None, rot=0.0):
    """ستاره هشت‌پر ایرانی (شمسه) — پایه Crosshair و تزئینات."""
    pts = []
    for i in range(16):
        ang = rot + i * math.pi / 8
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    d.polygon(pts, fill=fill, outline=outline)


def build_icons():
    """icons.png — قلب فیروزه‌ای، XP طلایی، Crosshair ستاره هشت‌پر."""
    src = Image.open(os.path.join(VANILLA, "gui", "icons.png")).convert("RGBA")
    img = src.resize((256 * S, 256 * S), Image.NEAREST)
    a = np.asarray(img).copy()

    # --- قلب‌ها (ردیف y=0..9 وانیلی): قرمز -> فیروزه‌ای (چرخش hue ~ +0.42)
    region = a[0:9 * S, :, :]
    r, g, b = region[..., 0].astype(int), region[..., 1].astype(int), region[..., 2].astype(int)
    red_mask = (r > 120) & (r > g + 40) & (r > b + 40)
    region[:] = hue_remap(region, red_mask, 0.485)  # قرمز -> فیروزه واقعی
    # حاشیه‌های تیره قلب -> طلایی تیره (لبه طلایی درخواستی)
    dark = (r < 70) & (g < 70) & (b < 70) & (region[..., 3] > 200)
    region[dark] = [GOLD_DARK[0], GOLD_DARK[1], GOLD_DARK[2], 255]
    a[0:9 * S, :, :] = region

    # --- نوار XP (y=64..69 خالی، 69..74 پر): سبز -> طلایی
    xp = a[64 * S:74 * S, 0:182 * S, :]
    rg, gg, bg = xp[..., 0].astype(int), xp[..., 1].astype(int), xp[..., 2].astype(int)
    green_mask = (gg > 90) & (gg > rg + 30) & (gg > bg + 30)
    xp[:] = hue_remap(xp, green_mask, -0.20)  # سبز -> طلایی
    a[64 * S:74 * S, 0:182 * S, :] = xp

    img = Image.fromarray(a)

    # --- Crosshair: پاک‌سازی ناحیه (0,0,16,16) و ترسیم ستاره هشت‌پر مینیمال
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 16 * S - 1, 16 * S - 1], fill=(0, 0, 0, 0))
    cx = cy = 7.5 * S
    t = max(1, S // 2)             # ضخامت خطوط (مینیمال = دقت نشانه‌گیری)
    ray, gap = 6 * S, int(1.8 * S)  # طول بازو و فاصله از مرکز (دید باز روی هدف)
    white = (255, 255, 255, 235)
    for ang in (0, 90, 180, 270):   # چهار بازوی اصلی سفید
        rad = math.radians(ang)
        x1 = cx + gap * math.cos(rad); y1 = cy + gap * math.sin(rad)
        x2 = cx + ray * math.cos(rad); y2 = cy + ray * math.sin(rad)
        d.line([x1, y1, x2, y2], fill=white, width=t * 2)
    for ang in (45, 135, 225, 315):  # چهار بازوی مورب طلایی کوتاه
        rad = math.radians(ang)
        x1 = cx + (gap + S) * math.cos(rad); y1 = cy + (gap + S) * math.sin(rad)
        x2 = cx + (ray - S) * math.cos(rad); y2 = cy + (ray - S) * math.sin(rad)
        d.line([x1, y1, x2, y2], fill=GOLD + (220,), width=t)
    draw_eight_star(d, cx, cy, 1.4 * S, 0.6 * S, TURQUOISE + (255,))  # شمسه مرکزی

    save_png(img, os.path.join(TEX, "gui", "icons.png"))


def build_widgets():
    """widgets.png — Hotbar شفاف با قاب گره‌چینی طلایی + سلکتور فیروزه‌ای."""
    src = Image.open(os.path.join(VANILLA, "gui", "widgets.png")).convert("RGBA")
    img = src.resize((256 * S, 256 * S), Image.NEAREST)
    d = ImageDraw.Draw(img)

    # ---------- Hotbar وانیلی: (0,0) تا (182,22) — بازطراحی کامل
    d.rectangle([0, 0, 182 * S - 1, 22 * S - 1], fill=(0, 0, 0, 0))
    # پس‌زمینه بسیار کم‌رنگ (شفاف => دید کامل به زمین زیر پا)
    d.rectangle([S, S, 182 * S - S - 1, 22 * S - S - 1], fill=(10, 16, 20, 64))
    # قاب طلایی بیرونی دو لایه
    d.rectangle([0, 0, 182 * S - 1, 22 * S - 1], outline=GOLD + (230,), width=S)
    d.rectangle([S, S, 182 * S - S - 1, 22 * S - S - 1],
                outline=GOLD_DARK + (200,), width=max(1, S // 2))
    # جداکننده اسلات‌ها + گره‌چینی (ستاره‌های طلایی روی قاب) [v2: پاک‌سازی حلقه]
    for i in range(1, 9):
        x = (1 + 20 * i) * S
        d.line([x, 2 * S, x, 20 * S], fill=GOLD + (150,), width=max(1, S // 2))
    for i in range(9):  # ستاره کوچک بالا/پایین هر اسلات (موتیف گره‌چینی، غیرمزاحم)
        cx = (1 + 20 * i + 10) * S
        draw_eight_star(d, cx, 1.1 * S, 1.0 * S, 0.45 * S, GOLD + (200,))
        draw_eight_star(d, cx, 20.9 * S, 1.0 * S, 0.45 * S, GOLD + (200,))

    # ---------- سلکتور اسلات: (0,22) تا (24,46) — فیروزه‌ای درخشان، مرکز کاملاً شفاف
    d.rectangle([0, 22 * S, 24 * S - 1, 46 * S - 1], fill=(0, 0, 0, 0))
    d.rectangle([0, 22 * S, 24 * S - 1, 46 * S - 1],
                outline=TURQUOISE + (255,), width=S)
    d.rectangle([S, 22 * S + S, 24 * S - S - 1, 46 * S - S - 1],
                outline=IVORY + (170,), width=max(1, S // 2))
    for cx, cy in [(0, 22 * S), (24 * S - 1, 22 * S),
                   (0, 46 * S - 1), (24 * S - 1, 46 * S - 1)]:
        draw_eight_star(ImageDraw.Draw(img), cx, cy, 1.6 * S, 0.7 * S,
                        GOLD + (255,))

    save_png(img, os.path.join(TEX, "gui", "widgets.png"))


def build_gui():
    build_icons()
    build_widgets()
    print("[5/9] HUD پارسی (قلب فیروزه‌ای/Hotbar شفاف/Crosshair شمسه) ساخته شد ✔")


# ============================================ ۵) پارتیکل‌های پرکنتراست PvP
def star_particle(size, color_core, color_glow, points=4, rot=0.0):
    """اسپرایت ستاره‌ای کوچک و پرکنتراست — در شلوغی PvP گم نمی‌شود."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size / 2
    pts = []
    for i in range(points * 2):
        ang = rot + i * math.pi / points
        r = c * 0.95 if i % 2 == 0 else c * 0.28
        pts.append((c + r * math.cos(ang), c + r * math.sin(ang)))
    d.polygon(pts, fill=color_glow)
    pts2 = [((x - c) * 0.55 + c, (y - c) * 0.55 + c) for x, y in pts]
    d.polygon(pts2, fill=color_core)
    return img


def build_particles():
    out = os.path.join(TEX, "particle")
    # کریت (ضربه بحرانی) = ستاره طلایی | گلینت = ستاره فیروزه‌ای
    save_png(star_particle(32, IVORY + (255,), GOLD + (230,)),
             os.path.join(out, "critical_hit.png"))
    save_png(star_particle(32, IVORY + (255,), TURQUOISE + (230,), rot=math.pi / 4),
             os.path.join(out, "glint.png"))
    # موج شمشیر (Sweep): تینت فیروزه‌ای->طلایی روی فریم‌های وانیلی
    for i in range(8):
        p = os.path.join(VANILLA, "particle", f"sweep_{i}.png")
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGBA")
        arr = np.asarray(im).astype(np.float32)
        t = i / 7.0
        tint = np.array([TURQUOISE[0] * (1 - t) + GOLD[0] * t,
                         TURQUOISE[1] * (1 - t) + GOLD[1] * t,
                         TURQUOISE[2] * (1 - t) + GOLD[2] * t]) / 255.0
        arr[..., :3] = np.clip(arr[..., :3] * tint + 40 * (arr[..., 3:4] / 255.0), 0, 255)
        save_png(Image.fromarray(arr.astype(np.uint8)), os.path.join(out, f"sweep_{i}.png"))
    # گلینت انچنت فیروزه‌ای (به‌جای بنفش وانیلی)
    for name in ["enchanted_glint_item.png", "enchanted_glint_entity.png"]:
        p = os.path.join(VANILLA, "misc", name)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGBA")
        arr = np.asarray(im).astype(np.float32)
        lum = arr[..., :3].mean(axis=-1, keepdims=True) / 255.0
        col = np.array(TURQUOISE, dtype=np.float32)
        arr[..., :3] = np.clip(lum * col * 1.25, 0, 255)
        save_png(Image.fromarray(arr.astype(np.uint8)), os.path.join(TEX, "misc", name))
    print("[6/9] پارتیکل‌های PvP (فیروزه/طلا) ساخته شد ✔")


# =========================================== ۶) Colormap بایوم‌های ایرانی
def bilinear_map(c_tl, c_tr, c_bl, c_br, size=256):
    """گرادیان دوبعدی رنگ بایوم: محور X دما، محور Y رطوبت."""
    x = np.linspace(0, 1, size)[None, :, None]
    y = np.linspace(0, 1, size)[:, None, None]
    tl, tr = np.array(c_tl, float), np.array(c_tr, float)
    bl, br = np.array(c_bl, float), np.array(c_br, float)
    a = (tl * (1 - x) + tr * x) * (1 - y) + (bl * (1 - x) + br * x) * y
    return Image.fromarray(a.astype(np.uint8), "RGB").convert("RGBA")


def build_colormaps():
    out = os.path.join(TEX, "colormap")
    # چمن: کویر لوت (خشک/گرم = طلایی-خاکی) تا جنگل هیرکانی (مرطوب = سبز عمیق)
    save_png(bilinear_map((196, 178, 106), (172, 158, 92),
                          (66, 152, 66), (34, 118, 52)),
             os.path.join(out, "grass.png"))
    # شاخ‌وبرگ: سبزهای اشباع‌تر هیرکانی + زیتونی ارتفاعات البرز
    save_png(bilinear_map((150, 148, 84), (128, 132, 70),
                          (44, 132, 52), (20, 100, 44)),
             os.path.join(out, "foliage.png"))
    # آب فیروزه‌ای (OptiFine Custom Colors)
    save_png(bilinear_map((64, 190, 200), (48, 160, 190),
                          (30, 140, 160), (16, 100, 140)),
             os.path.join(PACK, "assets", "minecraft", "optifine",
                          "colormap", "water.png"))
    print("[7/9] Colormap بایوم‌ها (هیرکانی/لوت/البرز) ساخته شد ✔")


# ======================================= ۷) مدل‌های JSON سلاح (PvP-First)
def build_pvp_models():
    """
    ترنسفورم‌های PvP:
      - شمشیر در First Person کوچک‌تر و پایین‌تر => مرکز دید کاملاً باز
      - بدون هیچ المان سه‌بعدی اضافه (فقط مدل مسطح وانیلی = Hitbox دقیق)
    """
    mdl_dir = os.path.join(PACK, "assets", "minecraft", "models", "item")
    display = {
        "thirdperson_righthand": {"rotation": [0, -90, 55], "translation": [0, 3.0, 0.5],
                                  "scale": [0.80, 0.80, 0.80]},
        "thirdperson_lefthand": {"rotation": [0, 90, -55], "translation": [0, 3.0, 0.5],
                                 "scale": [0.80, 0.80, 0.80]},
        "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.5, 3.2, 1.0],
                                  "scale": [0.62, 0.62, 0.62]},
        "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [1.5, 3.2, 1.0],
                                 "scale": [0.62, 0.62, 0.62]},
        "gui": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]},
        "ground": {"translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
        "fixed": {"rotation": [0, 180, 0], "scale": [1, 1, 1]},
    }
    for sword in SWORDS:
        model = {
            "_comment": "Persian Legacy PvP model — flat, small, clean hitbox",
            "parent": "minecraft:item/handheld",
            "textures": {"layer0": f"minecraft:item/{sword}"},
            "display": display,
        }
        with open(os.path.join(mdl_dir, sword + ".json"), "w") as f:
            json.dump(model, f, indent=2)

    # [v3.1] گرز ۱.۲۱ (Mace) — همان فلسفه: مسطح، کوچک، Hitbox وانیلی
    mace = {"_comment": "Persian gorz — flat PvP model (MC 1.21+)",
            "parent": "minecraft:item/handheld",
            "textures": {"layer0": "minecraft:item/mace"},
            "display": display}
    with open(os.path.join(mdl_dir, "mace.json"), "w") as f:
        json.dump(mace, f, indent=2)

    # [v3.1] سپر دوبعدی PvP: مدل ۳بعدی وانیلی نیمِ صفحه را کور می‌کند؛
    # مدل تختِ کوچک => دید باز + سیلوئت خوانا (تکنیک رایج پک‌های PvP)
    sh_disp = {
        "thirdperson_righthand": {"rotation": [0, 90, 0],
                                  "translation": [0, 2.0, 1.0],
                                  "scale": [0.65, 0.65, 0.65]},
        "thirdperson_lefthand": {"rotation": [0, -90, 0],
                                 "translation": [0, 2.0, 1.0],
                                 "scale": [0.65, 0.65, 0.65]},
        "firstperson_righthand": {"rotation": [0, -10, 0],
                                  "translation": [-2.5, 1.0, 0],
                                  "scale": [0.55, 0.55, 0.55]},
        "firstperson_lefthand": {"rotation": [0, 10, 0],
                                 "translation": [-2.5, 1.0, 0],
                                 "scale": [0.55, 0.55, 0.55]},
        "gui": {"scale": [1, 1, 1]},
        "ground": {"translation": [0, 2, 0], "scale": [0.4, 0.4, 0.4]},
        "fixed": {"rotation": [0, 180, 0], "scale": [1, 1, 1]},
    }
    shield = {"_comment": "Persian round shield — flat 2D PvP model",
              "parent": "minecraft:item/generated",
              "textures": {"layer0": "minecraft:item/shield"},
              "display": sh_disp,
              "overrides": [{"predicate": {"blocking": 1},
                             "model": "minecraft:item/shield_blocking"}]}
    blocking = {"_comment": "blocking pose — نزدیک‌تر اما همچنان غیرمسدودکننده",
                "parent": "minecraft:item/generated",
                "textures": {"layer0": "minecraft:item/shield"},
                "display": {
                    **sh_disp,
                    "firstperson_righthand": {"rotation": [0, -5, 5],
                                              "translation": [-1.2, 1.5, 0],
                                              "scale": [0.75, 0.75, 0.75]},
                    "firstperson_lefthand": {"rotation": [0, 5, -5],
                                             "translation": [-1.2, 1.5, 0],
                                             "scale": [0.75, 0.75, 0.75]}}}
    with open(os.path.join(mdl_dir, "shield.json"), "w") as f:
        json.dump(shield, f, indent=2)
    with open(os.path.join(mdl_dir, "shield_blocking.json"), "w") as f:
        json.dump(blocking, f, indent=2)
    print("[8/9] مدل‌های PvP (شمشیرها + گرز + سپر تخت) نوشته شد ✔")


# ================================================ ۸) آسمان و محیط
def build_environment():
    env_out = os.path.join(TEX, "environment")
    sky_dir = os.path.join(PACK, "assets", "minecraft", "optifine", "sky", "world0")

    # ---- خورشید: حذف پس‌زمینه مشکی (آلفا از روشنایی) + هاله طلایی
    sun_src = os.path.join(SRC, "environment", "sun.png")
    if os.path.exists(sun_src):
        im = Image.open(sun_src).convert("RGB")
        im = ImageOps.fit(im, (512, 512), Image.LANCZOS)
        arr = np.asarray(im).astype(np.float32)
        lum = arr.max(axis=-1)
        alpha = np.clip((lum - 14) * 1.6, 0, 255).astype(np.uint8)
        save_png(Image.fromarray(np.dstack([arr.astype(np.uint8), alpha]), "RGBA"),
                 os.path.join(env_out, "sun.png"))

    # ---- ماه: ساخت خودکار ۸ فاز از یک تصویر ماه کامل (گرید 4x2 وانیلی)
    moon_src = os.path.join(SRC, "environment", "moon.png")
    if os.path.exists(moon_src):
        cell = 256
        moon = Image.open(moon_src).convert("RGB")
        moon = ImageOps.fit(moon, (cell, cell), Image.LANCZOS)
        marr = np.asarray(moon).astype(np.float32)
        lum = marr.max(axis=-1)
        malpha = np.clip((lum - 12) * 2.0, 0, 255).astype(np.uint8)
        moon_rgba = Image.fromarray(
            np.dstack([marr.astype(np.uint8), malpha]), "RGBA")
        grid = Image.new("RGBA", (cell * 4, cell * 2), (0, 0, 0, 0))
        # [v3-fix B11] ترمیناتور بیضوی تحلیلی: هلال تدریجی واقعی برای ۸ فاز
        yy, xx = np.mgrid[0:cell, 0:cell].astype(np.float32)
        cx = cy = (cell - 1) / 2.0
        R = cell * 0.5
        ry = np.sqrt(np.clip(R * R - (yy - cy) ** 2, 1e-6, None))
        s = np.clip((xx - cx) / ry, -1.5, 1.5)   # مختصات نرمال روی قرص
        for phase in range(8):
            frame = moon_rgba.copy()
            if phase != 0:
                k = math.cos(2 * math.pi * phase / 8.0)
                if phase == 4:                       # ماه نو = تمام تیره
                    dark_mask = np.ones_like(s, bool)
                elif phase < 4:                      # کاهنده: تاریکی از چپ
                    dark_mask = s < -k
                else:                                # فزاینده: تاریکی از راست
                    dark_mask = s > k
                shade = Image.fromarray(
                    (dark_mask * 235).astype(np.uint8)).filter(
                        ImageFilter.GaussianBlur(3))
                dark = Image.new("RGBA", (cell, cell), (8, 10, 24, 255))
                frame = Image.composite(dark, frame, shade)
                frame.putalpha(Image.fromarray(malpha))  # حفظ آلفای قرص
            grid.paste(frame, ((phase % 4) * cell, (phase // 4) * cell))
        save_png(grid, os.path.join(env_out, "moon_phases.png"))

    # ---- آسمان OptiFine: کویر روز / شب پرستاره (در صورت وجود سورس)
    skies = {"sky_day.png": ("sky1", "0:00", "12:00", "blend=add"),
             "sky_night.png": ("sky2", "13:00", "23:00", "blend=add")}
    idx = 0
    for fname, (layer, _, _, _) in skies.items():
        p = os.path.join(SRC, "environment", fname)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        im = ImageOps.fit(im, (3072, 2048), Image.LANCZOS)  # گرید 3x2 اپتیفاین
        save_png(im.convert("RGBA"), os.path.join(sky_dir, f"{layer}.png"))
        props = [
            f"source=./{layer}.png",
            "blend=add" if layer == "sky2" else "blend=alpha",
            "rotate=true",
            "speed=1.0",
            "axis=1 0 0",
        ]
        if layer == "sky1":   # روز
            props += ["startFadeIn=4:30", "endFadeIn=6:00",
                      "startFadeOut=18:30", "endFadeOut=20:00"]
        else:                 # شب
            props += ["startFadeIn=18:30", "endFadeIn=20:00",
                      "startFadeOut=4:30", "endFadeOut=6:00"]
        with open(os.path.join(sky_dir, f"{layer}.properties"), "w") as f:
            f.write("\n".join(props) + "\n")
        idx += 1
    print(f"[9a] محیط: خورشید/ماه/آسمان ({idx} لایه اسکای) ساخته شد ✔")


# ====================================== [v2] ۸.۵) سیستم Fallback تماتیک
def build_fallbacks():
    """
    مشتق‌سازی خودکار دارایی‌های بدون تکسچر اختصاصی از نزدیک‌ترین دارایی
    تماتیک => هیچ بلاک/آیتم پرکاربردی خارج از تم پارسی نمی‌ماند.
    """
    blk_dir = os.path.join(TEX, "block")
    itm_dir = os.path.join(TEX, "item")
    n = 0
    for target, (source, ops) in DERIVED_BLOCKS.items():
        src_p = os.path.join(blk_dir, source + ".png")
        dst_p = os.path.join(blk_dir, target + ".png")
        if not os.path.exists(src_p) or os.path.exists(dst_p):
            continue
        img = adjust(Image.open(src_p), **ops)
        save_png(img, dst_p)
        # نقشه‌های PBR متریال منبع نیز به ارث می‌رسند
        mat = BLOCK_MATERIALS.get(source)
        if mat:
            normal, spec = gen_labpbr(img.convert("RGB"), mat)
            save_png(normal, os.path.join(blk_dir, target + "_n.png"))
            save_png(spec, os.path.join(blk_dir, target + "_s.png"))
        n += 1
    for target, (source, ops) in DERIVED_ITEMS.items():
        src_p = os.path.join(itm_dir, source + ".png")
        dst_p = os.path.join(itm_dir, target + ".png")
        if not os.path.exists(src_p) or os.path.exists(dst_p):
            continue
        save_png(adjust(Image.open(src_p), **ops), dst_p)
        n += 1
    # [v3-QA] فریم‌های کشیدن کمان: اگر bow.png سفارشی است ولی pulling ها نه،
    # عدم‌تطابق بصری رخ می‌دهد => سه فریم با فشردگی افقی فزاینده مشتق می‌شود
    # [v3.1] وجه کناری بلاک چمن: خاک البرز + نوار سبز هیرکانی در لبه بالا
    d_p = os.path.join(blk_dir, "dirt.png")
    t_p = os.path.join(blk_dir, "grass_block_top.png")
    side_p = os.path.join(blk_dir, "grass_block_side.png")
    if os.path.exists(d_p) and os.path.exists(t_p) and not os.path.exists(side_p):
        base = Image.open(d_p).convert("RGBA")
        top = Image.open(t_p).convert("RGBA")
        wh = base.width
        strip = np.asarray(top.resize((wh, wh)).crop((0, 0, wh, int(wh * 0.22))),
                           np.float32)
        lum = strip[..., :3].mean(-1, keepdims=True) / 255.0
        green = np.array([96, 158, 72], np.float32)  # سبز هیرکانی ثابت
        colored = np.dstack([np.clip(lum * green[None, None, :] * 1.55, 0, 255)
                             .astype(np.uint8), strip[..., 3].astype(np.uint8)])
        base.paste(Image.fromarray(colored, "RGBA"), (0, 0))
        save_png(base, side_p)
        n += 1
    bow_p = os.path.join(itm_dir, "bow.png")
    if os.path.exists(bow_p):
        bow = Image.open(bow_p).convert("RGBA")
        w, hgt = bow.size
        for idx, squeeze in enumerate([0.96, 0.88, 0.78]):
            frame = Image.new("RGBA", (w, hgt), (0, 0, 0, 0))
            sq = bow.resize((int(w * squeeze), hgt), Image.LANCZOS)
            frame.paste(sq, ((w - sq.width) // 2, 0), sq)
            save_png(frame, os.path.join(itm_dir, f"bow_pulling_{idx}.png"))
            n += 1
    print(f"[8.5] سیستم Fallback: {n} دارایی مشتق‌شده تولید شد ✔")


# ====================================== [v2] ۸.۶) اعتبارسنجی JSON و ارجاع‌ها
def validate_pack():
    """
    ممیزی خودکار: پارس تمام JSON ها + کنترل ارجاع تکسچر مدل‌ها.
    (ارجاع شکسته = تنها عامل واقعی تکسچر بنفش Missing در بازی)
    """
    bad = []
    checked = 0
    for root, _, files in os.walk(PACK):
        for f in files:
            if not f.endswith((".json", ".mcmeta")):
                continue
            p = os.path.join(root, f)
            try:
                with open(p, encoding="utf-8") as fh:
                    data = json.load(fh)
                checked += 1
            except Exception as e:
                bad.append(f"{p}: {e}")
                continue
            # کنترل ارجاع تکسچر مدل‌های آیتم
            for ref in (data.get("textures") or {}).values():
                name = ref.split("/")[-1]
                local = os.path.join(TEX, "item", name + ".png")
                # یا در خود پک موجود است یا وانیلا آن را دارد (whitelist)
                if not os.path.exists(local) and name not in (
                        SWORDS + ["bow", "golden_apple", "ender_pearl",
                                  "shield", "totem_of_undying", "arrow",
                                  "mace"]):
                    bad.append(f"{p}: ارجاع ناشناخته -> {ref}")
    if bad:
        for b in bad:
            print("  ✖", b)
        ERRORS.extend(bad)
    print(f"[8.6] اعتبارسنجی: {checked} فایل JSON سالم، {len(bad)} خطا ✔")


# ====================================== [v2] ۸.۷) فایل زبان فارسی fa_ir
def write_lang():
    """فارسی‌سازی نام آیتم‌های کلیدی پک (وقتی زبان بازی fa_ir باشد)."""
    lang = {
        "language.name": "فارسی — میراث پارسی",
        "language.region": "ایران",
        "item.minecraft.diamond_sword": "شمشیرِ فیروزه‌ی دمشقی",
        "item.minecraft.iron_sword": "شمشیرِ فولاد جوهردار",
        "item.minecraft.netherite_sword": "شمشیرِ شب‌فولاد",
        "item.minecraft.golden_sword": "شمشیرِ زرین هخامنشی",
        "item.minecraft.bow": "کمانِ پارسی",
        "item.minecraft.arrow": "تیرِ پارتی",
        "item.minecraft.golden_apple": "سیبِ زرینِ افسانه",
        "item.minecraft.enchanted_golden_apple": "سیبِ جاودانگی",
        "item.minecraft.ender_pearl": "گویِ فیروزه",
        "item.minecraft.shield": "سپرِ سپرداران",
        "item.minecraft.mace": "گرزِ رستم",
        "block.minecraft.obsidian": "آبسیدینِ دماوند",
        "block.minecraft.diamond_ore": "رگه‌ی فیروزه‌ی نیشابور",
        "block.minecraft.gold_ore": "رگه‌ی زرِ ساسانی",
        "block.minecraft.glass": "شیشه‌ی اروسی",
        "item.minecraft.totem_of_undying": "فَروَهَرِ جاودانی",
        "block.minecraft.stone": "سنگِ پارسه",
        "block.minecraft.stone_bricks": "سنگ‌نگاره‌ی تخت‌جمشید",
        "block.minecraft.bricks": "آجرِ یزدی",
        "block.minecraft.mud_bricks": "کاهگل",
        "block.minecraft.oak_planks": "تخته‌ی خاتم",
        "block.minecraft.sand": "شنِ کویر لوت",
        "block.minecraft.blue_glazed_terracotta": "کاشیِ اصفهان",
        "block.minecraft.gold_block": "بلوکِ زرِ هخامنشی",
        "block.minecraft.diamond_block": "بلوکِ فیروزه‌ی نیشابور",
        "itemGroup.combat": "رزم",
        "gui.done": "انجام شد",
    }
    lang_dir = ensure(os.path.join(PACK, "assets", "minecraft", "lang"))
    with open(os.path.join(lang_dir, "fa_ir.json"), "w", encoding="utf-8") as f:
        json.dump(lang, f, ensure_ascii=False, indent=2)
    print("[8.7] فایل زبان fa_ir.json نوشته شد ✔")


# ================================================ ۹) لوگو، بهینه‌سازی، ZIP
def build_logo():
    logo_src = os.path.join(SRC, "pack_logo.png")
    if os.path.exists(logo_src):
        im = Image.open(logo_src).convert("RGBA")
        im = ImageOps.fit(im, (512, 512), Image.LANCZOS)
        save_png(im, os.path.join(PACK, "pack.png"))
        print("[9b] pack.png (لوگو) ساخته شد ✔")


def audit_textures():
    """
    [v3-Phase1] ممیزی بی‌نقصی تکسچرها — خروجی: docs/qa-metrics.md
      • Seam Score: میانگین اختلاف رنگ لبه‌های مقابل (0 = بی‌درز مطلق)
      • Normal Sanity: میانگین کانال‌های نرمال باید ≈128 باشد
        (انحراف زیاد = نور پخته‌شده در نرمال‌مپ = مردود)
      • Roughness Split: کاشی صیقلی باید صاف‌تر از سنگ خام باشد
    """
    lines = ["# 📋 QA Metrics — Persian Legacy (خودکار، هر بیلد بازنویسی می‌شود)",
             "", "| تکسچر | Seam Score (<6 قبول) | Normal μ (≈128) | Smooth μ |",
             "|---|---|---|---|"]
    blk = os.path.join(TEX, "block")
    worst = 0.0
    for name in sorted(BLOCK_MATERIALS):
        p = os.path.join(blk, name + ".png")
        if not os.path.exists(p):
            continue
        a = np.asarray(Image.open(p).convert("RGB"), dtype=np.float32)
        seam = (np.abs(a[:, 0] - a[:, -1]).mean() +
                np.abs(a[0, :] - a[-1, :]).mean()) / 2
        worst = max(worst, seam)
        n_p = os.path.join(blk, name + "_n.png")
        s_p = os.path.join(blk, name + "_s.png")
        nmu = smu = "—"
        if os.path.exists(n_p):
            nn = np.asarray(Image.open(n_p))[..., :2].mean()
            nmu = f"{nn:.0f}"
            if abs(nn - 128) > 20:
                ERRORS.append(f"audit: نور پخته در نرمال {name} (μ={nn:.0f})")
        if os.path.exists(s_p):
            smu = f"{np.asarray(Image.open(s_p))[..., 0].mean():.0f}"
        flag = "✅" if seam < 6 else "⚠"
        lines.append(f"| {name} | {seam:.2f} {flag} | {nmu} | {smu} |")
    lines += ["", f"بدترین Seam Score: **{worst:.2f}** (آستانه قبول: 6.0)",
              "", "قاعده Roughness: کاشی/طلا/فیروزه صیقلی (Smooth μ بالا) و "
              "سنگ/شن خام زبر (Smooth μ پایین) — در جدول قابل راستی‌آزمایی است."]
    with open(os.path.join(ROOT, "docs", "qa-metrics.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[9d] ممیزی تکسچر: بدترین درز {worst:.2f} — docs/qa-metrics.md ✔")


# دسته‌هایی که کوانتیزاسیون پالت (منطق pngquant) رویشان بی‌خطر است:
# گرافیک تخت/کم‌رنگ — نه آلبدوی فتورئال و نه نرمال‌مپ (دقت بالا لازم دارند)
QUANT_SAFE = ("textures/gui", "textures/particle", "textures/misc",
              "textures/colormap", "_s.png")


def optimize_all():
    """
    [v3] بهینه‌سازی دومرحله‌ای:
      1) کوانتیزاسیون پالت تطبیقی (منطق pngquant) فقط روی دسته‌های امن
      2) فشرده‌سازی Lossless روی همه — بدون هیچ افت کیفیت قابل‌مشاهده
    """
    total = saved = 0
    for root, _, files in os.walk(PACK):
        for f in files:
            if not f.endswith(".png"):
                continue
            p = os.path.join(root, f)
            rel = p.replace("\\", "/")
            before = os.path.getsize(p)
            img = Image.open(p)
            if any(k in rel for k in QUANT_SAFE) and img.mode == "RGBA":
                q = img.quantize(colors=256, method=Image.FASTOCTREE, dither=0)
                # پذیرش فقط اگر بدون افت محسوس (خطای میانگین < 1.5/255)
                diff = np.abs(
                    np.asarray(q.convert("RGBA"), np.int16) -
                    np.asarray(img, np.int16)).mean()
                if diff < 1.5:
                    q.save(p, "PNG", optimize=True)
                else:
                    img.save(p, "PNG", optimize=True)
            else:
                img.save(p, "PNG", optimize=True)
            saved += before - os.path.getsize(p)
            total += 1
    print(f"[9c] {total} فایل PNG بهینه شد (صرفه‌جویی {saved/1024:.0f} KB) ✔")


def make_zip():
    ensure(RELEASE)
    zpath = os.path.join(RELEASE, "PersianLegacy-PvP-v1.0.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for root, _, files in os.walk(PACK):
            for f in files:
                p = os.path.join(root, f)
                z.write(p, os.path.relpath(p, PACK))
    size = os.path.getsize(zpath) / (1024 * 1024)
    print(f"[9/9] ZIP نهایی: {zpath} ({size:.1f} MB) ✔")


# ================================================================ اجرا
def main():
    ap = argparse.ArgumentParser(description="Persian Legacy PvP pack builder")
    # [v2/QA] پیش‌فرض 512 = تعادل طلایی PvP (۳۲ برابر وانیلا، بدون فشار رم)
    # برای نسخه نمایشی/عکاسی: --res 1024 یا --res 2048
    ap.add_argument("--res", type=int, default=512,
                    help="رزولوشن بلاک‌ها (512 پیش‌فرض PvP، 1024 نمایشی، 2048 اولترا)")
    ap.add_argument("--item-res", type=int, default=512, help="رزولوشن آیتم‌ها")
    ap.add_argument("--no-zip", action="store_true")
    args = ap.parse_args()

    print("═" * 60)
    print("  PERSIAN LEGACY v3.1 — Persian Photoreal PvP Pack Builder")
    print("═" * 60)
    # [v2] هر مرحله ایزوله اجرا می‌شود؛ خطای یک مرحله بیلد را متوقف نمی‌کند
    steps = [
        ("ساختار", build_structure, ()),
        ("mcmeta", write_mcmeta, ()),
        ("بلاک‌ها", build_blocks, (pot(args.res),)),
        ("آیتم‌ها", build_items, (pot(args.item_res),)),
        ("HUD", build_gui, ()),
        ("پارتیکل‌ها", build_particles, ()),
        ("Colormap", build_colormaps, ()),
        ("مدل‌های PvP", build_pvp_models, ()),
        ("Fallback", build_fallbacks, ()),
        ("زبان فارسی", write_lang, ()),
        ("محیط/آسمان", build_environment, ()),
        ("لوگو", build_logo, ()),
        ("اعتبارسنجی", validate_pack, ()),
        ("ممیزی تکسچر", audit_textures, ()),
        ("بهینه‌سازی", optimize_all, ()),
    ]
    for label, fn, fargs in steps:
        stage(label)(fn)(*fargs)
    if not args.no_zip:
        stage("ZIP")(make_zip)()
    if ERRORS:
        print(f"\n⚠ بیلد با {len(ERRORS)} هشدار تمام شد:")
        for e in ERRORS:
            print("  -", e)
        sys.exit(1)
    print("\n✅ ساخت پک بدون خطا کامل شد — پوشه: PersianLegacy/")


if __name__ == "__main__":
    main()
