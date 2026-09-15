from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

# Create your models here.


class TimeStampMixin(models.Model):
    """
    Abstract timestamp mixin shared across all domain models.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Address(TimeStampMixin):
    """
    Structured delivery and billing address.
    """
    country = models.CharField(max_length=255, default='Bangladesh')
    city = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    address_line = models.CharField(max_length=500)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.address_line}, {self.city}, {self.country}"


class Category(TimeStampMixin):
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-grid', help_text="Bootstrap icon class")

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            if self.parent:
                self.slug = slugify(f"{self.parent.slug}-{self.name}")
            else:
                self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    @property
    def is_parent(self):
        return self.parent is None


class SubCategory(Category):
    class Meta:
        proxy = True
        verbose_name = "Subcategory"
        verbose_name_plural = "Subcategories"


class Brand(TimeStampMixin):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "brand"
            slug = base_slug
            counter = 1
            while Brand.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(TimeStampMixin):
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    description = models.TextField(verbose_name="Specification")
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.8)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def default_variant(self):
        """
        Returns the default active variant for this product,
        or the first available variant, or the first variant.
        """
        if hasattr(self, '_prefetched_objects_cache') and 'variants' in self._prefetched_objects_cache:
            variants = self._prefetched_objects_cache['variants']
            for v in variants:
                if v.is_default and v.is_available:
                    return v
            for v in variants:
                if v.is_default:
                    return v
            for v in variants:
                if v.is_available:
                    return v
            return variants[0] if variants else None

        return (
            self.variants.filter(is_default=True, is_available=True).first()
            or self.variants.filter(is_default=True).first()
            or self.variants.filter(is_available=True).first()
            or self.variants.first()
        )

    @property
    def price(self):
        dv = self.default_variant
        return dv.price if dv else 0

    @property
    def regular_price(self):
        dv = self.default_variant
        return dv.regular_price if dv else None

    @property
    def quantity(self):
        dv = self.default_variant
        return dv.quantity if dv else 0

    @property
    def in_stock(self):
        dv = self.default_variant
        return (dv.quantity > 0 and dv.is_available) if dv else False

    @property
    def discount_amount(self):
        if self.regular_price and self.regular_price > self.price:
            return self.regular_price - self.price
        return 0

    @property
    def discount_percent(self):
        if self.regular_price and self.regular_price > self.price:
            pct = ((self.regular_price - self.price) / self.regular_price) * 100
            return int(round(pct))
        return 0

    @property
    def badge_info(self):
        """
        Returns dictionary for card badge:
        - Featured: For handpicked flagship products
        - New: For newly arrived products
        - Hot Deals: For products with active discounts
        """
        if hasattr(self, '_custom_badge'):
            return self._custom_badge
        if self.is_featured:
            return {
                'label': 'Featured',
                'icon': 'bi bi-star-fill text-warning',
                'css_class': 'featured',
            }
        elif self.discount_amount and self.discount_amount > 0:
            return {
                'label': 'Hot Deals',
                'icon': 'bi bi-lightning-fill text-warning',
                'css_class': 'hot-deal',
            }
        return None


class ProductVariant(TimeStampMixin):
    """
    Product variant representing specific combination (color, storage, region).
    Stores distinct selling price, regular price, stock quantity, availability, and default status.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=255, verbose_name="Variant Name")
    slug = models.SlugField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Discounted / Selling Price")
    regular_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Original / Regular Price without discount")
    quantity = models.PositiveIntegerField(default=10, help_text="Stock Quantity")
    is_available = models.BooleanField(default=True, verbose_name="Is Available")
    is_default = models.BooleanField(default=False, verbose_name="Is Default Variation")

    class Meta:
        ordering = ['-is_default', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.product.slug}-{self.name}") if self.product_id else slugify(self.name)
            slug = base_slug or "variant"
            counter = 1
            while ProductVariant.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        super().save(*args, **kwargs)

        # If marked as default, ensure all other variants of this product are not default
        if self.is_default and self.product_id:
            ProductVariant.objects.filter(product_id=self.product_id).exclude(pk=self.pk).update(is_default=False)

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def in_stock(self):
        return self.quantity > 0 and self.is_available

    @property
    def discount_amount(self):
        if self.regular_price and self.regular_price > self.price:
            return self.regular_price - self.price
        return 0

    @property
    def discount_percent(self):
        if self.regular_price and self.regular_price > self.price:
            pct = ((self.regular_price - self.price) / self.regular_price) * 100
            return int(round(pct))
        return 0


class ProductImage(TimeStampMixin):
    """
    Product gallery images.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    product_image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.product.name} Image"


class Customer(TimeStampMixin):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='customer_profile'
    )
    first_name = models.CharField(max_length=100, blank=True, default='')
    last_name = models.CharField(max_length=100, blank=True, default='')
    name = models.CharField(max_length=150, blank=True, default='')
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True, default='')
    email = models.EmailField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile/', blank=True, null=True)
    addresses = models.ManyToManyField(Address, blank=True, related_name='customers')

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.first_name or self.last_name:
            self.name = f"{self.first_name} {self.last_name}".strip()
        elif self.name and not self.first_name and not self.last_name:
            parts = self.name.split(' ', 1)
            self.first_name = parts[0]
            self.last_name = parts[1] if len(parts) > 1 else ''
        super().save(*args, **kwargs)

    def get_full_name(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.name

    def __str__(self):
        return f"{self.name or self.first_name} ({self.phone})"


class Order(TimeStampMixin):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=32, blank=True, db_index=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_method = models.CharField(max_length=50, default='Cash on Delivery')
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    delivery_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    class Meta:
        ordering = ['-order_date']

    def __str__(self):
        return f"Order #{self.order_number or self.id} - {self.product.name} ({self.customer.name})"


class Payment(TimeStampMixin):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    transaction_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50, default='Stripe')
    status = models.CharField(max_length=50, default='pending')
    raw_response = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Payment {self.transaction_id} for Order #{self.order.order_number}"


class Review(TimeStampMixin):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.customer.name} on {self.product.name}"


class FeaturedProduct(TimeStampMixin):
    """
    Curated products featured prominently on the homepage.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='featured_entries')
    order = models.PositiveIntegerField(default=0, help_text="Display order on homepage (lower numbers appear first)")

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Featured Product"
        verbose_name_plural = "Featured Products"

    def __str__(self):
        return f"Featured: {self.product.name}"


class NewProduct(TimeStampMixin):
    """
    Curated new arrivals and fresh products featured on the homepage.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='new_entries')
    order = models.PositiveIntegerField(default=0, help_text="Display order on homepage (lower numbers appear first)")

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "New Product"
        verbose_name_plural = "New Products"

    def __str__(self):
        return f"New Arrival: {self.product.name}"


class OfferProduct(TimeStampMixin):
    """
    Curated hot deals and special offer products featured on the homepage.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='offer_entries')
    order = models.PositiveIntegerField(default=0, help_text="Display order on homepage (lower numbers appear first)")

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Offer Product"
        verbose_name_plural = "Offer Products"

    def __str__(self):
        return f"Offer Deal: {self.product.name}"



