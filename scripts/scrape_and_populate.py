"""
scrape_and_populate.py
======================
Run with:
    .\venv\Scripts\python.exe scripts\scrape_and_populate.py

Scrapes selected branded products from applegadgetsbd.com and populates
the djCommerce DB with:
  - Real product data (name, brand, category, slug, specs as HTML table)
  - Real images saved to media/products/ and media/product_images/
  - Proper variant combinations (Color | Storage | Region) with real prices
  - Featured, New, and Offer homepage curations
"""

import os
import sys
import re
import json
import time
import django
import requests
from io import BytesIO
from pathlib import Path
from PIL import Image as PILImage
from django.core.files.base import ContentFile
from django.utils.text import slugify

# Django setup
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shop.models import (
    Category, Brand, Product, ProductVariant, ProductImage,
    FeaturedProduct, NewProduct, OfferProduct, Order, Review
)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
}
IMAGE_BASE = 'https://adminapi.applegadgetsbd.com/storage/media/large/'
REQUEST_DELAY = 1.5

TARGET_PRODUCTS = [
    # slug, cat_name, subcat_name, is_featured, is_new, is_offer
    ('iphone-16-pro-max',    'Smart Phone', 'Apple',   True,  False, False),
    ('iphone-16-pro',        'Smart Phone', 'Apple',   True,  False, False),
    ('iphone-16',            'Smart Phone', 'Apple',   False, True,  False),
    ('iphone-15-pro-max',    'Smart Phone', 'Apple',   False, False, True),
    ('iphone-15',            'Smart Phone', 'Apple',   False, False, False),
    ('iphone-13',            'Smart Phone', 'Apple',   False, False, True),
    ('galaxy-s24-ultra-5g',  'Smart Phone', 'SAMSUNG', True,  False, False),
    ('galaxy-s24-5g',        'Smart Phone', 'SAMSUNG', False, True,  False),
    ('galaxy-z-fold6',       'Smart Phone', 'SAMSUNG', True,  False, False),
    ('galaxy-z-flip6',       'Smart Phone', 'SAMSUNG', False, True,  False),
    ('galaxy-a55-5g',        'Smart Phone', 'SAMSUNG', False, False, True),
    ('pixel-9-pro-xl',       'Smart Phone', 'Google',  True,  False, False),
    ('pixel-9-pro',          'Smart Phone', 'Google',  False, True,  False),
    ('pixel-9',              'Smart Phone', 'Google',  False, True,  False),
    ('xiaomi-14-ultra',      'Smart Phone', 'Xiaomi',  True,  False, False),
    ('xiaomi-14',            'Smart Phone', 'Xiaomi',  False, True,  False),
    ('redmi-note-13-4g',     'Smart Phone', 'Xiaomi',  False, False, True),
    ('ipad-pro-m4-2024-11inch',           'Tablet', 'Apple',   True,  False, False),
    ('ipad-air-m2-2024-11inch',           'Tablet', 'Apple',   False, True,  False),
    ('ipad-10-9-10th-gen-2022',           'Tablet', 'Apple',   False, False, True),
    ('galaxy-tab-s9-ultra',               'Tablet', 'SAMSUNG', True,  False, False),
    ('xiaomi-pad-6',                      'Tablet', 'Xiaomi',  False, True,  False),
    ('apple-watch-series-10',             'Smart Watch', 'Apple',   True,  False, False),
    ('apple-watch-se-3',                  'Smart Watch', 'Apple',   False, False, True),
    ('galaxy-watch-ultra',                'Smart Watch', 'SAMSUNG', True,  False, False),
    ('galaxy-watch7',                     'Smart Watch', 'SAMSUNG', False, True,  False),
    ('amazfit-balance-2-smart-watch',     'Smart Watch', 'Amazfit', False, True,  False),
    ('pixel-watch-3-41mm',                'Smart Watch', 'Google',  False, True,  False),
    ('airpods-pro-2nd-generation-usbc',   'Audio', 'Airpods',  True,  False, False),
    ('apple-airpods-max',                 'Audio', 'Airpods',  False, False, True),
    ('sony-wh-1000xm5-wireless-noise-cancelling-headphones', 'Audio', 'Headphone', False, True, False),
    ('sony-wf-1000xm5-wireless-noise-cancelling-headphones', 'Audio', 'tws',       False, False, False),
    ('galaxy-buds3-pro',                  'Audio', 'tws',       False, True,  True),
    ('jbl-flip-6-portable-waterproof-speaker', 'Audio', 'Speakers', False, False, True),
    ('marshall-emberton-ii-portable-bluetooth-speaker', 'Audio', 'Speakers', False, False, False),
    ('apple-20w-usb-c-power-adapter',     'Accessories', 'adapters', False, False, True),
    ('samsung-45w-pd-power-adapter-with-5a-usb-type-c-to-c-cable', 'Accessories', 'adapters', False, False, True),
    ('dji-osmo-pocket-3',                 'Gadgets', 'Lifestyle', False, True,  False),
    ('dualsense-wireless-controller-for-playstation-5', 'Gadgets', 'Gaming', False, False, True),
]


