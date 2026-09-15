from decimal import Decimal
from django.conf import settings
from .models import Product, ProductVariant


class Cart:
    """
    Session-based shopping cart for djCommerce supporting both products and variants.
    """
    SESSION_KEY = 'cart_session'

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(self.SESSION_KEY)
        if not cart:
            cart = self.session[self.SESSION_KEY] = {}
        self.cart = cart

    def add(self, product, quantity=1, variant=None, override_quantity=False):
        """
        Add a product (and optional variant) to the cart.
        """
        item_key = f"{product.id}_{variant.id}" if variant else str(product.id)
        
        if variant:
            price = variant.price
            max_stock = variant.quantity
        else:
            price = product.price
            max_stock = product.quantity

        if item_key not in self.cart:
            self.cart[item_key] = {
                'product_id': product.id,
                'variant_id': variant.id if variant else None,
                'variant_name': variant.name if variant else '',
                'quantity': 0,
                'price': str(price)
            }

        if override_quantity:
            self.cart[item_key]['quantity'] = quantity
        else:
            self.cart[item_key]['quantity'] += quantity

        if self.cart[item_key]['quantity'] > max_stock:
            self.cart[item_key]['quantity'] = max_stock

        if self.cart[item_key]['quantity'] <= 0:
            self.remove_by_key(item_key)
        else:
            self.save()

    def decrease(self, item_key):
        """
        Decrease quantity by item key.
        """
        if item_key in self.cart:
            self.cart[item_key]['quantity'] -= 1
            if self.cart[item_key]['quantity'] <= 0:
                self.remove_by_key(item_key)
            else:
                self.save()

    def remove_by_key(self, item_key):
        """
        Remove item by key.
        """
        if item_key in self.cart:
            del self.cart[item_key]
            self.save()

    def remove(self, product):
        """
        Remove all instances of a product.
        """
        keys_to_remove = [k for k, v in self.cart.items() if str(v.get('product_id')) == str(product.id) or k == str(product.id)]
        for k in keys_to_remove:
            del self.cart[k]
        self.save()

    def save(self):
        """
        Save session modification.
        """
        self.session.modified = True

    def __iter__(self):
        """
        Iterate over items, fetching products and variants from database.
        """
        cart = self.cart.copy()
        product_ids = [item['product_id'] for item in cart.values() if 'product_id' in item]
        # Also check keys if legacy format
        for k in cart.keys():
            if '_' not in k and k.isdigit():
                product_ids.append(int(k))

        products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
        
        variant_ids = [item.get('variant_id') for item in cart.values() if item.get('variant_id')]
        variants = {v.id: v for v in ProductVariant.objects.filter(id__in=variant_ids)}

        for key, item in cart.items():
            pid = item.get('product_id') or (int(key) if key.isdigit() else None)
            if pid and pid in products:
                item_copy = item.copy()
                item_copy['item_key'] = key
                item_copy['product'] = products[pid]
                vid = item.get('variant_id')
                item_copy['variant'] = variants.get(vid) if vid else None
                item_copy['price'] = Decimal(item['price'])
                item_copy['total_price'] = item_copy['price'] * item['quantity']
                yield item_copy

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def get_subtotal(self):
        return self.get_total_price()

    def get_shipping_cost(self):
        return Decimal('100') if len(self) > 0 else Decimal('0')

    def get_grand_total(self):
        if len(self) == 0:
            return Decimal('0')
        return self.get_total_price() + self.get_shipping_cost()

    def clear(self):
        if self.SESSION_KEY in self.session:
            del self.session[self.SESSION_KEY]
        self.cart = {}
        self.save()


