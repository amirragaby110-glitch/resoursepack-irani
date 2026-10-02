# ⚔️ SHAMSHIR — Persian Combat Pack (مستندات فنی)

**نسخه:** Minecraft Java Edition **1.21.11** · `pack_format: 75` · رزولوشن پایه **16x**، آیتم‌های کلیدی **32x** · حجم ZIP: **~6.4MB**

## ساختار
```
PersianCombat/
├── pack.mcmeta                  ← pack_format 75 + supported_formats 48–99
├── pack.png                     ← لوگوی شمشیر+شمسه (256x)
└── assets/minecraft/
    ├── textures/
    │   ├── block/               ← 16x هارمونایز + کاشی/خاتم/اورهای اختصاصی
    │   ├── item/                ← 16x + سلاح‌های 32x
    │   ├── entity/              ← موب‌ها/equipment (زره تنی 1.21.2+)
    │   ├── gui/container/       ← همه‌ی GUIها (شنی/طلایی)
    │   ├── gui/sprites/hud/     ← 27+4 اسپرایت HUD ترسیمی
    │   ├── gui/sprites/widget/  ← دکمه‌های منو
    │   ├── particle/            ← کریت/هیت فیروزه-طلا
    │   ├── colormap/            ← بایوم هیرکانی/لوت/البرز
    │   └── misc/                ← جلای انچنت فیروزه
    ├── models/item/             ← 20 مدل JSON (شمشیر کوتاه و...)
    └── lang/fa_ir.json          ← نام‌های فارسی
```

## پالت رسمی
| نقش | رنگ |
|---|---|
| Persian Turquoise | `#40E0D0` (HUD، انچنت، الماس) |
| Lapis | `#264696` | Gold | `#E0B646` (قاب‌ها) |
| Warm Red | `#C43C36` | Sand | `#E0D3BA` (GUI) | Slate | `#2E3038` |

## بخش‌ها
1. **پایه (۲۹۸۶ فایل):** کل تکسچرهای 1.21.11 در 16x با «هارمونایز پالت» — Hue هر پیکسل ۳۸٪ به نزدیک‌ترین لنگر پارسی کشیده می‌شود؛ سبزها حفظ می‌شوند (حس وانیلا نمی‌شکند).
2. **PvP 32x:** ۶ شمشیرِ «شمشیر» (یک فرم، ۶ متریال‌تینت) + گرز؛ توتم فروهر؛ اندرپرل گوی بادگیر؛ ۸ شیشه کیمیاگری؛ سیب طلایی پراشباع + انچنتد با هاله فیروزه؛ فریم‌های کشیدن کمان.
3. **بلاک‌ها:** ۶ کاشی شاه‌عباسی seamless؛ میز خاتم؛ ۱۶ اور (۸+۸ دیپ‌اسلیت) با رگه‌های پراشباع؛ لو-فایر؛ آب آلفا ۶۲٪؛ گدازه پرکنتراست.
4. **GUI (۵۲۳ فایل):** بازرنگ خاکستری→شنی/طلایی با حفظ دقیق لی‌اوت (inventory, crafting, furnace, enchanting, anvil, chest/generic_54, و همه‌ی بقیه + دکمه‌ها).
5. **HUD:** قلب فیروزه (۱۱ حالت)، سپر طلا، انار، حباب، کراس‌هیر شمسه، XP فیروزه، هات‌بار خاتم با سلکتور فیروزه.

## نمونه JSON (شمشیر کوتاه — models/item/diamond_sword.json)
```json
{
  "parent": "minecraft:item/handheld",
  "textures": { "layer0": "minecraft:item/diamond_sword" },
  "display": {
    "firstperson_righthand": { "rotation": [0,-90,25], "translation": [1.0,2.2,0.8], "scale": [0.46,0.46,0.46] },
    "thirdperson_righthand": { "rotation": [0,-90,55], "translation": [0,3.5,0.5], "scale": [0.64,0.64,0.64] }
  }
}
```

## QA
184 فایل JSON معتبر · ZIP سالم (۳۷۰۰ فایل) · بازتولیدپذیر با `python3 tools/build_combat.py`