def fetch_product_data(slug):
    url = f'https://www.applegadgetsbd.com/product/{slug}'
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
    except Exception as e:
        print(f'  [ERR] Request failed for {slug}: {e}')
        return None

    if r.status_code != 200:
        print(f'  [ERR] HTTP {r.status_code} for {slug}')
        return None

    html = r.text
    chunks = re.findall(r'self\.__next_f\.push\(\[1,\s*"(.*?)"\]\)', html, re.DOTALL)
    full_str = ''
    for c in chunks:
        try:
            full_str += c.encode('utf-8').decode('unicode_escape')
        except Exception:
            full_str += c.replace('\\"', '"').replace('\\\\', '\\')

    start_pos = full_str.find('"product":{"id":')
    if start_pos == -1:
        print(f'  [ERR] product JSON not found for {slug}')
        return None

    start_obj = start_pos + len('"product":')
    depth = 0
    end_pos = start_obj
    for i, ch in enumerate(full_str[start_obj:], start=start_obj):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end_pos = i + 1
                break

    try:
        return json.loads(full_str[start_obj:end_pos])
    except Exception as e:
        print(f'  [ERR] JSON parse error for {slug}: {e}')
        return None


def build_specs_html(specifications):
    if not specifications:
        return ''
    rows = []
    for s in specifications:
        label = s.get('name', '').strip()
        value = s.get('pivot', {}).get('details', '').strip()
        if label and value:
            rows.append(
                f'<tr><th style="width:30%;vertical-align:top;padding:6px 10px;background:#f8f9fa;">'
                f'{label}</th>'
                f'<td style="padding:6px 10px;">{value}</td></tr>'
            )
    if not rows:
        return ''
    return (
        '<table class="table table-bordered" '
        'style="font-size:0.9rem;width:100%;border-collapse:collapse;">'
        '<tbody>' + ''.join(rows) + '</tbody></table>'
    )


def download_image(file_name):
    for fmt in [file_name]:
        url = IMAGE_BASE + fmt
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200 and len(r.content) > 1000:
                try:
                    img = PILImage.open(BytesIO(r.content))
                    if img.mode in ('RGBA', 'P', 'LA'):
                        img = img.convert('RGB')
                    buf = BytesIO()
                    img.save(buf, format='JPEG', quality=85)
                    return ContentFile(buf.getvalue()), '.jpg'
                except Exception:
                    return ContentFile(r.content), os.path.splitext(fmt)[1] or '.jpg'
        except Exception:
            pass
    return None, None


def get_or_create_category(cat_name, subcat_name):
    parent = Category.objects.filter(name__iexact=cat_name, parent__isnull=True).first()
    if not parent:
        parent = Category.objects.create(name=cat_name)

    if subcat_name:
        sub = Category.objects.filter(name__iexact=subcat_name, parent=parent).first()
        if not sub:
            sub = Category.objects.create(name=subcat_name, parent=parent)
        return sub
    return parent


