from django.core.management.base import BaseCommand
from django.utils.text import slugify
from shop.models import Category, Product, ProductVariant

class Command(BaseCommand):
    help = "Seed categories, subcategories, and link products according to user specification."

    def handle(self, *args, **options):
        self.stdout.write("Seeding categories and subcategories...")

        # Exact specification dictionary
        cat_data = {
            "Smart Phone": {
                "icon": "bi-phone",
                "subcategories": [
                    "Apple", "Google", "HONOR", "Huawei", "MOTOROLA", "Nokia",
                    "NOTHING", "OnePlus", "oppo", "Others", "Realme", "SAMSUNG",
                    "vivo", "Xiaomi"
                ]
            },
            "Tablet": {
                "icon": "bi-tablet",
                "subcategories": [
                    "Amazon", "Apple", "HONOR", "Huawei", "OnePlus", "Others",
                    "SAMSUNG", "Xiaomi"
                ]
            },
            "Audio": {
                "icon": "bi-headphones",
                "subcategories": [
                    "Airpods", "tws", "Headphone", "Speakers", "headset"
                ]
            },
            "Smart Watch": {
                "icon": "bi-smartwatch",
                "subcategories": [
                    "Amazfit", "Apple", "Fastrack", "Fitbit", "Google", "Haylou",
                    "HONOR", "Huawei", "Joyroom", "Kieslect", "MOTOROLA", "NOTHING",
                    "OnePlus", "oraimo", "Others", "Realme", "SAMSUNG", "WiWU", "Xiaomi"
                ]
            },
            "Accessories": {
                "icon": "bi-plug",
                "subcategories": [
                    "adapters", "screen protector", "case", "powerbank", "others"
                ]
            }
        }

        category_map = {}
        subcategory_map = {}

        for main_name, data in cat_data.items():
            main_slug = slugify(main_name)
            main_cat, _ = Category.objects.get_or_create(
                slug=main_slug,
                defaults={
                    "name": main_name,
                    "icon": data["icon"],
                    "description": f"Explore premium {main_name} collection at djCommerce."
                }
            )
            main_cat.name = main_name
            main_cat.icon = data["icon"]
            main_cat.parent = None
            main_cat.save()
            category_map[main_name] = main_cat
            self.stdout.write(self.style.SUCCESS(f"Main Category: {main_name}"))

            for sub_name in data["subcategories"]:
                sub_slug = slugify(f"{main_slug}-{sub_name}")
                sub_cat, _ = Category.objects.get_or_create(
                    slug=sub_slug,
                    defaults={
                        "name": sub_name,
                        "parent": main_cat,
                        "icon": "bi-chevron-right",
                        "description": f"{sub_name} in {main_name}"
                    }
                )
                sub_cat.name = sub_name
                sub_cat.parent = main_cat
                sub_cat.save()
                subcategory_map[(main_name, sub_name.lower())] = sub_cat

        # Map existing smartphones to Smart Phone and their respective subcategories
        smart_phone_cat = category_map["Smart Phone"]
        for prod in Product.objects.all():
            brand_clean = (prod.brand or "").strip().lower()
            # If product is a phone, categorize under Smart Phone
            matched_sub = None
            for sub_name in cat_data["Smart Phone"]["subcategories"]:
                if sub_name.lower() in brand_clean or brand_clean == sub_name.lower():
                    matched_sub = subcategory_map.get(("Smart Phone", sub_name.lower()))
                    break
            
            if not matched_sub and "iphone" in prod.name.lower():
                matched_sub = subcategory_map.get(("Smart Phone", "apple"))
            
            if matched_sub:
                prod.category = matched_sub
                prod.save()
            elif prod.category is None or prod.category.parent is None:
                # Default to Others subcategory under Smart Phone if it's a phone
                prod.category = subcategory_map.get(("Smart Phone", "others")) or smart_phone_cat
                prod.save()

        # Seed sample items for Tablet, Audio, Smart Watch, Accessories if needed
        self._seed_sample_devices(category_map, subcategory_map)

        self.stdout.write(self.style.SUCCESS("All categories and subcategories created successfully!"))

    def _seed_sample_devices(self, category_map, subcategory_map):
        sample_catalog = [
            # Tablets
            {
                "name": "iPad Pro 13-inch M4",
                "brand": "Apple",
                "price": 178000,
                "regular_price": 185000,
                "main_cat": "Tablet",
                "sub_cat": "apple",
                "short": "Ultra Retina XDR OLED display, Apple M4 chip, Thunderbolt / USB 4 support.",
                "image_path": "products/iphone_16_pro_max_natural.png"
            },
            {
                "name": "Samsung Galaxy Tab S10 Ultra",
                "brand": "SAMSUNG",
                "price": 142000,
                "regular_price": 149000,
                "main_cat": "Tablet",
                "sub_cat": "samsung",
                "short": "14.6-inch Dynamic AMOLED 2X, MediaTek Dimensity 9300+, S Pen included.",
                "image_path": "products/galaxy-s25-ultra-silver.png"
            },
            {
                "name": "Xiaomi Pad 6 Pro",
                "brand": "Xiaomi",
                "price": 46500,
                "regular_price": 49000,
                "main_cat": "Tablet",
                "sub_cat": "xiaomi",
                "short": "11-inch 144Hz 2.8K display, Snapdragon 8+ Gen 1, 8600mAh battery.",
                "image_path": "products/xiaomi-15-ultra.png"
            },
            # Audio
            {
                "name": "Apple AirPods Pro 2 (USB-C)",
                "brand": "Apple",
                "price": 27500,
                "regular_price": 29500,
                "main_cat": "Audio",
                "sub_cat": "airpods",
                "short": "Active Noise Cancellation up to 2x more, Adaptive Audio, USB-C MagSafe Case.",
                "image_path": "products/iphone-16-plus.png"
            },
            {
                "name": "Sony WH-1000XM5 Wireless Headphones",
                "brand": "Sony",
                "price": 38500,
                "regular_price": 42000,
                "main_cat": "Audio",
                "sub_cat": "headphone",
                "short": "Industry Leading Noise Canceling with two processors and 8 microphones.",
                "image_path": "products/iphone_16_black.png"
            },
            {
                "name": "JBL Charge 5 Portable Bluetooth Speaker",
                "brand": "JBL",
                "price": 18500,
                "regular_price": 20000,
                "main_cat": "Audio",
                "sub_cat": "speakers",
                "short": "Bold JBL Original Pro Sound, 20 Hours Playtime, IP67 Waterproof and Dustproof.",
                "image_path": "products/iphone_16_pro_max_desert.png"
            },
            # Smart Watch
            {
                "name": "Apple Watch Ultra 2 (GPS + Cellular)",
                "brand": "Apple",
                "price": 98000,
                "regular_price": 105000,
                "main_cat": "Smart Watch",
                "sub_cat": "apple",
                "short": "49mm Titanium case, Precision dual-frequency GPS, up to 36 hours battery life.",
                "image_path": "products/iphone_16_pro_max_white.png"
            },
            {
                "name": "Samsung Galaxy Watch Ultra",
                "brand": "SAMSUNG",
                "price": 72000,
                "regular_price": 78000,
                "main_cat": "Smart Watch",
                "sub_cat": "samsung",
                "short": "Grade 4 Titanium cushion frame, 10ATM water resistance, dual-frequency GPS.",
                "image_path": "products/galaxy-s24-ultra.png"
            },
            {
                "name": "Amazfit Balance Smartwatch",
                "brand": "Amazfit",
                "price": 24500,
                "regular_price": 26500,
                "main_cat": "Smart Watch",
                "sub_cat": "amazfit",
                "short": "Mind & Body Readiness Analysis, Body Composition Measurement, Dual-band GPS.",
                "image_path": "products/pixel-9-pro.png"
            },
            # Accessories
            {
                "name": "Apple 20W USB-C Power Adapter",
                "brand": "Apple",
                "price": 2800,
                "regular_price": 3200,
                "main_cat": "Accessories",
                "sub_cat": "adapters",
                "short": "Fast, efficient charging at home, in the office, or on the go for iPhone & iPad.",
                "image_path": "products/iphone-16.png"
            },
            {
                "name": "Anker Prime 20,000mAh Power Bank (200W)",
                "brand": "Anker",
                "price": 14500,
                "regular_price": 16000,
                "main_cat": "Accessories",
                "sub_cat": "powerbank",
                "short": "200W Total Output, Ultra-Compact Design, Smart Digital Display.",
                "image_path": "products/iphone-15-pro-max.png"
            },
            {
                "name": "Spigen Ultra Hybrid MagSafe Case for iPhone",
                "brand": "Spigen",
                "price": 3200,
                "regular_price": 3600,
                "main_cat": "Accessories",
                "sub_cat": "case",
                "short": "Crystal clear transparency with built-in magnetic ring for MagSafe compatibility.",
                "image_path": "products/iphone-15.png"
            }
        ]

        for item in sample_catalog:
            sub = subcategory_map.get((item["main_cat"], item["sub_cat"]))
            if not sub:
                sub = category_map[item["main_cat"]]
            
            p, created = Product.objects.get_or_create(
                name=item["name"],
                defaults={
                    "category": sub,
                    "brand": item["brand"],
                    "price": item["price"],
                    "regular_price": item["regular_price"],
                    "short_description": item["short"],
                    "description": f"<h3>{item['name']}</h3><p>{item['short']}</p><p>Authentic official warranty at djCommerce.</p>",
                    "quantity": 15,
                    "rating": 4.9,
                    "is_featured": True,
                    "image": item["image_path"]
                }
            )
            if not created:
                p.category = sub
                p.save()
