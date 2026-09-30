# 📋 چک‌لیست شکاف دارایی‌ها (Asset Gap Analysis)

وضعیت‌ها: ✅ اختصاصی ساخته شد | 🟡 با Fallback تماتیک پوشش داده شد | 🔴 نیازمند آرت AI (پرامپت آماده در `expansion-prompts.md`) | ⚪ وانیلا می‌ماند (کم‌اهمیت برای تم/PvP)

## بلاک‌ها
| دارایی | وضعیت |
|---|---|
| stone / cobblestone / stone_bricks / bricks / oak_planks / sand / dirt / blue_glazed_terracotta / gold_block / diamond_block | ✅ + PBR |
| deepslate ×2، smooth_stone، andesite/diorite/granite، sandstone ×3، cracked/mossy_stone_bricks، planks ×۸ گونه (چری/بامبو/...)، gravel، mud_bricks (کاهگل) | 🟡 مشتق خودکار + PBR |
| grass_block top (tint-safe خاکستری) + side (کامپوزیت خودکار) | ✅ v3.1 |
| water/lava (استریپ انیمیشن + `.mcmeta`) | 🔴 |
| diamond_ore (فیروزه نیشابور) / gold_ore (زر ساسانی) | ✅ v3.1 |
| iron_ore, copper_ore, redstone_ore, ... | 🔴 |
| بلاک‌های مس/۱.۲۱ (copper family, tuff, trial spawner) | 🔴 |
| glass (اروسی، مرکز شفاف PvP) / obsidian (دماوند) / netherrack | ✅ v3.1 |
| end_stone | 🔴 |

## آیتم‌ها
| دارایی | وضعیت |
|---|---|
| diamond_sword, iron_sword, bow (+۳ فریم کشش), golden_apple, ender_pearl | ✅ |
| netherite/golden/stone/wooden_sword | 🟡 مشتق رنگی از شمشیرهای اصلی |
| arrow (تیر پارتی), shield (سپر فروهر + مدل تخت 2D PvP), totem (فروهر), mace (گرز رستم ۱.۲۱ + مدل) | ✅ v3.1 |
| trident, crossbow, fishing_rod, axe ها | 🔴 |
| زره‌ها (item + `models/armor/*_layer_1/2`) + trim ها | 🔴 |
| elytra (بال سیمرغ) | 🔴 |

## ماب‌ها (Entities) — همه 🔴
zombie (جنگجوی مومیایی کویر)، skeleton (کماندار هخامنشی)، stray، villager/wandering_trader (بازرگان پارسی)، enderman (دیو شب)، ender_dragon (**سیمرغ**)، iron_golem (**لاماسو**)، horse (اسب کاسپین)، wolf (سگ سارابی)، creeper، witch، piglin/blaze

## UI / HUD
| دارایی | وضعیت |
|---|---|
| icons.png (قلب/آرمور/XP/Crosshair)، widgets.png (Hotbar/سلکتور) | ✅ |
| gui/container/* (inventory, crafting, chest, ...) | 🔴 (عمداً وانیلا مانده تا با پلاگین‌های سرور تداخل نکند — تغییر اختیاری) |
| فونت فارسی (`font/default.json` + گلیف‌های fa) | 🔴 |
| gui/title/minecraft.png (لوگوی منو) | 🔴 |

## محیط و صدا
| دارایی | وضعیت |
|---|---|
| sun, moon_phases (۸ فاز خودکار), sky day/night (OptiFine), colormap ها, آب فیروزه‌ای | ✅ |
| rain/snow استریپ | ⚪ |
| صداها (نیازمند فایل .ogg واقعی — ضربه شمشیر «چکاچک فولاد جوهردار»، کمان، سنتور در منو) | 🔴 خارج از توان تولید تصویری؛ ساختار `sounds.json` در اسکریپت v3 پشتیبانی می‌شود، فایل صوتی باید ضبط/تهیه شود |
| lang/fa_ir.json | ✅ نمونه ۲۵ کلیدی |

## اولویت‌بندی پیشنهادی برای فاز بعد (PvP-Critical اول)
2. 🔴 zombie / skeleton — پرتکرارترین ماب‌ها
3. 🔴 armor layers (زره فلس هخامنشی)
4. 🔴 ore ها + glass + obsidian
5. 🔴 ender_dragon سیمرغ + elytra (پرستیژ پک!)