def build_variants(raw_variants):
    seen = {}
    first_featured_name = None

    for v in raw_variants:
        prices_list = v.get('prices', [])
        if not prices_list:
            continue
        price_val = prices_list[0].get('price', {}).get('value', 0)
        comp_val = prices_list[0].get('compare_price', {}).get('value', 0)
        if price_val <= 0:
            continue

        values = v.get('values', [])
        color = storage = region = ''
        for val in values:
            opt_name = val.get('option', {}).get('name', {}).get('en', '').lower()
            val_name = val.get('name', {}).get('en', '').strip()
            if 'color' in opt_name:
                color = val_name
            elif 'storage' in opt_name or 'size' in opt_name or 'rom' in opt_name:
                storage = val_name
            elif 'region' in opt_name:
                region = val_name

        parts = [p for p in [color, storage, region] if p]
        combo_name = ' | '.join(parts) if parts else 'Standard'
        status = v.get('status', 'in-stock')
        is_available = status == 'in-stock'
        featured = v.get('featured', 0)
        quantity = 10 if is_available else 0

        vd = {
            'name': combo_name,
            'price': price_val,
            'regular_price': comp_val if comp_val > price_val else None,
            'quantity': quantity,
            'is_available': is_available,
            'is_default': False,
            '_featured': featured,
        }

        if combo_name not in seen or (featured and not seen[combo_name].get('_featured')):
            seen[combo_name] = vd
            if featured and not first_featured_name:
                first_featured_name = combo_name

    result = list(seen.values())
    if not result:
        return []

    # Mark default
    default_set = False
    if first_featured_name and first_featured_name in seen and seen[first_featured_name]['is_available']:
        seen[first_featured_name]['is_default'] = True
        default_set = True
    if not default_set:
        for vd in result:
            if vd['is_available']:
                vd['is_default'] = True
                default_set = True
                break
    if not default_set and result:
        result[0]['is_default'] = True

    result.sort(key=lambda x: (-x['is_default'], -x['price']))
    return result


def wipe_catalog():
    print('\n[WIPE] Clearing old catalog (keeping order references)...')
    FeaturedProduct.objects.all().delete()
    NewProduct.objects.all().delete()
    OfferProduct.objects.all().delete()
    Review.objects.all().delete()

    products_in_orders = set(Order.objects.values_list('product_id', flat=True))
    print(f'  Products referenced in orders: {len(products_in_orders)} (keeping)')

    for img in ProductImage.objects.all():
        try:
            if img.product_image and img.product_image.name and os.path.exists(img.product_image.path):
                os.remove(img.product_image.path)
        except Exception:
            pass

    for prod in Product.objects.exclude(id__in=products_in_orders):
        try:
            if prod.image and prod.image.name and os.path.exists(prod.image.path):
                os.remove(prod.image.path)
        except Exception:
            pass

    Product.objects.exclude(id__in=products_in_orders).delete()
    print('[WIPE] Done.\n')
    return products_in_orders


