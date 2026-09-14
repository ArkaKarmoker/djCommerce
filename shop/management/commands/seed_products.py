import os
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
import io

from shop.models import Category, Product, ProductVariant, ProductImage, Customer, Address, Review


def create_phone_mockup_image(phone_name, brand, bg_color=(240, 243, 246), accent_color=(79, 70, 229)):
    """
    Generate an appealing 600x600 phone graphic using Pillow.
    """
    img = Image.new('RGB', (600, 600), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Outer decorative glow / circle
    draw.ellipse([100, 100, 500, 500], fill=(255, 255, 255), outline=(226, 232, 240), width=2)

    # Phone Body (Rounded Rectangle)
    # [x0, y0, x1, y1]
    phone_rect = [190, 80, 410, 520]
    draw.rounded_rectangle(phone_rect, radius=36, fill=(15, 23, 42), outline=(100, 116, 139), width=4)

    # Phone Screen
    screen_rect = [204, 94, 396, 506]
    draw.rounded_rectangle(screen_rect, radius=26, fill=accent_color)

    # Dynamic Island / Camera punch hole
    draw.rounded_rectangle([270, 110, 330, 126], radius=8, fill=(15, 23, 42))

    # Screen UI Elements (mock cards)
    draw.rounded_rectangle([220, 150, 380, 250], radius=16, fill=(255, 255, 255))
    draw.rounded_rectangle([220, 270, 380, 370], radius=16, fill=(255, 255, 255))

    # Draw Brand on screen card
    draw.text((235, 170), f"djCommerce", fill=(79, 70, 229))
    draw.text((235, 200), f"5G • OLED", fill=(100, 116, 139))
    draw.text((235, 290), f"{brand}", fill=(15, 23, 42))
    draw.text((235, 320), f"Official Store", fill=(16, 185, 129))

    # Save to BytesIO
    buffer = io.BytesIO()
    img.save(buffer, format='PNG', quality=95)
    return buffer.getvalue()


class Command(BaseCommand):
    help = 'Seeds database with realistic smartphone categories and products'

    def handle(self, *args, **options):
        self.stdout.write("Starting djCommerce product seeding...")

        # 1. Categories
        categories_data = [
            {
                'name': 'Flagships',
                'slug': 'flagships',
                'icon': 'bi-stars',
                'description': 'Top-tier premium smartphones with maximum performance and pro cameras.'
            },
            {
                'name': 'Gaming Phones',
                'slug': 'gaming-phones',
                'icon': 'bi-controller',
                'description': 'High-refresh displays, active cooling, and ultra-responsive triggers.'
            },
            {
                'name': 'Foldables',
                'slug': 'foldables',
                'icon': 'bi-layout-split',
                'description': 'Innovative folding screens and dual-display productivity devices.'
            },
            {
                'name': 'Mid-Range',
                'slug': 'mid-range',
                'icon': 'bi-lightning-charge',
                'description': 'Balanced flagship features and high battery life at sensible prices.'
            },
            {
                'name': 'Budget Phones',
                'slug': 'budget-phones',
                'icon': 'bi-wallet2',
                'description': 'Reliable everyday mobile phones with great battery life and value.'
            }
        ]

        created_categories = {}
        for cat in categories_data:
            c, created = Category.objects.get_or_create(
                slug=cat['slug'],
                defaults={
                    'name': cat['name'],
                    'icon': cat['icon'],
                    'description': cat['description']
                }
            )
            created_categories[cat['slug']] = c
            status = "Created" if created else "Updated"
            self.stdout.write(f"Category {c.name}: {status}")

        # 2. Products
        products_data = [
            {
                'category_slug': 'flagships',
                'name': 'iPhone 16 Pro Max',
                'brand': 'Apple',
                'price': Decimal('1199.00'),
                'quantity': 15,
                'rating': Decimal('4.9'),
                'is_featured': True,
                'accent': (30, 41, 59),
                'short_description': 'A18 Pro chip, Grade 5 Titanium design, 48MP Fusion camera with 5x optical zoom.',
                'description': (
                    "The iPhone 16 Pro Max introduces a stunning Grade 5 Titanium design with thinner borders and the largest 6.9-inch Super Retina XDR display.\n\n"
                    "Key Specifications:\n"
                    "• Processor: Apple A18 Pro Bionic (3nm)\n"
                    "• Display: 6.9\" Super Retina XDR OLED, 120Hz ProMotion\n"
                    "• Camera: 48MP Main + 48MP Ultra Wide + 12MP 5x Telephoto\n"
                    "• Battery: Up to 33 hours video playback, MagSafe wireless\n"
                    "• Storage: 256GB / 512GB / 1TB\n"
                    "• Warranty: 1-Year Official Apple Warranty"
                )
            },
            {
                'category_slug': 'flagships',
                'name': 'Samsung Galaxy S25 Ultra',
                'brand': 'Samsung',
                'price': Decimal('1299.00'),
                'quantity': 12,
                'rating': Decimal('4.9'),
                'is_featured': True,
                'accent': (15, 23, 42),
                'short_description': 'Snapdragon 8 Elite, 200MP camera system, built-in S-Pen, Galaxy AI powerhouse.',
                'description': (
                    "The Galaxy S25 Ultra redefines mobile computing with cutting-edge Galaxy AI, flat titanium chassis, and legendary built-in S Pen stylus.\n\n"
                    "Key Specifications:\n"
                    "• Processor: Qualcomm Snapdragon 8 Elite (3nm)\n"
                    "• Display: 6.8\" Dynamic AMOLED 2X, 120Hz, 2600 nits peak\n"
                    "• Camera: 200MP Quad Telephoto System with 100x Space Zoom\n"
                    "• Battery: 5,000mAh with 45W Fast Charging\n"
                    "• Storage: 512GB UFS 4.0\n"
                    "• Warranty: 1-Year Official Samsung Warranty"
                )
            },
            {
                'category_slug': 'flagships',
                'name': 'Google Pixel 9 Pro XL',
                'brand': 'Google',
                'price': Decimal('1099.00'),
                'quantity': 10,
                'rating': Decimal('4.8'),
                'is_featured': True,
                'accent': (51, 65, 85),
                'short_description': 'Google Tensor G4, Gemini AI integrated, studio-quality HDR photo and video editing.',
                'description': (
                    "Google Pixel 9 Pro XL brings the best of Google AI directly to your hand with a sleek visor camera design and clean Pixel Experience OS.\n\n"
                    "Key Specifications:\n"
                    "• Processor: Google Tensor G4 with Titan M2 security\n"
                    "• Display: 6.8\" Super Actua LTPO OLED, 1-120Hz\n"
                    "• Camera: 50MP Main + 48MP 5x Telephoto + 48MP Ultrawide\n"
                    "• Battery: 5,060mAh with 37W Fast Charging\n"
                    "• OS: 7 Years of Android OS & Security Updates\n"
                    "• Warranty: 1-Year Official Google Hardware Warranty"
                )
            },
            {
                'category_slug': 'gaming-phones',
                'name': 'ASUS ROG Phone 8 Pro',
                'brand': 'ASUS ROG',
                'price': Decimal('999.00'),
                'quantity': 8,
                'rating': Decimal('4.8'),
                'is_featured': True,
                'accent': (220, 38, 38),
                'short_description': '165Hz AMOLED, AniMe Vision mini-LED matrix, AirTrigger ultrasonic touch buttons.',
                'description': (
                    "Designed for serious mobile gamers and esports competitors. Features rapid thermal dissipation and built-in ultrasonic shoulder triggers.\n\n"
                    "Key Specifications:\n"
                    "• Processor: Snapdragon 8 Gen 3 Gaming Edition\n"
                    "• Display: 6.78\" Samsung E6 AMOLED, 165Hz, 1ms response\n"
                    "• Memory: 16GB LPDDR5X RAM + 512GB Storage\n"
                    "• Audio: Stereo dual front-facing speakers with Dirac HD\n"
                    "• Battery: 5,500mAh Dual-Cell with 65W HyperCharge\n"
                    "• Warranty: 1-Year ASUS ROG Official Warranty"
                )
            },
            {
                'category_slug': 'gaming-phones',
                'name': 'Nubia RedMagic 9S Pro',
                'brand': 'Nubia',
                'price': Decimal('749.00'),
                'quantity': 14,
                'rating': Decimal('4.7'),
                'is_featured': False,
                'accent': (185, 28, 28),
                'short_description': 'ICE 13.5 Cooling Fan 22,000 RPM, true bezel-less under-display camera, 6500mAh.',
                'description': (
                    "Zero notch or camera punch-holes. A truly full-screen gaming phone with a built-in 22,000 RPM cooling fan and massive 6,500mAh battery.\n\n"
                    "Key Specifications:\n"
                    "• Processor: Leading Version Snapdragon 8 Gen 3\n"
                    "• Display: 6.8\" Full AMOLED, 120Hz, 100% Notchless\n"
                    "• Cooling: Built-in centrifugal turbofan + 10-layer VC\n"
                    "• Battery: 6,500mAh with 80W Fast Charging\n"
                    "• Warranty: 1-Year Official Warranty"
                )
            },
            {
                'category_slug': 'foldables',
                'name': 'Samsung Galaxy Z Fold 6',
                'brand': 'Samsung',
                'price': Decimal('1799.00'),
                'quantity': 6,
                'rating': Decimal('4.7'),
                'is_featured': True,
                'accent': (79, 70, 229),
                'short_description': 'Slim dual-screen folding design, Armor Aluminum frame, multi-tasking monster.',
                'description': (
                    "A cinema screen in your pocket. Unfold an 7.6-inch expansive dynamic AMOLED workspace for unmatched multitasking and tablet-like productivity.\n\n"
                    "Key Specifications:\n"
                    "• Cover Screen: 6.3\" Dynamic AMOLED 2X\n"
                    "• Main Screen: 7.6\" Foldable Dynamic AMOLED 2X, 120Hz\n"
                    "• Processor: Snapdragon 8 Gen 3 for Galaxy\n"
                    "• Water Resistance: IP48 Certified\n"
                    "• Warranty: 1-Year Official Samsung Care+"
                )
            },
            {
                'category_slug': 'foldables',
                'name': 'OnePlus Open',
                'brand': 'OnePlus',
                'price': Decimal('1499.00'),
                'quantity': 7,
                'rating': Decimal('4.8'),
                'is_featured': False,
                'accent': (22, 101, 52),
                'short_description': 'Virtually crease-free folding display, Hasselblad Triple Camera, Open Canvas multitasking.',
                'description': (
                    "Light, thin, and remarkably capable. Features the award-winning Open Canvas UI for running three full-screen apps simultaneously.\n\n"
                    "Key Specifications:\n"
                    "• Display: 7.82\" 2K Flexi-fluid AMOLED + 6.31\" Cover Display\n"
                    "• Camera: Hasselblad 48MP LYT-T808 + 64MP 3x Periscope\n"
                    "• Battery: 4,805mAh with 67W SUPERVOOC charging\n"
                    "• Warranty: 1-Year Official Warranty"
                )
            },
            {
                'category_slug': 'mid-range',
                'name': 'OnePlus 13',
                'brand': 'OnePlus',
                'price': Decimal('699.00'),
                'quantity': 20,
                'rating': Decimal('4.8'),
                'is_featured': False,
                'accent': (5, 150, 105),
                'short_description': 'Snapdragon 8 Elite, 6,000mAh Glacier Battery, 100W SuperVOOC, 2K Oriental Screen.',
                'description': (
                    "Flagship killer elevated to supreme status. Offers top-shelf performance, giant battery capacity, and IP68/IP69 water resistance.\n\n"
                    "Key Specifications:\n"
                    "• Processor: Qualcomm Snapdragon 8 Elite\n"
                    "• Display: 6.82\" 2K Oriental OLED, 120Hz ProXDR\n"
                    "• Battery: 6,000mAh Silicon-Carbon Glacier Battery\n"
                    "• Charging: 100W Wired + 50W AIRVOOC Wireless\n"
                    "• Warranty: 1-Year Official Warranty"
                )
            },
            {
                'category_slug': 'mid-range',
                'name': 'Nothing Phone (2)',
                'brand': 'Nothing',
                'price': Decimal('599.00'),
                'quantity': 18,
                'rating': Decimal('4.6'),
                'is_featured': False,
                'accent': (38, 38, 38),
                'short_description': 'Iconic Glyph Interface LEDs, clean Nothing OS 2.5, Snapdragon 8+ Gen 1.',
                'description': (
                    "Stand out with transparent aesthetics and interactive LED Glyph lighting on the rear glass. Super smooth, bloatware-free Android experience.\n\n"
                    "Key Specifications:\n"
                    "• Processor: Snapdragon 8+ Gen 1\n"
                    "• Display: 6.7\" Flexible LTPO OLED, 1-120Hz\n"
                    "• Unique Feature: 33 individually addressable Glyph LED zones\n"
                    "• Battery: 4,700mAh with 45W Fast Charging\n"
                    "• Warranty: 1-Year Official Warranty"
                )
            },
            {
                'category_slug': 'budget-phones',
                'name': 'Samsung Galaxy A55 5G',
                'brand': 'Samsung',
                'price': Decimal('399.00'),
                'quantity': 25,
                'rating': Decimal('4.6'),
                'is_featured': False,
                'accent': (37, 99, 235),
                'short_description': 'Metal frame design, 50MP OIS camera, Samsung Knox Vault, IP67 rating.',
                'description': (
                    "Premium glass and metal build at a friendly mid-tier price. Super AMOLED clarity paired with dependable 2-day battery life.\n\n"
                    "Key Specifications:\n"
                    "• Processor: Exynos 1480 with AMD Xclipse 530 GPU\n"
                    "• Display: 6.6\" Super AMOLED, 120Hz, Vision Booster\n"
                    "• Camera: 50MP Main with OIS + 12MP Ultrawide + 5MP Macro\n"
                    "• Battery: 5,000mAh with 25W Charging\n"
                    "• Warranty: 1-Year Official Samsung Warranty"
                )
            },
            {
                'category_slug': 'budget-phones',
                'name': 'Redmi Note 14 Pro+',
                'brand': 'Xiaomi Redmi',
                'price': Decimal('349.00'),
                'quantity': 22,
                'rating': Decimal('4.5'),
                'is_featured': False,
                'accent': (217, 119, 6),
                'short_description': '6200mAh titan battery, 200MP flagship sensor, 90W HyperCharge, curved AMOLED.',
                'description': (
                    "Unbeatable price-to-performance champion. Huge silicon-carbon battery and ultra-fast 90W charger included in the box.\n\n"
                    "Key Specifications:\n"
                    "• Processor: Snapdragon 7s Gen 3\n"
                    "• Display: 6.67\" 1.5K 120Hz Curved OLED, 3000 nits\n"
                    "• Battery: 6,200mAh with 90W HyperCharge\n"
                    "• Protection: Corning Gorilla Glass Victus 2, IP68\n"
                    "• Warranty: 1-Year Official Warranty"
                )
            }
        ]

        # Default demo customer
        demo_customer, _ = Customer.objects.get_or_create(
            phone="01712345678",
            defaults={
                'name': "Arka Karmoker",
                'address': "House 12, Road 4, Banani, Dhaka, Bangladesh",
                'email': "arka@example.com"
            }
        )
        demo_address, _ = Address.objects.get_or_create(
            address_line="House 12, Road 4, Banani",
            city="Dhaka",
            country="Bangladesh",
            postal_code="1213",
            is_default=True
        )
        demo_customer.addresses.add(demo_address)

        for p_data in products_data:
            cat = created_categories[p_data['category_slug']]
            product, created = Product.objects.get_or_create(
                name=p_data['name'],
                defaults={
                    'category': cat,
                    'brand': p_data['brand'],
                    'price': p_data['price'],
                    'quantity': p_data['quantity'],
                    'rating': p_data['rating'],
                    'is_featured': p_data['is_featured'],
                    'short_description': p_data['short_description'],
                    'description': p_data['description'],
                }
            )

            # Primary image
            if not product.image or created:
                image_bytes = create_phone_mockup_image(
                    phone_name=p_data['name'],
                    brand=p_data['brand'],
                    accent_color=p_data['accent']
                )
                filename = f"{p_data['name'].lower().replace(' ', '_').replace('(', '').replace(')', '').replace('+', 'plus')}.png"
                product.image.save(filename, ContentFile(image_bytes), save=True)

            # Seed Variants
            if not product.variants.exists():
                variants_list = [
                    {'name': f"{p_data['name']} (Black / 256GB)", 'color': 'Space Black', 'stock': 8, 'price_adj': Decimal('0.00')},
                    {'name': f"{p_data['name']} (Silver / 512GB)", 'color': 'Titanium Silver', 'stock': 5, 'price_adj': Decimal('100.00')},
                    {'name': f"{p_data['name']} (Special / 1TB)", 'color': 'Deep Edition', 'stock': 3, 'price_adj': Decimal('200.00')},
                ]
                for v in variants_list:
                    ProductVariant.objects.create(
                        product=product,
                        name=v['name'],
                        color=v['color'],
                        stock=v['stock'],
                        price_adjustment=v['price_adj']
                    )

            # Seed Gallery Images
            if not product.images.exists():
                # Add 2 extra angles
                for idx, angle_color in enumerate([(20, 184, 166), (99, 102, 241)], start=1):
                    gallery_bytes = create_phone_mockup_image(
                        phone_name=f"{p_data['name']} Angle {idx}",
                        brand=p_data['brand'],
                        accent_color=angle_color
                    )
                    gallery_img = ProductImage(product=product, alt_text=f"{p_data['name']} Angle {idx}")
                    gallery_img.product_image.save(f"{p_data['name'].lower().replace(' ', '_')}_angle_{idx}.png", ContentFile(gallery_bytes), save=True)

            # Seed Sample Review
            if not product.reviews.exists():
                Review.objects.create(
                    customer=demo_customer,
                    product=product,
                    rating=5,
                    comment=f"Amazing build quality and battery backup! Delivered within 24 hours in authentic sealed packaging from djCommerce."
                )

            status = "Created" if created else "Updated"
            self.stdout.write(f"Product '{product.name}': {status} (Variants & Gallery attached)")

        self.stdout.write(self.style.SUCCESS("djCommerce production seeding completed successfully!"))

