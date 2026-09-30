# ⚙️ PvP_Shader_Config — کانفیگ آماده برای SEUS PTGI و Kappa

هدف: نمایش کامل PBR پارسی (LabPBR) + پایداری FPS در PvP.
(راهنمای عمومی‌تر: [`shader-guide.md`](shader-guide.md))

---

## 🅐 Kappa Shaders (پیشنهاد اصلی برای PvP + PBR)

فایل: `.minecraft/shaderpacks/Kappa_v5.x.zip.txt` — مقادیر کلیدی:

```properties
# ---------- Material / PBR ----------
MATERIAL_FORMAT=1            # LabPBR 1.3 (فرمت نقشه‌های _n/_s این پک)
NORMAL_MAPPING=true          # نقش‌برجسته تخت‌جمشید
SPECULAR_MAPPING=true        # جلای کاشی اصفهان/طلا
EMISSION_MODE=1              # امیسیو LabPBR (درخشش فیروزه)
POM=false                    # ❌ در PvP خاموش (‑15% FPS)
POM_DEPTH=0.25               # اگر برای عکاسی روشن شد

# ---------- Lighting (تم کویر) ----------
SUNLIGHT_TEMPERATURE=5200    # آفتاب گرم کویری
SKY_SATURATION=1.10
AMBIENT_SKYLIGHT_BLUE=1.05   # سایه‌های مایل به فیروزه
GOLDEN_HOUR_INTENSITY=1.2

# ---------- Post (خوانایی PvP) ----------
BLOOM=true
BLOOM_INTENSITY=0.35         # کم — بلوم زیاد = کوری در فایت
MOTION_BLUR=false            # ❌ همیشه
DOF=false                    # ❌ همیشه
TAA=false                    # شبح‌زدگی در تعقیب بازیکن
FXAA=true
CONTRAST=1.03
SATURATION=1.06              # پاپ‌کردن فیروزه/طلا بدون خستگی چشم

# ---------- Performance ----------
SHADOW_RESOLUTION=2048
SHADOW_DISTANCE=96           # PvP در شعاع نزدیک است
VOLUMETRIC_LIGHT=false       # مه حجمی = پنهان شدن دشمن! ❌
CLOUD_QUALITY=1
WATER_REFLECTION_QUALITY=1
```

## 🅑 SEUS PTGI (فقط سینمایی/عکاسی — برای مسابقه توصیه نمی‌شود)

```properties
# ---------- PBR ----------
# SEUS PTGI HRR: فرمت را روی lab-PBR بگذارید
TEXTURE_RESOLUTION=512       # مطابق بیلد پیش‌فرض پک (1024 اگر --res 1024)
NORMAL_MAP_STRENGTH=1.0
SPECULAR_FORMAT=LABPBR
SMOOTH_LIGHTING=true

# ---------- GI / RT ----------
GI_RESOLUTION=0.5            # نصف = تعادل کیفیت/FPS
RAY_TRACING_QUALITY=Medium
PTGI_BOUNCES=2               # بازتاب طلایی کافی است؛ 3+ فقط برای رندر

# ---------- تم کویر ----------
ATMOSPHERE_DENSITY=0.85      # هوای خشک و شفاف لوت
SUN_TEMPERATURE=5300
TORCH_COLOR_TEMPERATURE=2600 # نور مشعل کاروانسرایی

# ---------- خاموش‌های اجباری PvP ----------
MOTION_BLUR=false
DOF=false
LENS_FLARE=false             # فلر روی Crosshair می‌افتد ❌
```

## 🅒 تنظیمات خود بازی (هر دو شیدر)

| گزینه | مقدار | دلیل |
|---|---|---|
| Mipmap Levels | **4** | LOD خودکار تکسچرهای دور → FPS پایدار (کلید حل پارادوکس پک سنگین) |
| Anisotropic Filtering | 4x | وضوح کاشی‌ها در زاویه تند بدون هزینه زیاد |
| Graphics | Fancy (نه Fabulous) | Fabulous با شیدر تداخل دارد |
| RAM | 512x → 4GB • 1024x → 6–8GB | جلوگیری از GC-lag وسط فایت |
| Render Distance | 8–12 در PvP | بیشتر = آپلود تکسچر بیشتر = استاتر |

## ✅ چک‌لیست ۱۰ ثانیه‌ای قبل از فایت
Motion Blur ❌ · DoF ❌ · Volumetric Fog ❌ · Lens Flare ❌ · POM ❌ · Bloom ≤ 0.35 ✔ · Mipmap 4 ✔ · TAA→FXAA ✔