def import_product(slug, cat_name, subcat_name, is_featured, is_new, is_offer, products_in_orders):
    print(f'\n>> Importing: {slug}')
    data = fetch_product_data(slug)
    if not data:
        return None

    name = data.get('attribute_data', {}).get('name', {}).get('en', '').strip()
    if not name:
        print(f'  [SKIP] No name found for {slug}')
        return None

    brand_name = data.get('brand', {}).get('attribute_data', {}).get('name', '').strip()
    raw_variants = data.get('variants', [])
    media_list = data.get('media', [])
    specs = data.get('specifications', [])

    print(f'  Name: {name} | Brand: {brand_name}')
    print(f'  Raw variants: {len(raw_variants)} | Images: {len(media_list)} | Specs: {len(specs)}')

    category = get_or_create_category(cat_name, subcat_name)
    brand_str = brand_name if brand_name else cat_name
    specs_html = build_specs_html(specs)

    base_slug = slug
    final_slug = base_slug
    counter = 1
    while Product.objects.filter(slug=final_slug).exists():
        final_slug = f'{base_slug}-{counter}'
        counter += 1

    short_desc = f'Genuine {brand_name} {name}' if brand_name else f'Genuine {name}'

    product = Product.objects.create(
        name=name,
        slug=final_slug,
        brand=brand_str,
        category=category,
        short_description=short_desc,
        description=specs_html,
        rating=4.8,
        is_featured=is_featured,
    )

    # Images
    main_image_saved = False
    gallery_count = 0
    for i, media in enumerate(media_list[:5]):
        file_name = media.get('file_name', '')
        if not file_name:
            continue
        img_content, ext = download_image(file_name)
        if img_content is None:
            continue
        safe_name = re.sub(r'[^a-zA-Z0-9\-_]', '_', os.path.splitext(file_name)[0]) + ext
        try:
            if not main_image_saved:
                product.image.save(safe_name, img_content, save=True)
                main_image_saved = True
                print(f'  [IMG] Main: {safe_name}')
            else:
                pi = ProductImage(product=product, alt_text=name)
                pi.product_image.save(safe_name, img_content, save=True)
                gallery_count += 1
        except Exception as e:
            print(f'  [IMG ERR] {safe_name}: {e}')
        time.sleep(0.2)

    print(f'  [IMG] Gallery images saved: {gallery_count}')

    # Variants
    processed_variants = build_variants(raw_variants)
    if not processed_variants:
        ProductVariant.objects.create(
            product=product, name='Standard', price=9999,
            quantity=10, is_available=True, is_default=True,
        )
        print(f'  [VAR] 1 fallback variant')
    else:
        processed_variants = processed_variants[:12]
        for vd in processed_variants:
            ProductVariant.objects.create(
                product=product,
                name=vd['name'],
                price=vd['price'],
                regular_price=vd['regular_price'],
                quantity=vd['quantity'],
                is_available=vd['is_available'],
                is_default=vd['is_default'],
            )
        print(f'  [VAR] {len(processed_variants)} variants created')

    return product


def main():
    print('='*60)
    print('djCommerce Catalog Scraper & Importer')
    print('='*60)

    products_in_orders = wipe_catalog()

    featured_products = []
    new_products = []
    offer_products = []
    imported = []
    failed = []

    for (slug, cat_name, subcat_name, is_featured, is_new, is_offer) in TARGET_PRODUCTS:
        try:
            product = import_product(slug, cat_name, subcat_name, is_featured, is_new, is_offer, products_in_orders)
            if product:
                imported.append(product)
                if is_featured:
                    featured_products.append(product)
                if is_new:
                    new_products.append(product)
                if is_offer:
                    offer_products.append(product)
            else:
                failed.append(slug)
        except Exception as e:
            print(f'  [ERR] Exception importing {slug}: {e}')
            import traceback; traceback.print_exc()
            failed.append(slug)
        time.sleep(REQUEST_DELAY)

    # Homepage curations
    print('\n[CURATION] Setting up homepage sections...')
    for i, p in enumerate(featured_products[:8]):
        FeaturedProduct.objects.get_or_create(product=p, defaults={'order': i})
    for i, p in enumerate(new_products[:8]):
        NewProduct.objects.get_or_create(product=p, defaults={'order': i})

    offer_with_discount = [p for p in imported if p.discount_amount and p.discount_amount > 0]
    offer_set = list({p.id: p for p in (offer_with_discount + offer_products)}.values())
    for i, p in enumerate(offer_set[:8]):
        OfferProduct.objects.get_or_create(product=p, defaults={'order': i})

    print('\n' + '='*60)
    print('IMPORT COMPLETE')
    print(f'  Successfully imported: {len(imported)} products')
    print(f'  Failed / Skipped:      {len(failed)} products')
    if failed:
        print(f'  Failed slugs: {failed}')
    print(f'  Featured:  {FeaturedProduct.objects.count()}')
    print(f'  New:       {NewProduct.objects.count()}')
    print(f'  Offers:    {OfferProduct.objects.count()}')
    print(f'  Total Products in DB: {Product.objects.count()}')
    print(f'  Total Variants in DB: {ProductVariant.objects.count()}')
    print('='*60)


if __name__ == '__main__':
    main()
