# 🌇 راهنمای تنظیمات شیدر — Persian Legacy PvP

هدف: **حداکثر جلوه‌ی تم ایرانی (فیروزه/طلا/کویر) + حداکثر FPS در PvP**

## شیدر پیشنهادی

| اولویت | شیدر | چرا؟ |
|---|---|---|
| 🥇 PvP رقابتی | **Complementary Reimagined** (پروفایل Performance) | کمترین Input-lag، پشتیبانی کامل LabPBR |
| 🥈 تعادل | **BSL Shaders** | رنگ‌های گرم کویری فوق‌العاده |
| 🥉 سینمایی | **SEUS PTGI / Rethinking Voxels** | فقط برای اسکرین‌شات — نه PvP! |

## ⚙️ تنظیمات کلیدی (Complementary / BSL)

### Material / PBR — فعال‌سازی نقشه‌های LabPBR پک
- `Material Format` → **LabPBR 1.3**
- `Normal Maps` → **ON** (نقش‌برجسته‌های تخت جمشید زنده می‌شوند)
- `Specular / Reflections` → **ON** — کاشی اصفهان و بلاک طلا جلای واقعی می‌گیرند
- `Emissive / Glowing Ores` → **ON** (درخشش ملایم بلاک فیروزه)
- `Parallax Occlusion (POM)` → ❌ **OFF برای PvP** (تا 15٪ FPS می‌گیرد) — فقط برای عکاسی روشن کنید

### رنگ و نور (تم کویری)
- `Sunlight Color` → گرم‌تر: R 1.00 / G 0.93 / B 0.80 (آفتاب کویر)
- `Ambient / Sky Color Multiplier` → +5٪ آبی (فیروزه‌ای شدن سایه‌ها)
- `Saturation` → 1.05 تا 1.10 (کاشی‌ها بدرخشند)
- `Bloom` → **کم (0.3–0.5)** — بلوم زیاد در PvP دید را کور می‌کند!

### ⚡ بهینه‌سازی PvP (حیاتی)
- `Shadow Distance` → **96–120** (بیشتر = لگ بی‌دلیل)
- `Shadow Quality` → 1.0x
- `Motion Blur` → ❌ OFF (سم مطلق برای PvP)
- `Depth of Field` → ❌ OFF
- `Water Reflection Quality` → Medium
- `Anti-Aliasing (TAA)` → **FXAA** به‌جای TAA (شبح‌زدگی TAA در تعقیب بازیکن مزاحم است)

### تنظیمات خود ماینکرفت (Video Settings)
- `Mipmap Levels` → **4** (پک از رزولوشن توان-۲ استفاده می‌کند => دورها خودکار سبک لود می‌شوند و FPS پایدار می‌ماند)
- `Anisotropic Filtering` → 4x
- `Graphics` → Fancy (نه Fabulous — Fabulous با شیدر تداخل دارد)
- اختصاص RAM: **6–8 GB** برای نسخه 1024x (پک‌های HD رم می‌خواهند)
- نسخه سبک: اگر FPS پایین بود پک را با `--res 512` دوباره بسازید:
  ```bash
  python3 tools/build_pack.py --res 512
  ```

## 🎯 چک‌لیست قبل از مسابقه
1. Motion Blur / DoF خاموش ✔
2. POM خاموش ✔
3. Mipmap = 4 ✔
4. Bloom ≤ 0.5 ✔
5. FPS پایدار بالای ریفرش‌ریت مانیتور ✔
